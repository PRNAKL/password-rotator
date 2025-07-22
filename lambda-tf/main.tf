# Random suffix for bucket
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 bucket
resource "aws_s3_bucket" "my_bucket" {
  bucket         = "prnakl-terraform-bucket-${random_id.bucket_suffix.hex}"
  force_destroy  = true
  tags = {
    Environment = "dev"
    Owner       = "you"
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_execution_role_v2"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Action    = "sts:AssumeRole",
        Effect    = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda function
resource "aws_lambda_function" "my_lambda" {
  function_name    = "THETerraformLambda"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  filename         = "${path.module}/lambda_function.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda_function.zip")
  timeout          = 30

  layers = [
    "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python39:30"
  ]

  environment {
    variables = {
      SECRET_NAME = var.secret_name
      BUCKET_NAME      = aws_s3_bucket.my_bucket.bucket
      PASSWORD_API_URL = var.API_url
    }
  }

  tags = {
    Environment = "dev"
    Owner       = "you"
  }
}

# Attach Lambda basic execution policy
resource "aws_iam_policy_attachment" "lambda_logs" {
  name       = "lambda_logs"
  roles      = [aws_iam_role.lambda_exec_role.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for Lambda access to Secrets Manager and S3
resource "aws_iam_policy" "lambda_secrets_s3_policy" {
  name = "lambda_secrets_s3_policy_v2"  # changed
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
          "${aws_s3_bucket.my_bucket.arn}/*"
        ]
      }
    ]
  })
}

# Attach custom IAM policy to Lambda execution role
resource "aws_iam_policy_attachment" "lambda_secrets_s3_attach" {
  name       = "lambda_secrets_s3_attach"
  roles      = [aws_iam_role.lambda_exec_role.name]
  policy_arn = aws_iam_policy.lambda_secrets_s3_policy.arn
}
