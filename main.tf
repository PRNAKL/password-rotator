# Randomized Suffix for S3 Bucket Name
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Conditionally Create S3 Bucket
resource "aws_s3_bucket" "my_bucket" {
  count         = var.existing_bucket_name == "" ? 1 : 0
  bucket        = "prnakl-terraform-bucket-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = {
    Environment = "dev"
    Owner       = "you"
  }
}

# Unified Bucket Reference
locals {
  use_existing_bucket    = var.existing_bucket_name != ""
  resolved_bucket_name   = local.use_existing_bucket ? var.existing_bucket_name : (
    length(aws_s3_bucket.my_bucket) > 0 ? aws_s3_bucket.my_bucket[0].bucket : ""
  )
  bucket_name            = local.resolved_bucket_name
  bucket_arn             = "arn:aws:s3:::${local.bucket_name}"
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_execution_role_v2"

  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

data "archive_file" "zip_files"{
  for_each = toset([
  for x in fileset("${path.module}/lambda_src/", "**") : split("/", x)[0]
  if !endswith(x, ".zip")
  ])
  type = "zip"
  source_dir ="${path.module}/lambda_src/${each.key}"
  output_path ="${path.module}/lambda_src/${each.key}.zip"

}


# Lambda Function
resource "aws_lambda_function" "my_lambda" {
  function_name = "THETerraformLambda"
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"

filename         = data.archive_file.zip_files["lambda_functions"].output_path
source_code_hash = data.archive_file.zip_files["lambda_functions"].output_base64sha256
  timeout          = 30

  layers = [
    "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python39:30"
  ]

  environment {
    variables = {
      SECRET_NAME      = var.secret_name
      BUCKET_NAME      = local.bucket_name
      PASSWORD_API_URL = var.API_url
    }
  }

  tags = {
    Environment = "dev"
    Owner       = "you"
  }
}

# Attach AWS-Managed Logging Policy
resource "aws_iam_policy_attachment" "lambda_logs" {
  name       = "lambda_logs"
  roles      = [aws_iam_role.lambda_exec_role.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom IAM Policy: Secrets Manager + S3
resource "aws_iam_policy" "lambda_secrets_s3_policy" {
  name        = "lambda_secrets_s3_policy_v2"
  description = "Allows Lambda to access Secrets Manager and S3 bucket for backups"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:UpdateSecret"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject"
        ],
        Resource = [
          "${local.bucket_arn}/*"
        ]
      }
    ]
  })
}

# Attach Custom Policy to Lambda Role
resource "aws_iam_policy_attachment" "lambda_secrets_s3_attach" {
  name       = "lambda_secrets_s3_attach"
  roles      = [aws_iam_role.lambda_exec_role.name]
  policy_arn = aws_iam_policy.lambda_secrets_s3_policy.arn
}
