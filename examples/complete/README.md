# Complete Example

This example demonstrates a full-featured production-ready configuration with all optional features enabled.

## Features

- ✅ VPC deployment for enhanced security
- ✅ Customer-managed KMS encryption
- ✅ Scheduled synchronization (daily at 2 AM UTC)
- ✅ Scheduled cleanup (weekly on Sundays at 3 AM UTC)
- ✅ Custom log retention (90 days)
- ✅ Version cleanup (keep 10 versions)
- ✅ SNS topic display name
- ✅ Increased Lambda resources
- ✅ Comprehensive tagging

## Prerequisites

1. **VPC with private subnets** and NAT Gateway
2. **Security group** allowing outbound HTTPS
3. **KMS key** for encryption (or let Terraform create one)
4. **HCP Terraform/TFE token** with provider management permissions

## Usage

### 1. Create KMS Key (Optional)

```bash
aws kms create-key \
  --description "Terraform Provider Sync Encryption Key" \
  --tags TagKey=Name,TagValue=provider-sync-key
```

### 2. Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values (see example file for details).

### 3. Set Sensitive Variables

```bash
export TF_VAR_tfc_token="your-hcp-terraform-token"
```

### 4. Deploy

```bash
terraform init
terraform plan
terraform apply
```

### 5. Verify Deployment

```bash
# Check Step Functions state machine
aws stepfunctions list-state-machines

# Check EventBridge rules
aws events list-rules --name-prefix terraform-provider-sync

# View Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `terraform-provider-sync`)]'
```

## Configuration Details

### VPC Configuration

Lambda functions are deployed in private subnets with:

- NAT Gateway for internet access
- Security group allowing HTTPS outbound
- VPC endpoints (optional) for AWS services

### Encryption

All data encrypted with customer-managed KMS key:

- S3 bucket (config storage)
- Secrets Manager (TFC token)
- SNS topic (notifications)
- CloudWatch Logs

### Scheduling

**Sync Schedule**: Daily at 2 AM UTC

```
cron(0 2 * * ? *)
```

**Cleanup Schedule**: Weekly on Sundays at 3 AM UTC

```
cron(0 3 ? * SUN *)
```

### Version Cleanup

- Keeps 10 most recent versions per provider
- Dry-run mode disabled (actual deletion)
- Runs weekly to manage storage costs

## Monitoring

### CloudWatch Dashboards

Create custom dashboard:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name provider-sync \
  --dashboard-body file://dashboard.json
```

### CloudWatch Alarms

Monitor Lambda errors:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name provider-sync-lambda-errors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold
```

## Cost Estimate

**Monthly cost**: ~$50-100 USD (production workload)

- Lambda: ~$20-40 (VPC, scheduled execution)
- Step Functions: ~$1-2
- S3: ~$5-10
- VPC: ~$30 (NAT Gateway)
- KMS: ~$1
- SNS: ~$1
- CloudWatch Logs: ~$5-10

**Cost Optimization Tips**:

1. Use VPC endpoints instead of NAT Gateway
2. Reduce log retention period
3. Decrease cleanup keep count
4. Optimize Lambda memory allocation

## Security Considerations

### Network Isolation

- Lambda functions in private subnets
- No direct internet access
- All traffic through NAT Gateway or VPC endpoints

### Encryption

- Data encrypted at rest (KMS)
- Data encrypted in transit (TLS)
- Secrets never exposed in logs

### Access Control

- IAM roles follow least privilege
- KMS key policies restrict access
- S3 bucket blocks public access

### Compliance

- CloudTrail logging enabled
- VPC Flow Logs (optional)
- AWS Config rules (optional)

## Disaster Recovery

### Backup Strategy

- S3 versioning enabled (90-day retention)
- Terraform state in remote backend
- KMS key with deletion protection

### Recovery Procedures

1. **Lambda failure**: Automatic retries in Step Functions
2. **S3 data loss**: Restore from version history
3. **Complete region failure**: Deploy to secondary region

## Clean Up

```bash
# Destroy all resources
terraform destroy

# Or selective cleanup
terraform destroy -target=module.provider_sync.aws_lambda_function.cleanup_old_versions
```

## Next Steps

- Configure CloudWatch alarms
- Set up cross-region replication
- Implement backup automation
- Create runbooks for operations team
- Review [Architecture Documentation](../../ARCHITECTURE.md)

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.14.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.26.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_provider_sync"></a> [provider\_sync](#module\_provider\_sync) | ../../ | n/a |

## Resources

