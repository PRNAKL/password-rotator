resource "aws_s3_bucket" "rotation_bucket" {
  bucket        = var.bucket_name
  force_destroy = true  # Allows deletion even if the bucket has objects
}