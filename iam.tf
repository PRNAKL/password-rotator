# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_execution_role_v3"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Custom IAM Policy: Secrets Manager + S3
resource "aws_iam_policy" "lambda_secrets_s3_policy" {
  name        = "lambda_secrets_s3_policy_v3"
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

# Attach Lambda deployment permissions from GitHub Secret ARN
resource "aws_iam_role_policy_attachment" "lambda_permissions_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = var.deploy_lambda_permissions
}

# IAM Policy: Full SNS + CloudWatch + Logs
resource "aws_iam_policy" "full_cloudwatch_sns_policy" {
  name        = "full_cloudwatch_sns_policy"
  description = "Full SNS and CloudWatch access for Lambda and Terraform"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:*",
          "logs:*",
          "cloudwatch:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach the policy to the Lambda execution role
resource "aws_iam_role_policy_attachment" "attach_full_cloudwatch_sns" {
  role       = "invoke_lambda_permissions"
  policy_arn = aws_iam_policy.full_cloudwatch_sns_policy.arn
}

# SNS Topic for Lambda alerts
resource "aws_sns_topic" "lambda_alerts" {
  name = "lambda-error-alerts"
}

# SNS Email Subscription
resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.lambda_alerts.arn
  protocol  = "email"
  endpoint  = "gunner.fox5274@gmail.com"
}

# CloudWatch Alarm for Lambda errors
resource "aws_cloudwatch_metric_alarm" "lambda_error_alarm" {
  alarm_name          = "LambdaErrorAlarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  statistic           = "Sum"
  period              = 60
  threshold           = 1
  treat_missing_data  = "missing"

  dimensions = {
    FunctionName = "password_rotator"
  }

  alarm_description = "Alarm when Lambda errors occur"
  alarm_actions     = [aws_sns_topic.lambda_alerts.arn]
}
