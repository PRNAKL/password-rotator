
resource "aws_s3_bucket" "rotation_bucket" {
  bucket  =var.bucket_name
  force_destroy = true
}
/*creates an S3 bucket with the name bucket_name
and then allows terraform to destroy the bucket even if it has files in it*/

#
