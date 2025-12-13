action "aws_sfn_start_execution" "upload_provider" {
  config {
    state_machine_arn = aws_sfn_state_machine.provider_sync.arn
    input = jsonencode({
      bucket = aws_s3_bucket.config.id
      key    = "config.json"
    })
  }
}

action "aws_sfn_start_execution" "upload_provider_fail" {
  config {
    state_machine_arn = aws_sfn_state_machine.provider_sync.arn
    input = jsonencode({
      bucket = aws_s3_bucket.config.id
      key    = "config2.json"
    })
  }
}


action "aws_lambda_invoke" "cleanup_old_versions" {
  config {
    function_name = aws_lambda_function.cleanup_old_versions.function_name
    payload       = jsonencode({})
  }
}
