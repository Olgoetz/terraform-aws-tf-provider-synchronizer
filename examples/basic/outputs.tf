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
