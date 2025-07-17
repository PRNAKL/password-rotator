provider "aws" {
  region = "us-east-1"
}

# Generates a random suffix for the S3 bucket to ensure uniqueness
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

module "s3" {
  source      = "./modules/s3"
  bucket_name = "password-rotator-${random_id.bucket_suffix.hex}"
}

module "lambda" {
  source            = "./modules/lambda"
  function_name     = "password-rotator"
  role_arn          = var.role_arn
  handler           = "main.lambda_handler"
  runtime           = "python3.11"
  lambda_zip        = "lambda_placeholder.zip"
  environment_vars = {
    BUCKET_NAME = module.s3.bucket_name
  }
}
