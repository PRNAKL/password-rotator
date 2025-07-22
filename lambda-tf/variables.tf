# Example to make your config reusable in the future
variable "environment" {
  default = "dev"
}

variable "secret_name" {
  default = "Users"
}
variable "API_url" {
      default = "https://makemeapassword.ligos.net/api/v1/alphanumeric/json?c=1&l=12&sym=T"
}