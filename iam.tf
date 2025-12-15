# IAM role for Lambda functions
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# CloudWatch Logs policy for Lambda
resource "aws_iam_role_policy" "lambda_logging" {
  name = "lambda-logging"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-*:*"
      }
    ]
  })
}

# S3 read policy for Lambda
resource "aws_iam_role_policy" "lambda_s3" {
  name = "lambda-s3-access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.config.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.config.arn
      }
    ]
  })
}

# SNS publish policy for error handler Lambda
resource "aws_iam_role_policy" "lambda_sns" {
  name = "lambda-sns-publish"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.errors.arn
      }
    ]
  })
}

# Secrets Manager read policy for Lambda
resource "aws_iam_role_policy" "lambda_secrets" {
  name = "lambda-secrets-access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = concat(
          [aws_secretsmanager_secret.tfc_token.arn],
          var.ca_bundle_secret_name != "" ? ["arn:aws:secretsmanager:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:secret:${var.ca_bundle_secret_name}*"] : []
        )
      }
    ]
  })
}

# VPC ENI management policy for Lambda (required when Lambda is in VPC)
resource "aws_iam_role_policy" "lambda_vpc" {
  count = var.vpc_subnet_ids != null ? 1 : 0
  name  = "lambda-vpc-access"
  role  = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses"
        ]
        Resource = "*"
      }
    ]
  })
}

# KMS policy for Lambda (required when using customer-managed KMS keys)
resource "aws_iam_role_policy" "lambda_kms" {
  count = var.kms_key_arn != null ? 1 : 0
  name  = "lambda-kms-access"
  role  = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = var.kms_key_arn
      }
    ]
  })
}

# KMS grant for Lambda to access encrypted resources
resource "aws_kms_grant" "lambda" {
  count             = var.kms_key_arn != null ? 1 : 0
  name              = "${var.project_name}-lambda-grant"
  key_id            = var.kms_key_arn
  grantee_principal = aws_iam_role.lambda.arn

  operations = [
    "Decrypt",
    "GenerateDataKey",
    "DescribeKey"
  ]
}

# IAM role for Step Functions
resource "aws_iam_role" "stepfunctions" {
  name = "${var.project_name}-stepfunctions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

# Step Functions Lambda invocation policy
resource "aws_iam_role_policy" "stepfunctions_lambda" {
  name = "stepfunctions-lambda-invoke"
  role = aws_iam_role.stepfunctions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.read_config.arn,
          aws_lambda_function.check_version.arn,
          aws_lambda_function.download_to_s3.arn,
          aws_lambda_function.upload_from_s3.arn,
          aws_lambda_function.error_handler.arn
        ]
      }
    ]
  })
}

# Step Functions CloudWatch Logs policy
resource "aws_iam_role_policy" "stepfunctions_logs" {
  name = "stepfunctions-logs"
  role = aws_iam_role.stepfunctions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ]
  })
}
