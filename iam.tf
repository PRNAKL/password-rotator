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

# Custom IAM Policy: EventBridge Scheduler
resource "aws_iam_policy" "lambda_eventbridge_policy" {
  name        = "lambda_eventbridge_policy_v1"
  description = "Allows Lambda (via Terraform) to manage EventBridge Scheduler"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "EventBridgeSchedulerFullAccess",
        Effect = "Allow",
        Action = [
          "scheduler:CreateSchedule",
          "scheduler:UpdateSchedule",
          "scheduler:DeleteSchedule",
          "scheduler:DescribeSchedule",
          "scheduler:ListSchedules",
          "scheduler:TagResource",
          "scheduler:UntagResource"
        ],
        Resource = var.eventbridge_scheduler
      },
      {
        Sid    = "IAMPassRoleForScheduler",
        Effect = "Allow",
        Action = [
          "iam:PassRole"
        ],
        Resource = var.lambda_exec_role_v3,
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "scheduler.amazonaws.com"
          }
        }
      }
    ]
  })
}

# Attach EventBridge Policy to Lambda Execution Role
resource "aws_iam_policy_attachment" "lambda_eventbridge_attach" {
  name       = "lambda_eventbridge_attach"
  roles      = [aws_iam_role.lambda_exec_role.name]
  policy_arn = aws_iam_policy.lambda_eventbridge_policy.arn
}

# IAM Role for EventBridge Scheduler
resource "aws_iam_role" "scheduler_role" {
  name = "eventbridge_scheduler_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "scheduler.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Policy to allow scheduler to invoke password_rotator Lambda
resource "aws_iam_role_policy" "scheduler_invoke_lambda" {
  name = "scheduler-invoke-password-rotator"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = "lambda:InvokeFunction",
        Resource = var.lambda_function_arn
      }
    ]
  })
}

# EventBridge Scheduler: trigger Lambda every 24 hours
resource "aws_scheduler_schedule" "every_24_hrs" {
  name       = "password_rotator-every-24-hrs"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(1 day)"

  target {
    arn      = aws_lambda_function.my_lambda["password_rotator"].arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}

# IAM Policy: Full SNS + CloudWatch + Logs
resource "aws_iam_policy" "full_cloudwatch_sns_policy" {
  name        = "full_cloudwatch_sns_policy"
  description = "Full SNS and CloudWatch access for Lambda and Terraform"

  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "sns:*",
          "logs:*",
          "cloudwatch:*"
        ],
        Resource = "*"
      }
    ]
  })
}

# Attach the policy to the Lambda execution role
resource "aws_iam_role_policy_attachment" "attach_full_cloudwatch_sns" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.full_cloudwatch_sns_policy.arn
}

# SNS Topic for Lambda alerts
resource "aws_sns_topic" "lambda_alerts" {
  name = "lambda-error-alerts"
}

# SNS Email Subscription
resource "aws_sns_topic_subscription" "email_alert" {
  for_each = toset(var.alarm_notification_emails)

  topic_arn = aws_sns_topic.lambda_alerts.arn
  protocol  = "email"
  endpoint  = "gunner.fox5274@gmail.com"

  lifecycle {
    ignore_changes = [endpoint]
  }
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
