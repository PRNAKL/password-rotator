#################################################
# IAM ROLE AND POLICIES FOR LAMBDA FUNCTION
#################################################

# Lambda execution role
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_execution_role_v3"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Attach AWS managed logging policy (CloudWatch Logs) to Lambda role
resource "aws_iam_policy_attachment" "lambda_logs" {
  name       = "lambda_logs"
  roles      = [aws_iam_role.lambda_exec_role.name]  # reference role name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"  # AWS managed policy
}

# Custom IAM policy for Lambda to access S3/secrets
resource "aws_iam_policy" "lambda_secrets_s3_policy" {
  name        = "lambda_secrets_s3_policy_v3"
  description = "Policy for Lambda to access secrets and S3"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Effect   = "Allow"
        Resource = "*"  # restrict later to specific bucket/ARN if needed
      }
    ]
  })
}

# Attach the custom Lambda policy to the execution role
resource "aws_iam_policy_attachment" "lambda_secrets_s3_attach" {
  name       = "lambda_secrets_s3_attach"
  roles      = [aws_iam_role.lambda_exec_role.name]
  policy_arn = aws_iam_policy.lambda_secrets_s3_policy.arn
}

# Attach additional permissions if needed (example: deploy Lambda permissions)
resource "aws_iam_policy_attachment" "lambda_permissions_attach" {
  name       = "lambda_permissions_attach"
  roles      = [aws_iam_role.lambda_exec_role.name]
  policy_arn = aws_iam_policy.lambda_secrets_s3_policy.arn  # replace with actual policy ARN if different
}
