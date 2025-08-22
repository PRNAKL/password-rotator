# Create a ZIP file of everything in lambda_src/lambda_functions
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_src/lambda_functions"
  output_path = "${path.module}/build/lambda_function.zip"
}

# Lambda Function
resource "aws_lambda_function" "my_lambda" {
  function_name = "THETerraformLambda"
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 30

  layers = [
    "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python39:30"
  ]

  environment {
    variables = {
      SECRET_NAME = var.secret_name
      BUCKET_NAME = local.bucket_name
      API_url     = var.api_url
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
