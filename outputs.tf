output "state_machine_arn" {
  description = "ARN of the Step Functions state machine"
  value       = aws_sfn_state_machine.provider_sync.arn
}

output "state_machine_name" {
  description = "Name of the Step Functions state machine"
  value       = aws_sfn_state_machine.provider_sync.name
}

output "config_bucket_name" {
  description = "Name of the S3 bucket for provider configurations"
  value       = aws_s3_bucket.config.id
}

output "config_bucket_arn" {
  description = "ARN of the S3 bucket for provider configurations"
  value       = aws_s3_bucket.config.arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for error notifications"
  value       = aws_sns_topic.errors.arn
}

output "tfc_token_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the TFC token"
  value       = aws_secretsmanager_secret.tfc_token.arn
}

output "tfc_token_secret_name" {
  description = "Name of the Secrets Manager secret containing the TFC token"
  value       = aws_secretsmanager_secret.tfc_token.name
}

output "lambda_function_arns" {
  description = "ARNs of all Lambda functions"
  value = {
    read_config          = aws_lambda_function.read_config.arn
    check_version        = aws_lambda_function.check_version.arn
    error_handler        = aws_lambda_function.error_handler.arn
    cleanup_old_versions = aws_lambda_function.cleanup_old_versions.arn
  }
}

output "execution_command" {
  description = "Example AWS CLI command to execute the state machine with array config"
  value       = <<-EOT
    # Execute with array config (processes multiple providers in parallel)
    # Modify config.json as needed and upload to the S3 bucket before running this command
    # Terraform will invoke an action to start the execution
    terraform apply
  EOT
}


output "example_config_format" {
  description = "Example config.json format for multiple providers"
  value       = <<-EOT
    [
      {
        "provider": "aws",
        "namespace": "hashicorp",
        "gpg-key-id": "34365D9472D7468F",
        "version": "latest",
        "platforms": [
          {"os": "linux", "arch": "amd64"},
          {"os": "darwin", "arch": "arm64"}
        ]
      },
      {
        "provider": "github",
        "namespace": "integrations",
        "gpg-key-id": "38027F80D7FD5FB2",
        "version": "latest",
        "platforms": [{"os": "darwin", "arch": "arm64"}]
      }
    ]
  EOT
}


output "cloudwatch_log_groups" {
  description = "CloudWatch Log Group names for debugging"
  value = {
    stepfunctions        = aws_cloudwatch_log_group.stepfunctions.name
    read_config          = aws_cloudwatch_log_group.read_config.name
    check_version        = aws_cloudwatch_log_group.check_version.name
    error_handler        = aws_cloudwatch_log_group.error_handler.name
    cleanup_old_versions = aws_cloudwatch_log_group.cleanup_old_versions.name
  }
}
