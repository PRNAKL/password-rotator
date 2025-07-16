output "bucket_name" {
  value = aws_s3_bucket.rotation_bucket.bucket
}
#Exposes the name of the bucket to other modules or the root config.