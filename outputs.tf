
#Output: S3 Bucket Name
output "s3_bucket_name" {
  description = "The name of the generated S3 bucket"
  value       = local.bucket_name
}

output "lambda_files" {
  value = fileset("${path.module}/lambda_src", "**")
}
