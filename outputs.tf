#Output: Lambda Function Name
output "lambda_function_name" {
  description = "The name of the deployed AWS Lambda function"
  value       = aws_lambda_function.my_lambda.function_name
}

#Output: S3 Bucket Name
output "s3_bucket_name" {
  description = "The name of the generated S3 bucket"
  value       = local.bucket_name
}
