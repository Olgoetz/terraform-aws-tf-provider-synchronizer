output "state_machine_arn" {
  description = "ARN of the Step Functions state machine"
  value       = module.provider_sync.state_machine_arn
}

output "state_machine_name" {
  description = "Name of the Step Functions state machine"
  value       = module.provider_sync.state_machine_name
}

output "config_bucket_name" {
  description = "Name of the S3 bucket for provider configurations"
  value       = module.provider_sync.config_bucket_name
}

output "config_bucket_arn" {
  description = "ARN of the S3 bucket for provider configurations"
  value       = module.provider_sync.config_bucket_arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for error notifications"
  value       = module.provider_sync.sns_topic_arn
}

output "lambda_function_arns" {
  description = "ARNs of all Lambda functions"
  value       = module.provider_sync.lambda_function_arns
}

output "execution_command" {
  description = "Example AWS CLI command to execute the state machine"
  value       = module.provider_sync.execution_command
}

output "cloudwatch_log_groups" {
  description = "CloudWatch Log Group names for debugging"
  value       = module.provider_sync.cloudwatch_log_groups
}

output "kms_key_arn" {
  description = "ARN of the KMS key used for encryption"
  value       = var.create_kms_key ? aws_kms_key.provider_sync[0].arn : var.kms_key_arn
}

output "kms_key_id" {
  description = "ID of the KMS key used for encryption"
  value       = var.create_kms_key ? aws_kms_key.provider_sync[0].key_id : null
}

output "tfc_token_secret_name" {
  description = "Name of the Secrets Manager secret containing the TFC token"
  value       = module.provider_sync.tfc_token_secret_name
}

output "tfc_token_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the TFC token"
  value       = module.provider_sync.tfc_token_secret_arn
}
