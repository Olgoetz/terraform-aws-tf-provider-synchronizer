# Terraform Infrastructure for Provider Synchronization

[![Terraform](https://img.shields.io/badge/Terraform-%3E%3D1.14.0-623CE4?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![AWS Provider](https://img.shields.io/badge/AWS%20Provider-~%3E6.0-FF9900?logo=amazon-aws&logoColor=white)](https://registry.terraform.io/providers/hashicorp/aws/latest)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![AWS Lambda](https://img.shields.io/badge/AWS%20Lambda-Serverless-FF9900?logo=aws-lambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![Step Functions](https://img.shields.io/badge/AWS%20Step%20Functions-Orchestration-C925D1?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/step-functions/)

This directory contains Terraform configuration to deploy the complete AWS infrastructure for the Terraform Provider Synchronization workflow.

## Architecture

The infrastructure deploys:

- **5 Lambda Functions** (Read Config, Check Version, Download/Upload, Error Handler, Clean Up)
- **Step Functions State Machine** (orchestrates the workflow)
- **S3 Bucket** (stores provider configuration files)
- **SNS Topic** (sends error notifications via email)
- **IAM Roles & Policies** (least privilege access)
- **CloudWatch Log Groups** (centralized logging)
- **EventBridge CrongJob** (scheduled execution)

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.14.0
- HCP Terraform or Terraform Enterprise account and API token
- AWS CLI configured with credentials

## Quick Start

### 1. Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
export TF_VAR_tfc_token="your-token"
```

Edit `terraform.tfvars` with your values:

```hcl
aws_region         = "us-east-1"
tfc_organization   = "your-org"
notification_email = "your-email@example.com"
```

**For Terraform Enterprise:**

```hcl
tfc_address = "https://tfe.example.com"
```

### 2. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Deploy
terraform apply
```

### 3. Confirm SNS Subscription

After deployment, check your email and confirm the SNS subscription to receive error notifications.

### 4. Upload Provider Configuration

> **Important**: The gpg key must exist on HCP/TFE, otherwise the upload procedure fails! You can use `./scripts/manage_gpg_keys.py` to manage a gpg key.

Create a provider config file:

```json
[
  {
    "provider": "github",
    "namespace": "integrations",
    "gpg-key-id": "38027F80D7FD5FB2", // already available in the targeted organization
    "version": "latest", // always tries to pull the latest version when executed
    "platforms": [{ "os": "darwin", "arch": "arm64" }]
  },
  {
    "provider": "aws",
    "namespace": "hashicorp",
    "gpg-key-id": "34365D9472D7468F",
    "version": "6.25.0", // should only be set to a specific version when manually executing
    "platforms": [{ "os": "darwin", "arch": "arm64" }]
  }
]
```

### 5. Execute Workflow

Change the `config.json` and run:

```bash
terraform apply
```

## Configuration Reference

## Outputs

After deployment, Terraform provides useful outputs:

```bash
# Get state machine ARN
terraform output state_machine_arn

# Get S3 bucket name
terraform output config_bucket_name

# Get execution command template
terraform output -raw execution_command

# View all Lambda function ARNs
terraform output lambda_function_arns

# View CloudWatch log groups
terraform output cloudwatch_log_groups
```

## Cost Estimation

Typical monthly costs (assuming moderate usage):

- **Lambda**: ~$5-20/month (depends on executions)
- **Step Functions**: ~$0.25 per 1000 executions
- **S3**: ~$0.023 per GB stored
- **SNS**: First 1000 emails free, then $2 per 100,000
- **CloudWatch Logs**: ~$0.50 per GB ingested

**Estimated total**: $10-30/month for light to moderate usage.

## Monitoring

### CloudWatch Logs

View logs for each component:

```bash
# State machine executions
aws logs tail /aws/stepfunctions/terraform-provider-sync --follow

# Lambda functions
aws logs tail /aws/lambda/terraform-provider-sync-read-config --follow
aws logs tail /aws/lambda/terraform-provider-sync-check-version --follow
aws logs tail /aws/lambda/terraform-provider-sync-download-upload --follow
aws logs tail /aws/lambda/terraform-provider-sync-error-handler --follow
```

### Step Functions Console

1. Open AWS Console → Step Functions
2. Click on `terraform-provider-sync-state-machine`
3. View execution history and detailed logs

### Error Notifications

Errors are automatically sent to the configured email address with:

- Provider details
- Error message
- Troubleshooting steps
- Links to CloudWatch logs

## Troubleshooting

### Lambda Timeout

If downloads timeout, increase timeout/memory:

```hcl
lambda_timeout     = 1200  # 20 minutes
lambda_memory_size = 4096  # More memory = faster network
```

### Insufficient Storage

If running out of ephemeral storage:

```hcl
lambda_ephemeral_storage = 15360  # 15 GB
```

### API Rate Limits

Step Functions automatically retries with exponential backoff. Check `state_machine.json` for retry configuration.

## Security Best Practices

1. **Secrets Management**: Store `tfc_token` in AWS Secrets Manager or SSM Parameter Store
2. **Encryption**: Enable KMS encryption for S3 and CloudWatch Logs
3. **Network**: Deploy Lambda in VPC for enhanced security
4. **Least Privilege**: IAM roles follow principle of least privilege
5. **Audit**: Enable CloudTrail for API call auditing

## Clean Up

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete the S3 bucket and all provider configurations.

## Support

For issues or questions:

- Check CloudWatch Logs for detailed error traces
- Review Step Functions execution history
- Check email notifications for error details

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.14.0 |
| <a name="requirement_archive"></a> [archive](#requirement\_archive) | ~> 2.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_archive"></a> [archive](#provider\_archive) | 2.7.1 |
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.26.0 |
| <a name="provider_terraform"></a> [terraform](#provider\_terraform) | n/a |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_cloudwatch_event_rule.cleanup_schedule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule) | resource |
| [aws_cloudwatch_event_rule.stepfunctions_schedule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule) | resource |
| [aws_cloudwatch_event_target.cleanup](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target) | resource |
| [aws_cloudwatch_event_target.stepfunctions_schedule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target) | resource |
| [aws_cloudwatch_log_group.check_version](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_log_group.cleanup_old_versions](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_log_group.download_to_s3](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_log_group.error_handler](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_log_group.read_config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_log_group.stepfunctions](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_log_group.upload_from_s3](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_iam_role.eventbridge_stepfunctions](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.stepfunctions](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy.eventbridge_stepfunctions](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.lambda_kms](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.lambda_logging](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.lambda_s3](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.lambda_secrets](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.lambda_sns](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.lambda_vpc](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.stepfunctions_lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.stepfunctions_logs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_kms_grant.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_grant) | resource |
| [aws_lambda_function.check_version](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_function.cleanup_old_versions](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_function.download_to_s3](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_function.error_handler](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_function.read_config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_function.upload_from_s3](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_layer_version.requests](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_layer_version) | resource |
| [aws_lambda_permission.allow_eventbridge_cleanup](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_s3_bucket.config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket_lifecycle_configuration.config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration) | resource |
| [aws_s3_bucket_ownership_controls.config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_ownership_controls) | resource |
| [aws_s3_bucket_policy.config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_policy) | resource |
| [aws_s3_bucket_public_access_block.config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block) | resource |
| [aws_s3_bucket_server_side_encryption_configuration.config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_server_side_encryption_configuration) | resource |
| [aws_s3_bucket_versioning.config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_versioning) | resource |
| [aws_s3_object.config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_object) | resource |
| [aws_secretsmanager_secret.tfc_token](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret) | resource |
| [aws_secretsmanager_secret_version.tfc_token](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_version) | resource |
| [aws_sfn_state_machine.provider_sync](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sfn_state_machine) | resource |
| [aws_sns_topic.errors](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic) | resource |
| [aws_sns_topic_policy.errors](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_policy) | resource |
| [aws_sns_topic_subscription.email](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription) | resource |
| [terraform_data.ensure_lambda_layer_stability](https://registry.terraform.io/providers/hashicorp/terraform/latest/docs/resources/data) | resource |
| [terraform_data.lambda_builds_directory](https://registry.terraform.io/providers/hashicorp/terraform/latest/docs/resources/data) | resource |
| [archive_file.check_version](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [archive_file.cleanup_old_versions](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [archive_file.download_to_s3](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [archive_file.error_handler](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [archive_file.lambda_layer](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [archive_file.read_config](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [archive_file.upload_from_s3](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_allow_local_exec_commands"></a> [allow\_local\_exec\_commands](#input\_allow\_local\_exec\_commands) | Allow the execution of local-exec provisioner | `bool` | `false` | no |
| <a name="input_ca_bundle_secret_name"></a> [ca\_bundle\_secret\_name](#input\_ca\_bundle\_secret\_name) | AWS Secrets Manager secret name containing the CA bundle for TLS verification. If not provided, default system CA bundle will be used. | `string` | `""` | no |
| <a name="input_cleanup_cron_expression"></a> [cleanup\_cron\_expression](#input\_cleanup\_cron\_expression) | Cron expression for scheduled cleanup of old provider versions (e.g., 'cron(0 3 ? * SUN *)' for weekly on Sundays at 3 AM UTC). Set to null to disable scheduled cleanup. | `string` | `null` | no |
| <a name="input_cleanup_dry_run"></a> [cleanup\_dry\_run](#input\_cleanup\_dry\_run) | Run cleanup in dry-run mode (log what would be deleted without actually deleting) | `bool` | `false` | no |
| <a name="input_cleanup_keep_version_count"></a> [cleanup\_keep\_version\_count](#input\_cleanup\_keep\_version\_count) | Number of provider versions to keep during cleanup (older versions will be deleted) | `number` | `10` | no |
| <a name="input_cloudwatch_logs_retention_days"></a> [cloudwatch\_logs\_retention\_days](#input\_cloudwatch\_logs\_retention\_days) | CloudWatch Logs retention in days | `number` | `30` | no |
| <a name="input_config_bucket_name"></a> [config\_bucket\_name](#input\_config\_bucket\_name) | S3 bucket name for provider configurations (if null, one will be created) | `string` | `null` | no |
| <a name="input_config_json"></a> [config\_json](#input\_config\_json) | Provider configuration JSON content to be uploaded to S3 | `string` | n/a | yes |
| <a name="input_kms_key_arn"></a> [kms\_key\_arn](#input\_kms\_key\_arn) | ARN of customer-managed KMS key for encryption (S3, Secrets Manager, SNS). If not provided, AWS managed keys will be used. | `string` | `null` | no |
| <a name="input_lambda_ephemeral_storage"></a> [lambda\_ephemeral\_storage](#input\_lambda\_ephemeral\_storage) | Lambda ephemeral storage in MB | `number` | `10240` | no |
| <a name="input_lambda_layer_arn"></a> [lambda\_layer\_arn](#input\_lambda\_layer\_arn) | ARN of the Lambda layer to use | `string` | `null` | no |
| <a name="input_lambda_memory_size"></a> [lambda\_memory\_size](#input\_lambda\_memory\_size) | Lambda function memory size in MB | `number` | `3008` | no |
| <a name="input_lambda_runtime"></a> [lambda\_runtime](#input\_lambda\_runtime) | Lambda runtime version | `string` | `"python3.12"` | no |
| <a name="input_lambda_timeout"></a> [lambda\_timeout](#input\_lambda\_timeout) | Lambda function timeout in seconds | `number` | `900` | no |
| <a name="input_notification_emails"></a> [notification\_emails](#input\_notification\_emails) | Email address for error notifications | `list(string)` | n/a | yes |
| <a name="input_project_name"></a> [project\_name](#input\_project\_name) | Project name used for resource naming | `string` | `"terraform-provider-sync"` | no |
| <a name="input_schedule_cron_expression"></a> [schedule\_cron\_expression](#input\_schedule\_cron\_expression) | Cron expression for scheduled Step Functions execution (e.g., 'cron(0 2 * * ? *)' for daily at 2 AM UTC). Set to null to disable scheduled execution. | `string` | `null` | no |
| <a name="input_sns_topic_display_name"></a> [sns\_topic\_display\_name](#input\_sns\_topic\_display\_name) | Display name for the SNS topic (used in email notifications) | `string` | `null` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Additional tags to apply to all resources | `map(string)` | `{}` | no |
| <a name="input_tfc_address"></a> [tfc\_address](#input\_tfc\_address) | HCP Terraform or Terraform Enterprise address | `string` | `"https://app.terraform.io"` | no |
| <a name="input_tfc_organization"></a> [tfc\_organization](#input\_tfc\_organization) | HCP Terraform or Terraform Enterprise organization name | `string` | n/a | yes |
| <a name="input_tfc_token"></a> [tfc\_token](#input\_tfc\_token) | HCP Terraform or Terraform Enterprise API token | `string` | n/a | yes |
| <a name="input_vpc_security_group_ids"></a> [vpc\_security\_group\_ids](#input\_vpc\_security\_group\_ids) | List of VPC security group IDs for Lambda functions (check\_version and download\_and\_upload). Required if vpc\_subnet\_ids is provided. | `list(string)` | `null` | no |
| <a name="input_vpc_subnet_ids"></a> [vpc\_subnet\_ids](#input\_vpc\_subnet\_ids) | List of VPC subnet IDs for Lambda functions (check\_version and download\_and\_upload). If provided, Lambda functions will be deployed in VPC. | `list(string)` | `null` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_cloudwatch_log_groups"></a> [cloudwatch\_log\_groups](#output\_cloudwatch\_log\_groups) | CloudWatch Log Group names for debugging |
| <a name="output_config_bucket_arn"></a> [config\_bucket\_arn](#output\_config\_bucket\_arn) | ARN of the S3 bucket for provider configurations |
| <a name="output_config_bucket_name"></a> [config\_bucket\_name](#output\_config\_bucket\_name) | Name of the S3 bucket for provider configurations |
| <a name="output_example_config_format"></a> [example\_config\_format](#output\_example\_config\_format) | Example config.json format for multiple providers |
| <a name="output_execution_command"></a> [execution\_command](#output\_execution\_command) | Example AWS CLI command to execute the state machine with array config |
| <a name="output_lambda_function_arns"></a> [lambda\_function\_arns](#output\_lambda\_function\_arns) | ARNs of all Lambda functions |
| <a name="output_sns_topic_arn"></a> [sns\_topic\_arn](#output\_sns\_topic\_arn) | ARN of the SNS topic for error notifications |
| <a name="output_state_machine_arn"></a> [state\_machine\_arn](#output\_state\_machine\_arn) | ARN of the Step Functions state machine |
| <a name="output_state_machine_name"></a> [state\_machine\_name](#output\_state\_machine\_name) | Name of the Step Functions state machine |
| <a name="output_tfc_token_secret_arn"></a> [tfc\_token\_secret\_arn](#output\_tfc\_token\_secret\_arn) | ARN of the Secrets Manager secret containing the TFC token |
| <a name="output_tfc_token_secret_name"></a> [tfc\_token\_secret\_name](#output\_tfc\_token\_secret\_name) | Name of the Secrets Manager secret containing the TFC token |
<!-- END_TF_DOCS -->
