terraform {
  required_version = ">= 1.3.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region  = "us-east-1"

  assume_role {
    role_arn = "arn:aws:iam::967246349943:role/invoke_lambda_permissions"
    session_name = "github-actions"
  }
}

