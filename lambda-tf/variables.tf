# Environment the infrastructure is being deployed to (e.g., dev, staging, prod)
variable "environment" {
  type        = string
  default     = "dev"
  description = "Deployment environment name"
}

# Name of the AWS Secrets Manager secret
variable "secret_name" {
  type        = string
  default     = "Users"
  description = "The name of the AWS Secrets Manager secret"
}

# URL of the external password generation API
variable "API_url" {
  type        = string
  default     = "https://makemeapassword.ligos.net/api/v1/alphanumeric/json?c=1&l=12&sym=T"
  description = "The URL for the password generation API"
}
