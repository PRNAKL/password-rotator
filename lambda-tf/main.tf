# Terraform block specifies required provider plugins and Terraform version
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"  # Use the official AWS provider
      version = "~> 6.0"         # Use any version >= 6.0 and < 7.0
    }
  }
  required_version = ">= 1.3.0"  # Require Terraform 1.3.0 or newer
}

# Configure the AWS provider with the region to use
provider "aws" {
  region = "us-east-1"  # All resources will be created in this AWS region
}

# Generate a short random hex string (used to make S3 bucket names globally unique)
resource "random_id" "bucket_suffix" {
  byte_length = 4  # Generates an 8-character hex string (4 bytes = 32 bits)
}

# Create an S3 bucket for logging, backups, or Lambda usage
resource "aws_s3_bucket" "my_bucket" {
  bucket = "Terraform-bucket-${random_id.bucket_suffix.hex}"  # Unique name
  force_destroy = true  # Deletes the bucket even if it's not empty (use with caution in production)

  tags = {
    Environment = "dev"  # Useful for cost tracking and resource organization
    Owner = "you"
  }
}

# IAM Role that Lambda will assume to execute
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_execution_role"  # Name that shows in the IAM console

  # JSON IAM policy allowing Lambda service to assume this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17", # IAM policy version
    Statement = [
      {
        Action = "sts:AssumeRole", # Allows assuming the role
        Effect = "Allow", # Grant permission
        Principal = {
          Service = "lambda.amazonaws.com"   # Only the Lambda service can assume this role
        }
      }
    ]
  })
}

# Attach basic Lambda execution permissions (writes logs to CloudWatch)
resource "aws_iam_policy_attachment" "lambda_logs" {
  name = "lambda_logs"  # Friendly name for the policy attachment
  roles = [aws_iam_role.lambda_exec_role.name]  # Attach to the role we created above
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"  # Built-in AWS policy
}

# Create the Lambda function itself
resource "aws_lambda_function" "my_lambda" {
  function_name = "MyTerraformLambda"  # Name of the function in AWS Lambda console
  role = aws_iam_role.lambda_exec_role.arn  # IAM Role ARN Lambda will assume
  handler = "password_rotator.lambda_handler"  # Format: filename.function (no .py)
  runtime = "python3.9"  # AWS Lambda Python runtime to use
  filename = "${path.module}/lambda_function.zip"  # Path to zipped code (relative to main.tf)

  # Hash the ZIP file contents so Terraform knows when the code changes (triggers re-deploy)
  source_code_hash = filebase64sha256("${path.module}/lambda_function.zip")

  tags = {
    Environment = "dev"
    Owner       = "you"
  }
}

# Output the deployed Lambda’s name to the CLI after `terraform apply`
output "lambda_function_name" {
  value = aws_lambda_function.my_lambda.function_name
}

# Output the generated S3 bucket name (since it includes a random suffix)
output "s3_bucket_name" {
  value = aws_s3_bucket.my_bucket.bucket
}
