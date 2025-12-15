variable "allow_local_exec_commands" {
  description = "Allow the execution of local-exec provisioner"
  type        = bool
  default     = false
}

variable "config_json" {
  description = "Provider configuration JSON content to be uploaded to S3"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "terraform-provider-sync"
}

variable "tfc_token" {
  description = "HCP Terraform or Terraform Enterprise API token"
  type        = string
  sensitive   = true
}

variable "tfc_organization" {
  description = "HCP Terraform or Terraform Enterprise organization name"
  type        = string
}

variable "tfc_address" {
  description = "HCP Terraform or Terraform Enterprise address"
  type        = string
  default     = "https://app.terraform.io"
}

variable "notification_emails" {
  description = "Email address for error notifications"
  type        = list(string)
}

variable "sns_topic_display_name" {
  description = "Display name for the SNS topic (used in email notifications)"
  type        = string
  default     = null
}

variable "schedule_cron_expression" {
  description = "Cron expression for scheduled Step Functions execution (e.g., 'cron(0 2 * * ? *)' for daily at 2 AM UTC). Set to null to disable scheduled execution."
  type        = string
  default     = null
}

variable "cleanup_cron_expression" {
  description = "Cron expression for scheduled cleanup of old provider versions (e.g., 'cron(0 3 ? * SUN *)' for weekly on Sundays at 3 AM UTC). Set to null to disable scheduled cleanup."
  type        = string
  default     = null
}

variable "cleanup_keep_version_count" {
  description = "Number of provider versions to keep during cleanup (older versions will be deleted)"
  type        = number
  default     = 10
}

variable "cleanup_dry_run" {
  description = "Run cleanup in dry-run mode (log what would be deleted without actually deleting)"
  type        = bool
  default     = false
}

variable "config_bucket_name" {
  description = "S3 bucket name for provider configurations (if null, one will be created)"
  type        = string
  default     = null
}

variable "lambda_runtime" {
  description = "Lambda runtime version"
  type        = string
  default     = "python3.12"
}

variable "lambda_layer_arn" {
  description = "ARN of the Lambda layer to use"
  type        = string
  default     = null
}

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

variable "cloudwatch_logs_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 30
}

variable "kms_key_arn" {
  description = "ARN of customer-managed KMS key for encryption (S3, Secrets Manager, SNS). If not provided, AWS managed keys will be used."
  type        = string
  default     = null
}

variable "vpc_subnet_ids" {
  description = "List of VPC subnet IDs for Lambda functions (check_version and download_and_upload). If provided, Lambda functions will be deployed in VPC."
  type        = list(string)
  default     = null
}

variable "vpc_security_group_ids" {
  description = "List of VPC security group IDs for Lambda functions (check_version and download_and_upload). Required if vpc_subnet_ids is provided."
  type        = list(string)
  default     = null
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
variable "proxy" {
  description = "HTTP proxy URL for Lambda functions"
  type        = string
  default     = ""
}

variable "ca_bundle_secret_name" {
  description = "AWS Secrets Manager secret name containing the CA bundle for TLS verification. If not provided, default system CA bundle will be used."
  type        = string
  default     = ""
}
