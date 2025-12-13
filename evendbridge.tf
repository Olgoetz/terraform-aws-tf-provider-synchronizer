# EventBridge Rule for Step Functions scheduled execution
resource "aws_cloudwatch_event_rule" "stepfunctions_schedule" {
  count               = var.schedule_cron_expression != null ? 1 : 0
  name                = "${var.project_name}-schedule"
  description         = "Scheduled execution of provider synchronization Step Functions"
  schedule_expression = var.schedule_cron_expression

  tags = merge(
    var.tags,
    {
      Name = "Provider Sync Schedule"
    }
  )
}

# EventBridge Target for Step Functions scheduled execution
resource "aws_cloudwatch_event_target" "stepfunctions_schedule" {
  count     = var.schedule_cron_expression != null ? 1 : 0
  rule      = aws_cloudwatch_event_rule.stepfunctions_schedule[0].name
  target_id = "StepFunctionsScheduledExecution"
  arn       = aws_sfn_state_machine.provider_sync.arn
  role_arn  = aws_iam_role.eventbridge_stepfunctions.arn

  input = jsonencode({
    bucket = aws_s3_bucket.config.id
    key    = "config.json"
  })
}



# EventBridge Rule for cleanup scheduled execution
resource "aws_cloudwatch_event_rule" "cleanup_schedule" {
  count               = var.cleanup_cron_expression != null ? 1 : 0
  name                = "${var.project_name}-cleanup-schedule"
  description         = "Scheduled cleanup of old provider versions"
  schedule_expression = var.cleanup_cron_expression

  tags = merge(
    var.tags,
    {
      Name = "Provider Cleanup Schedule"
    }
  )
}

# EventBridge Target for cleanup Lambda
resource "aws_cloudwatch_event_target" "cleanup" {
  count     = var.cleanup_cron_expression != null ? 1 : 0
  rule      = aws_cloudwatch_event_rule.cleanup_schedule[0].name
  target_id = "CleanupLambdaExecution"
  arn       = aws_lambda_function.cleanup_old_versions.arn
}

# Lambda permission for EventBridge to invoke cleanup
resource "aws_lambda_permission" "allow_eventbridge_cleanup" {
  count         = var.cleanup_cron_expression != null ? 1 : 0
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cleanup_old_versions.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cleanup_schedule[0].arn
}

# IAM Role for EventBridge to invoke Step Functions
resource "aws_iam_role" "eventbridge_stepfunctions" {
  name = "${var.project_name}-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name = "EventBridge Step Functions Role"
    }
  )
}

# IAM Policy for EventBridge to invoke Step Functions
resource "aws_iam_role_policy" "eventbridge_stepfunctions" {
  name = "eventbridge-stepfunctions-invoke"
  role = aws_iam_role.eventbridge_stepfunctions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = aws_sfn_state_machine.provider_sync.arn
      }
    ]
  })
}