| Name | Type |
|------|------|
| [aws_kms_alias.provider_sync](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_alias) | resource |
| [aws_kms_key.provider_sync](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_allow_local_exec_commands"></a> [allow\_local\_exec\_commands](#input\_allow\_local\_exec\_commands) | Allow the execution of local-exec provisioner | `bool` | n/a | yes |
| <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region) | AWS region to deploy resources | `string` | `"us-east-1"` | no |
| <a name="input_cleanup_cron_expression"></a> [cleanup\_cron\_expression](#input\_cleanup\_cron\_expression) | Cron expression for scheduled cleanup execution | `string` | `"cron(0 3 ? * SUN *)"` | no |
| <a name="input_cleanup_dry_run"></a> [cleanup\_dry\_run](#input\_cleanup\_dry\_run) | Run cleanup in dry-run mode | `bool` | `false` | no |
| <a name="input_cleanup_keep_version_count"></a> [cleanup\_keep\_version\_count](#input\_cleanup\_keep\_version\_count) | Number of provider versions to keep during cleanup | `number` | `10` | no |
| <a name="input_cloudwatch_logs_retention_days"></a> [cloudwatch\_logs\_retention\_days](#input\_cloudwatch\_logs\_retention\_days) | CloudWatch Logs retention in days | `number` | `90` | no |
| <a name="input_cost_center"></a> [cost\_center](#input\_cost\_center) | Cost center for billing | `string` | `"engineering"` | no |
| <a name="input_create_kms_key"></a> [create\_kms\_key](#input\_create\_kms\_key) | Whether to create a new KMS key | `bool` | `true` | no |
| <a name="input_environment"></a> [environment](#input\_environment) | Environment name (dev, staging, prod) | `string` | `"prod"` | no |
| <a name="input_kms_key_arn"></a> [kms\_key\_arn](#input\_kms\_key\_arn) | ARN of existing KMS key (if create\_kms\_key is false) | `string` | `null` | no |
| <a name="input_lambda_ephemeral_storage"></a> [lambda\_ephemeral\_storage](#input\_lambda\_ephemeral\_storage) | Lambda ephemeral storage in MB | `number` | `10240` | no |
| <a name="input_lambda_memory_size"></a> [lambda\_memory\_size](#input\_lambda\_memory\_size) | Lambda function memory size in MB | `number` | `3008` | no |
| <a name="input_lambda_timeout"></a> [lambda\_timeout](#input\_lambda\_timeout) | Lambda function timeout in seconds | `number` | `900` | no |
| <a name="input_notification_email"></a> [notification\_email](#input\_notification\_email) | Email address for error notifications | `string` | n/a | yes |
| <a name="input_project_name"></a> [project\_name](#input\_project\_name) | Project name used for resource naming | `string` | `"terraform-provider-sync"` | no |
| <a name="input_schedule_cron_expression"></a> [schedule\_cron\_expression](#input\_schedule\_cron\_expression) | Cron expression for scheduled sync execution | `string` | `"cron(0 2 * * ? *)"` | no |
| <a name="input_sns_topic_display_name"></a> [sns\_topic\_display\_name](#input\_sns\_topic\_display\_name) | Display name for the SNS topic | `string` | `"Terraform Provider Sync Notifications"` | no |
| <a name="input_tfc_address"></a> [tfc\_address](#input\_tfc\_address) | HCP Terraform or Terraform Enterprise address | `string` | `"https://app.terraform.io"` | no |
| <a name="input_tfc_organization"></a> [tfc\_organization](#input\_tfc\_organization) | HCP Terraform or Terraform Enterprise organization name | `string` | n/a | yes |
| <a name="input_tfc_token"></a> [tfc\_token](#input\_tfc\_token) | HCP Terraform or Terraform Enterprise API token | `string` | n/a | yes |
| <a name="input_vpc_security_group_ids"></a> [vpc\_security\_group\_ids](#input\_vpc\_security\_group\_ids) | List of VPC security group IDs for Lambda functions | `list(string)` | n/a | yes |
| <a name="input_vpc_subnet_ids"></a> [vpc\_subnet\_ids](#input\_vpc\_subnet\_ids) | List of VPC subnet IDs for Lambda functions | `list(string)` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_cloudwatch_log_groups"></a> [cloudwatch\_log\_groups](#output\_cloudwatch\_log\_groups) | CloudWatch Log Group names for debugging |
| <a name="output_config_bucket_arn"></a> [config\_bucket\_arn](#output\_config\_bucket\_arn) | ARN of the S3 bucket for provider configurations |
| <a name="output_config_bucket_name"></a> [config\_bucket\_name](#output\_config\_bucket\_name) | Name of the S3 bucket for provider configurations |
| <a name="output_execution_command"></a> [execution\_command](#output\_execution\_command) | Example AWS CLI command to execute the state machine |
| <a name="output_kms_key_arn"></a> [kms\_key\_arn](#output\_kms\_key\_arn) | ARN of the KMS key used for encryption |
| <a name="output_kms_key_id"></a> [kms\_key\_id](#output\_kms\_key\_id) | ID of the KMS key used for encryption |
| <a name="output_lambda_function_arns"></a> [lambda\_function\_arns](#output\_lambda\_function\_arns) | ARNs of all Lambda functions |
| <a name="output_sns_topic_arn"></a> [sns\_topic\_arn](#output\_sns\_topic\_arn) | ARN of the SNS topic for error notifications |
| <a name="output_state_machine_arn"></a> [state\_machine\_arn](#output\_state\_machine\_arn) | ARN of the Step Functions state machine |
| <a name="output_state_machine_name"></a> [state\_machine\_name](#output\_state\_machine\_name) | Name of the Step Functions state machine |
| <a name="output_tfc_token_secret_arn"></a> [tfc\_token\_secret\_arn](#output\_tfc\_token\_secret\_arn) | ARN of the Secrets Manager secret containing the TFC token |
| <a name="output_tfc_token_secret_name"></a> [tfc\_token\_secret\_name](#output\_tfc\_token\_secret\_name) | Name of the Secrets Manager secret containing the TFC token |
<!-- END_TF_DOCS -->
