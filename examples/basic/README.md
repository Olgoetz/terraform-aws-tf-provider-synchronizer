# Basic Example

This example demonstrates a minimal configuration for the Terraform Provider Synchronizer with only required parameters.

## Features

- Basic provider synchronization workflow
- Email error notifications
- AWS-managed encryption (default)
- S3 trigger on config.json upload
- No VPC deployment
- No scheduled execution

## Usage

### 1. Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
aws_region         = "us-east-1"
tfc_organization   = "your-organization"
notification_email = "ops@example.com"
```

### 2. Set TFC Token

```bash
export TF_VAR_tfc_token="your-hcp-terraform-token"
```

### 3. Deploy

```bash
terraform init
terraform plan
terraform apply
```

### 4. Upload Configuration

Create `config.json`:

```json
[
  {
    "namespace": "hashicorp",
    "provider": "aws",
    "version": "latest",
    "gpg-key-id": "34365D9472D7468F",
    "platforms": ["darwin_amd64", "linux_amd64"]
  }
]
```

Upload to trigger synchronization:

```bash
aws s3 cp config.json s3://$(terraform output -raw config_bucket_name)/config.json
```

## Outputs

```bash
# Get state machine ARN
terraform output state_machine_arn

# Get S3 bucket name
terraform output config_bucket_name

# Get execution command
terraform output -raw execution_command
```

## Cost Estimate

**Monthly cost**: ~$5-10 USD

- Lambda: ~$2-5 (depends on execution frequency)
- Step Functions: ~$0.25 per 1000 executions
- S3: ~$0.023 per GB
- SNS: First 1000 emails free
- CloudWatch Logs: ~$0.50 per GB

## Clean Up

```bash
terraform destroy
```

## Next Steps

- See [Complete Example](../complete/) for advanced features
- Review [Architecture Documentation](../../ARCHITECTURE.md)
- Check [Main README](../../provider-manager/README.md) for troubleshooting

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.14.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6.0 |

## Providers

No providers.

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_provider_sync"></a> [provider\_sync](#module\_provider\_sync) | ../../ | n/a |

## Resources

No resources.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region) | AWS region to deploy resources | `string` | `"us-east-1"` | no |
| <a name="input_notification_email"></a> [notification\_email](#input\_notification\_email) | Email address for error notifications | `string` | n/a | yes |
| <a name="input_project_name"></a> [project\_name](#input\_project\_name) | Project name used for resource naming | `string` | `"terraform-provider-sync"` | no |
| <a name="input_tfc_organization"></a> [tfc\_organization](#input\_tfc\_organization) | HCP Terraform or Terraform Enterprise organization name | `string` | n/a | yes |
| <a name="input_tfc_token"></a> [tfc\_token](#input\_tfc\_token) | HCP Terraform or Terraform Enterprise API token | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_cloudwatch_log_groups"></a> [cloudwatch\_log\_groups](#output\_cloudwatch\_log\_groups) | CloudWatch Log Group names for debugging |
| <a name="output_config_bucket_arn"></a> [config\_bucket\_arn](#output\_config\_bucket\_arn) | ARN of the S3 bucket for provider configurations |
| <a name="output_config_bucket_name"></a> [config\_bucket\_name](#output\_config\_bucket\_name) | Name of the S3 bucket for provider configurations |
| <a name="output_execution_command"></a> [execution\_command](#output\_execution\_command) | Example AWS CLI command to execute the state machine |
| <a name="output_lambda_function_arns"></a> [lambda\_function\_arns](#output\_lambda\_function\_arns) | ARNs of all Lambda functions |
| <a name="output_sns_topic_arn"></a> [sns\_topic\_arn](#output\_sns\_topic\_arn) | ARN of the SNS topic for error notifications |
| <a name="output_state_machine_arn"></a> [state\_machine\_arn](#output\_state\_machine\_arn) | ARN of the Step Functions state machine |
| <a name="output_state_machine_name"></a> [state\_machine\_name](#output\_state\_machine\_name) | Name of the Step Functions state machine |
<!-- END_TF_DOCS -->
