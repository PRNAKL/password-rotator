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

# Custom IAM Policy: EventBridge Scheduler (updated for Terraform/GitHub Actions)
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
        Resource = "arn:aws:scheduler:us-east-1:967246349943:schedule/*"
      },
      {
        Sid    = "IAMPassRoleForScheduler",
        Effect = "Allow",
        Action = [
          "iam:PassRole"
        ],
        Resource = "arn:aws:iam::967246349943:role/lambda_execution_role_v3",
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

# EventBridge Scheduler: trigger Lambda every 10 minutes
resource "aws_scheduler_schedule" "every_10_min" {
  name       = "password_rotator-every-10-min"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(10 minutes)"

  target {
    arn      = aws_lambda_function.my_lambda["password_rotator"].arn
    role_arn = aws_iam_role.lambda_exec_role.arn
  }
}
