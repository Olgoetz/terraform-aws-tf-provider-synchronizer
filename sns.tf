# SNS topic for error notifications
resource "aws_sns_topic" "errors" {
  name              = "${var.project_name}-errors"
  display_name      = var.sns_topic_display_name
  kms_master_key_id = var.kms_key_arn

  tags = merge(
    var.tags,
    {
      Name = "Provider Sync Error Notifications"
    }
  )
}

# SNS topic subscription
resource "aws_sns_topic_subscription" "email" {
  for_each = toset(var.notification_emails)
  topic_arn = aws_sns_topic.errors.arn
  protocol  = "email"
  endpoint  = each.value
}

# SNS topic policy
resource "aws_sns_topic_policy" "errors" {
  arn = aws_sns_topic.errors.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowLambdaPublish"
        Effect = "Allow"
        Principal = {
          Service = ["lambda.amazonaws.com", "events.amazonaws.com"]
        }
        Action   = "SNS:Publish"
        Resource = aws_sns_topic.errors.arn
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Sid    = "AllowCloudWatchEvents"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action   = "SNS:Publish"
        Resource = aws_sns_topic.errors.arn
      }
    ]
  })
}
