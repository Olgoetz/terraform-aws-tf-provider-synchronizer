# CloudWatch Log Group for Step Functions
resource "aws_cloudwatch_log_group" "stepfunctions" {
  name              = "/aws/stepfunctions/${var.project_name}"
  retention_in_days = var.cloudwatch_logs_retention_days
}

# Step Functions State Machine
resource "aws_sfn_state_machine" "provider_sync" {
  name     = "${var.project_name}-state-machine"
  role_arn = aws_iam_role.stepfunctions.arn

  definition = templatefile("${path.module}/stepfunctions/state_machine.json", {
    ReadConfigFunctionArn    = aws_lambda_function.read_config.arn
    CheckVersionFunctionArn  = aws_lambda_function.check_version.arn
    DownloadToS3FunctionArn  = aws_lambda_function.download_to_s3.arn
    UploadFromS3FunctionArn  = aws_lambda_function.upload_from_s3.arn
    ErrorHandlerFunctionArn  = aws_lambda_function.error_handler.arn
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.stepfunctions.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tracing_configuration {
    enabled = true
  }

  depends_on = [
    aws_iam_role_policy.stepfunctions_lambda,
    aws_iam_role_policy.stepfunctions_logs
  ]
}
