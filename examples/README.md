# Terraform Provider Synchronizer - Examples

This directory contains example configurations demonstrating how to use the Terraform Provider Synchronizer as a module.

## Available Examples

### [Basic Example](./basic/)

Minimal configuration with required parameters only. Best for quick start and simple use cases.

**Features:**

- Basic provider synchronization
- Email notifications
- Default AWS-managed encryption
- S3 trigger on config upload

**Use Case:** Simple provider mirroring for a single organization

---

### [Complete Example](./complete/)

Full-featured configuration showcasing all available options.

**Features:**

- VPC deployment for enhanced security
- Customer-managed KMS encryption
- Scheduled sync (daily)
- Scheduled cleanup (weekly)
- Custom retention policies
- SNS topic display name
- All optional features enabled

**Use Case:** Production deployment with enterprise security requirements

---

## Usage

Each example includes:

- `main.tf` - Main configuration calling the module
- `variables.tf` - Input variable definitions
- `outputs.tf` - Output values
- `terraform.tfvars.example` - Example variable values
- `README.md` - Specific documentation

### Quick Start

```bash
# Navigate to desired example
cd examples/basic  # or examples/complete

# Copy and customize variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply configuration
terraform apply
```

## Module Source Options

### Local Path (Development)

```hcl
module "provider_sync" {
  source = "../../provider-manager"
  # ...
}
```

### Git Repository

```hcl
module "provider_sync" {
  source = "git::https://github.com/your-org/terraform-aws-provider-synchronizer.git//provider-manager?ref=v1.0.0"
  # ...
}
```

### Terraform Registry (if published)

```hcl
module "provider_sync" {
  source  = "your-org/provider-sync/aws"
  version = "~> 1.0"
  # ...
}
```

## Common Patterns

### Multi-Environment Setup

Create separate configurations for each environment:

```
examples/
├── dev/
│   ├── main.tf
│   └── terraform.tfvars
├── staging/
│   ├── main.tf
│   └── terraform.tfvars
└── prod/
    ├── main.tf
    └── terraform.tfvars
```

### Workspace-based Deployment

Use Terraform workspaces with a single configuration:

```bash
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

terraform workspace select dev
terraform apply -var-file=dev.tfvars
```

## Best Practices

1. **Use specific module versions** in production
2. **Store sensitive values** in AWS Secrets Manager or Parameter Store
3. **Enable encryption** with customer-managed KMS keys
4. **Configure VPC** for enhanced security
5. **Set appropriate retention** for logs and S3 versions
6. **Test in non-production** environment first
7. **Enable scheduled cleanup** to manage storage costs

## Support

For detailed documentation, see:

- [Main README](../provider-manager/README.md)
- [Architecture Documentation](../ARCHITECTURE.md)
- [Terraform Auto-generated Docs](../provider-manager/README.md#terraform-docs)
