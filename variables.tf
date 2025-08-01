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

variable "API_url" {
  type        = string
  default     = "https://makemeapassword.ligos.net/api/v1/alphanumeric/json?c=1&l=12&sym=T"
  description = "The URL for the password generation API"
}

variable "existing_bucket_name" {
  type        = string
  default     = "prnakl-terraform-bucket-8aae6c0e"
  description = "Optional: Use this to specify an existing S3 bucket for storing old passwords. Leave blank to create a new one."
}
