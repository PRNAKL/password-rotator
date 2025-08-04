# Randomized Suffix for S3 Bucket Name
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Conditionally Create S3 Bucket
resource "aws_s3_bucket" "my_bucket" {
  count         = var.existing_bucket_name == "" ? 1 : 0
  bucket        = "prnakl-terraform-bucket-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = {
    Environment = "dev"
    Owner       = "you"
  }
}

# Unified Bucket Reference
locals {
  use_existing_bucket = var.existing_bucket_name != ""
  resolved_bucket_name = local.use_existing_bucket ? var.existing_bucket_name : (
    length(aws_s3_bucket.my_bucket) > 0 ? aws_s3_bucket.my_bucket[0].bucket : ""
  )
  bucket_name = local.resolved_bucket_name
  bucket_arn  = "arn:aws:s3:::${local.bucket_name}"
}