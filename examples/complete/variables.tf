variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "allow_local_exec_commands" {
  description = "Allow the execution of local-exec provisioner"
  type        = bool
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "engineering"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "terraform-provider-sync"
}

variable "tfc_organization" {
  description = "HCP Terraform or Terraform Enterprise organization name"
  type        = string
}

variable "tfc_token" {
  description = "HCP Terraform or Terraform Enterprise API token"
  type        = string
  sensitive   = true
}

variable "tfc_address" {
  description = "HCP Terraform or Terraform Enterprise address"
  type        = string
  default     = "https://app.terraform.io"
}

variable "notification_email" {
  description = "Email address for error notifications"
  type        = string
}

variable "sns_topic_display_name" {
  description = "Display name for the SNS topic"
  type        = string
  default     = "Terraform Provider Sync Notifications"
}

# VPC Configuration
variable "vpc_subnet_ids" {
  description = "List of VPC subnet IDs for Lambda functions"
  type        = list(string)
}

variable "vpc_security_group_ids" {
  description = "List of VPC security group IDs for Lambda functions"
  type        = list(string)
}

# KMS Configuration
variable "create_kms_key" {
  description = "Whether to create a new KMS key"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "ARN of existing KMS key (if create_kms_key is false)"
  type        = string
  default     = null
}

# Lambda Configuration
variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 900
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 3008
}

variable "lambda_ephemeral_storage" {
  description = "Lambda ephemeral storage in MB"
  type        = number
  default     = 10240
}

# Logging
variable "cloudwatch_logs_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 90
}

# Scheduling
variable "schedule_cron_expression" {
  description = "Cron expression for scheduled sync execution"
  type        = string
  default     = "cron(0 2 * * ? *)" # Daily at 2 AM UTC
}

variable "cleanup_cron_expression" {
  description = "Cron expression for scheduled cleanup execution"
  type        = string
  default     = "cron(0 3 ? * SUN *)" # Weekly on Sundays at 3 AM UTC
}

# Cleanup Configuration
variable "cleanup_keep_version_count" {
  description = "Number of provider versions to keep during cleanup"
  type        = number
  default     = 10
}

variable "cleanup_dry_run" {
  description = "Run cleanup in dry-run mode"
  type        = bool
  default     = false
}
