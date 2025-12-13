# Package Lambda functions
data "archive_file" "read_config" {
  type        = "zip"
  source_file = "${path.module}/lambda/read_config.py"
  output_path = "${path.module}/builds/read_config.zip"
}

data "archive_file" "check_version" {
  type        = "zip"
  source_file = "${path.module}/lambda/check_version.py"
  output_path = "${path.module}/builds/check_version.zip"
}

data "archive_file" "download_and_upload" {
  type        = "zip"
  source_file = "${path.module}/lambda/download_and_upload.py"
  output_path = "${path.module}/builds/download_and_upload.zip"
}

data "archive_file" "error_handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/error_handler.py"
  output_path = "${path.module}/builds/error_handler.zip"
}

data "archive_file" "cleanup_old_versions" {
  type        = "zip"
  source_file = "${path.module}/lambda/cleanup_old_versions.py"
  output_path = "${path.module}/builds/cleanup_old_versions.zip"
}

resource "terraform_data" "lambda_builds_directory" {
  count = var.allow_local_exec_commands ? 1 : 0
  provisioner "local-exec" {
    command = "pip3 install requests -t ${path.module}/lambda/layer/python/"
  }

}


# Package Lambda Layer
data "archive_file" "lambda_layer" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/layer"
  output_path = "${path.module}/builds/lambda_layer.zip"
  depends_on  = [terraform_data.lambda_builds_directory[0]]
}

# Lambda Layer with requests library
resource "aws_lambda_layer_version" "requests" {
  filename            = data.archive_file.lambda_layer.output_path
  layer_name          = "${var.project_name}-requests-layer"
  source_code_hash    = data.archive_file.lambda_layer.output_base64sha256
  compatible_runtimes = [var.lambda_runtime]
  description         = "Python requests library for provider sync Lambda functions"

  depends_on = [data.archive_file.lambda_layer]
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "read_config" {
  name              = "/aws/lambda/${var.project_name}-read-config"
  retention_in_days = var.cloudwatch_logs_retention_days
}

resource "aws_cloudwatch_log_group" "check_version" {
  name              = "/aws/lambda/${var.project_name}-check-version"
  retention_in_days = var.cloudwatch_logs_retention_days
}

resource "aws_cloudwatch_log_group" "download_and_upload" {
  name              = "/aws/lambda/${var.project_name}-download-upload"
  retention_in_days = var.cloudwatch_logs_retention_days
}

resource "aws_cloudwatch_log_group" "error_handler" {
  name              = "/aws/lambda/${var.project_name}-error-handler"
  retention_in_days = var.cloudwatch_logs_retention_days
}

resource "aws_cloudwatch_log_group" "cleanup_old_versions" {
  name              = "/aws/lambda/${var.project_name}-cleanup-old-versions"
  retention_in_days = var.cloudwatch_logs_retention_days
}

# Lambda function: Read Config
resource "aws_lambda_function" "read_config" {
  filename         = data.archive_file.read_config.output_path
  function_name    = "${var.project_name}-read-config"
  role             = aws_iam_role.lambda.arn
  handler          = "read_config.lambda_handler"
  source_code_hash = data.archive_file.read_config.output_base64sha256
  runtime          = var.lambda_runtime
  timeout          = 60
  memory_size      = 256
  layers           = [aws_lambda_layer_version.requests.arn]

  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.read_config,
    aws_iam_role_policy.lambda_logging,
    aws_iam_role_policy.lambda_s3
  ]
}

