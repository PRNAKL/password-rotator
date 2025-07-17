
resource "aws_s3_bucket" "rotation_bucket" {
  bucket  =var.bucket_name
  force_destroy = true
}
/*creates an S3 bucket with the name bucket_name
and then allows terraform to destroy the bucket even if it has files in it*/

resource "aws_lambda_function" "rotation_lambda" {
  function_name = var.function_name
  role = var.role_arn
  handler = var.handler
  runtime = var.runtime
  filename = var.lambda_zip
   source_code_hash = filebase64sha256(var.lambda_zip)
}

environment {
  variables = var.environment_vars
}
