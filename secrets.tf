# AWS Secrets Manager secret for TFC/TFE token
resource "aws_secretsmanager_secret" "tfc_token" {
  name                    = "${var.project_name}/tfc-token"
  description             = "HCP Terraform / Terraform Enterprise API token"
  recovery_window_in_days = 0
  kms_key_id              = var.kms_key_arn

  tags = merge(
    var.tags,
    {
      Name = "TFC Token"
    }
  )
}

# Store the token value in the secret
resource "aws_secretsmanager_secret_version" "tfc_token" {
  secret_id     = aws_secretsmanager_secret.tfc_token.id
  secret_string = var.tfc_token
}