# Lambda function: Check Version
resource "aws_lambda_function" "check_version" {
  filename         = data.archive_file.check_version.output_path
  function_name    = "${var.project_name}-check-version"
  role             = aws_iam_role.lambda.arn
  handler          = "check_version.lambda_handler"
  source_code_hash = data.archive_file.check_version.output_base64sha256
  runtime          = var.lambda_runtime
  timeout          = 120
  memory_size      = 256
  layers           = [aws_lambda_layer_version.requests.arn]

  dynamic "vpc_config" {
    for_each = var.vpc_subnet_ids != null ? [1] : []
    content {
      subnet_ids         = var.vpc_subnet_ids
      security_group_ids = var.vpc_security_group_ids
    }
  }

  environment {
    variables = {
      TFC_TOKEN_SECRET_NAME = aws_secretsmanager_secret.tfc_token.name
      TFC_ORGANIZATION      = var.tfc_organization
      TFC_ADDRESS           = var.tfc_address
      LOG_LEVEL             = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.check_version,
    aws_iam_role_policy.lambda_logging,
    aws_iam_role_policy.lambda_secrets,
    aws_iam_role_policy.lambda_vpc
  ]
}

# Lambda function: Download and Upload
resource "aws_lambda_function" "download_and_upload" {
  filename         = data.archive_file.download_and_upload.output_path
  function_name    = "${var.project_name}-download-upload"
  role             = aws_iam_role.lambda.arn
  handler          = "download_and_upload.lambda_handler"
  source_code_hash = data.archive_file.download_and_upload.output_base64sha256
  runtime          = var.lambda_runtime
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size
  layers           = [aws_lambda_layer_version.requests.arn]

  ephemeral_storage {
    size = var.lambda_ephemeral_storage
  }

  dynamic "vpc_config" {
    for_each = var.vpc_subnet_ids != null ? [1] : []
    content {
      subnet_ids         = var.vpc_subnet_ids
      security_group_ids = var.vpc_security_group_ids
    }
  }

  environment {
    variables = {
      TFC_TOKEN_SECRET_NAME = aws_secretsmanager_secret.tfc_token.name
      TFC_ORGANIZATION      = var.tfc_organization
      TFC_ADDRESS           = var.tfc_address
      LOG_LEVEL             = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.download_and_upload,
    aws_iam_role_policy.lambda_logging,
    aws_iam_role_policy.lambda_secrets,
    aws_iam_role_policy.lambda_vpc
  ]
}

# Lambda function: Error Handler
resource "aws_lambda_function" "error_handler" {
  filename         = data.archive_file.error_handler.output_path
  function_name    = "${var.project_name}-error-handler"
  role             = aws_iam_role.lambda.arn
  handler          = "error_handler.lambda_handler"
  source_code_hash = data.archive_file.error_handler.output_base64sha256
  runtime          = var.lambda_runtime
  timeout          = 60
  memory_size      = 256
  layers           = [aws_lambda_layer_version.requests.arn]

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.errors.arn
      LOG_LEVEL     = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.error_handler,
    aws_iam_role_policy.lambda_logging,
    aws_iam_role_policy.lambda_sns
  ]
}

# Lambda function: Cleanup Old Versions
resource "aws_lambda_function" "cleanup_old_versions" {
  filename         = data.archive_file.cleanup_old_versions.output_path
  function_name    = "${var.project_name}-cleanup-old-versions"
  role             = aws_iam_role.lambda.arn
  handler          = "cleanup_old_versions.lambda_handler"
  source_code_hash = data.archive_file.cleanup_old_versions.output_base64sha256
  runtime          = var.lambda_runtime
  timeout          = 900
  memory_size      = 512
  layers           = [aws_lambda_layer_version.requests.arn]

  dynamic "vpc_config" {
    for_each = var.vpc_subnet_ids != null ? [1] : []
    content {
      subnet_ids         = var.vpc_subnet_ids
      security_group_ids = var.vpc_security_group_ids
    }
  }

  environment {
    variables = {
      TFC_TOKEN_SECRET_NAME = aws_secretsmanager_secret.tfc_token.name
      TFC_ORGANIZATION      = var.tfc_organization
      TFC_ADDRESS           = var.tfc_address
      KEEP_VERSION_COUNT    = var.cleanup_keep_version_count
      DRY_RUN               = var.cleanup_dry_run ? "true" : "false"
      LOG_LEVEL             = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.cleanup_old_versions,
    aws_iam_role_policy.lambda_logging,
    aws_iam_role_policy.lambda_secrets
  ]
}
