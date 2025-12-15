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

data "archive_file" "download_to_s3" {
  type        = "zip"
  source_file = "${path.module}/lambda/download_to_s3.py"
  output_path = "${path.module}/builds/download_to_s3.zip"
}

data "archive_file" "upload_from_s3" {
  type        = "zip"
  source_file = "${path.module}/lambda/upload_from_s3.py"
  output_path = "${path.module}/builds/upload_from_s3.zip"
}

resource "terraform_data" "lambda_builds_directory" {
  count = var.allow_local_exec_commands ? 1 : 0
  provisioner "local-exec" {
    command = "pip3 install requests -t ${path.module}/lambda/layer/python/"
  }

}


# Package Lambda Layer
data "archive_file" "lambda_layer" {
  count = var.allow_local_exec_commands ? 1 : 0
  type        = "zip"
  source_dir  = "${path.module}/lambda/layer"
  output_path = "${path.module}/builds/lambda_layer.zip"
  depends_on  = [terraform_data.lambda_builds_directory[0]]
}

# Lambda Layer with requests library
resource "aws_lambda_layer_version" "requests" {
  count = var.allow_local_exec_commands ? 1 : 0
  filename            = data.archive_file.lambda_layer[0].output_path
  layer_name          = "${var.project_name}-requests-layer"
  source_code_hash    = data.archive_file.lambda_layer[0].output_base64sha256
  compatible_runtimes = [var.lambda_runtime]
  description         = "Python requests library for provider sync Lambda functions"

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

resource "aws_cloudwatch_log_group" "error_handler" {
  name              = "/aws/lambda/${var.project_name}-error-handler"
  retention_in_days = var.cloudwatch_logs_retention_days
}

resource "aws_cloudwatch_log_group" "cleanup_old_versions" {
  name              = "/aws/lambda/${var.project_name}-cleanup-old-versions"
  retention_in_days = var.cloudwatch_logs_retention_days
}

resource "terraform_data" "ensure_lambda_layer_stability" {
  lifecycle {
    precondition {
      condition     = var.allow_local_exec_commands == true || var.lambda_layer_arn != null
      error_message = "When 'allow_local_exec_commands' is false, 'lambda_layer_arn' must be provided to ensure Lambda layer stability."
    }
  }
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
  layers           = [var.allow_local_exec_commands ? aws_lambda_layer_version.requests[0].arn : var.lambda_layer_arn]

  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.read_config
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
  layers           = [var.allow_local_exec_commands ? aws_lambda_layer_version.requests[0].arn : var.lambda_layer_arn]

  dynamic "vpc_config" {
    for_each = var.vpc_subnet_ids != null ? [1] : []
    content {
      subnet_ids         = var.vpc_subnet_ids
      security_group_ids = var.vpc_security_group_ids
    }
  }

  environment {
    variables = {
      TFC_TOKEN_SECRET_NAME  = aws_secretsmanager_secret.tfc_token.name
      TFC_ORGANIZATION       = var.tfc_organization
      TFC_ADDRESS            = var.tfc_address
      CA_BUNDLE_SECRET_NAME  = var.ca_bundle_secret_name
      LOG_LEVEL              = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.check_version,
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
  layers           = [var.allow_local_exec_commands ? aws_lambda_layer_version.requests[0].arn : var.lambda_layer_arn]

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.errors.arn
      LOG_LEVEL     = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.error_handler,
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
  layers           = [var.allow_local_exec_commands ? aws_lambda_layer_version.requests[0].arn : var.lambda_layer_arn]

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
  ]
}

# Lambda function: Download to S3 (NOT in VPC - needs public internet access)
resource "aws_cloudwatch_log_group" "download_to_s3" {
  name              = "/aws/lambda/${var.project_name}-download-to-s3"
  retention_in_days = var.cloudwatch_logs_retention_days
}

resource "aws_lambda_function" "download_to_s3" {
  filename         = data.archive_file.download_to_s3.output_path
  function_name    = "${var.project_name}-download-to-s3"
  role             = aws_iam_role.lambda.arn
  handler          = "download_to_s3.lambda_handler"
  source_code_hash = data.archive_file.download_to_s3.output_base64sha256
  runtime          = var.lambda_runtime
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size
  layers           = [var.allow_local_exec_commands ? aws_lambda_layer_version.requests[0].arn : var.lambda_layer_arn]

  ephemeral_storage {
    size = var.lambda_ephemeral_storage
  }

  # NO VPC CONFIG - needs public internet access

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.config.id
      LOG_LEVEL      = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.download_to_s3,
  ]
}

# Lambda function: Upload from S3 (IN VPC - accesses S3 via VPC endpoint)
resource "aws_cloudwatch_log_group" "upload_from_s3" {
  name              = "/aws/lambda/${var.project_name}-upload-from-s3"
  retention_in_days = var.cloudwatch_logs_retention_days
}

resource "aws_lambda_function" "upload_from_s3" {
  filename         = data.archive_file.upload_from_s3.output_path
  function_name    = "${var.project_name}-upload-from-s3"
  role             = aws_iam_role.lambda.arn
  handler          = "upload_from_s3.lambda_handler"
  source_code_hash = data.archive_file.upload_from_s3.output_base64sha256
  runtime          = var.lambda_runtime
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size
  layers           = [var.allow_local_exec_commands ? aws_lambda_layer_version.requests[0].arn : var.lambda_layer_arn]

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
      TFC_TOKEN_SECRET_NAME  = aws_secretsmanager_secret.tfc_token.name
      TFC_ORGANIZATION       = var.tfc_organization
      TFC_ADDRESS            = var.tfc_address
      CA_BUNDLE_SECRET_NAME  = var.ca_bundle_secret_name
      LOG_LEVEL              = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.upload_from_s3,
  ]
}
