locals {
  lambda_dirs = toset([
    for d in fileset("${path.module}/lambda_src/lambda_functions", "*") : d
    if fileexists("${path.module}/lambda_src/lambda_functions/${d}/") # ensures it's a dir
  ])
}

# Create a ZIP file of everything in lambda_src/lambda_functions
data "archive_file" "lambda_zip" {
  for_each = local.lambda_dirs
  type = "zip"
  source_dir = "${path.module}/lambda_src/${each.key}"
  output_path = "${path.module}/lambda_src/${each.key}.zip"
}
# Lambda Function
resource "aws_lambda_function" "my_lambda" {
  for_each = data.archive_file.lambda_zip

  function_name = each.key
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "${each.key}.lambda_handler"
  runtime       = "python3.9"

  filename         = each.value.output_path
  source_code_hash = each.value.output_base64sha256
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


