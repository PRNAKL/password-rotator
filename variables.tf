variable "environment" {
  type        = string
  default     = "dev"
  description = "Deployment environment name"
}

variable "secret_name" {
  type        = string
  default     = "Users"
  description = "The name of the AWS Secrets Manager secret"
}

variable "api_url" {
  type        = string
  default     = "https://makemeapassword.ligos.net/api/v1/alphanumeric/json?c=1&l=12&sym=T"
  description = "The URL for the password generation API"
}

variable "existing_bucket_name" {
  type        = string
  default     = ""
  description = "Optional: Use this to specify an existing S3 bucket for storing old passwords. Leave blank to create a new one."
}

variable "deploy_lambda_permissions" {
  description = "The ARN for Lambda permissions"
  type        = string
}
