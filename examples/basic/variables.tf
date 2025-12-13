variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
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

variable "notification_email" {
  description = "Email address for error notifications"
  type        = string
}
