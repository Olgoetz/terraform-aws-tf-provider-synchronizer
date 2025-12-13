terraform {
  required_version = ">= 1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Basic module configuration with only required parameters
module "provider_sync" {
  source = "../../"

  # Required variables
  project_name       = var.project_name
  tfc_organization   = var.tfc_organization
  tfc_token          = var.tfc_token
  notification_email = var.notification_email

  # Optional: Override AWS region if needed
  aws_region = var.aws_region

  # Optional: Add resource tags
  tags = {
    Environment = "dev"
    ManagedBy   = "terraform"
    Example     = "basic"
  }
}
