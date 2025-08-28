
data "archive_file" "lambda_zip" {
  for_each = toset([for x in fileset("${path.module}/lambda_src", "**") : split("/", "${x}")[0]])
  type = "zip"
  source_dir = "${path.module}/src/${each.key}"
  output_path = "${path.module}/${each.key}.zip"
}
# Lambda Function
resource "aws_lambda_function" "my_lambda" {
  for_each = data.archive_file.lambda_zip

  function_name = each.key
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "${each.key}.lambda_handler"
  runtime       = "python3.9"

  filename         = "${data.archive_file.lambda_zip[each.key].output_path}"
  source_code_hash = "${data.archive_file.lambda_zip[each.key].output_base64sha256}"
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


