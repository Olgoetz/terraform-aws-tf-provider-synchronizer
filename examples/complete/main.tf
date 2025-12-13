terraform {
  required_version = ">= 1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Recommended: Use remote backend for production
  # backend "s3" {
  #   bucket         = "my-terraform-state"
  #   key            = "provider-sync/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Terraform Provider Sync"
      ManagedBy   = "Terraform"
      Environment = var.environment
      CostCenter  = var.cost_center
    }
  }
}

# Optional: Create KMS key if not provided
resource "aws_kms_key" "provider_sync" {
  count = var.create_kms_key ? 1 : 0

  description             = "KMS key for Terraform Provider Sync encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-encryption-key"
  }
}

resource "aws_kms_alias" "provider_sync" {
  count = var.create_kms_key ? 1 : 0

  name          = "alias/${var.project_name}"
  target_key_id = aws_kms_key.provider_sync[0].key_id
}

# Complete module configuration with all features enabled
module "provider_sync" {
  source = "../../"

  # Basic Configuration
  project_name              = var.project_name
  aws_region                = var.aws_region
  tfc_organization          = var.tfc_organization
  tfc_token                 = var.tfc_token
  tfc_address               = var.tfc_address
  notification_email        = var.notification_email
  allow_local_exec_commands = var.allow_local_exec_commands

  # VPC Configuration
  vpc_subnet_ids         = var.vpc_subnet_ids
  vpc_security_group_ids = var.vpc_security_group_ids

  # Encryption
  kms_key_arn = var.create_kms_key ? aws_kms_key.provider_sync[0].arn : var.kms_key_arn

  # Lambda Configuration
  lambda_timeout           = var.lambda_timeout
  lambda_memory_size       = var.lambda_memory_size
  lambda_ephemeral_storage = var.lambda_ephemeral_storage

  # Logging
  cloudwatch_logs_retention_days = var.cloudwatch_logs_retention_days

  # Scheduling
  schedule_cron_expression = var.schedule_cron_expression
  cleanup_cron_expression  = var.cleanup_cron_expression

  # Cleanup Configuration
  cleanup_keep_version_count = var.cleanup_keep_version_count
  cleanup_dry_run            = var.cleanup_dry_run

  # SNS Configuration
  sns_topic_display_name = var.sns_topic_display_name

  # Resource Tagging
  tags = {
    Example     = "complete"
    Environment = var.environment
    CostCenter  = var.cost_center
  }
}
