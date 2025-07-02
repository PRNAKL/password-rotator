import boto3
import uuid
# s3_client = boto3.client('s3')

# s3_resource = boto3.resource('s3')
  
# s3_resource.meta.client.generate_presigned_url()

def create_bucket_name(bucket_prefix):
  # the bucket name must be 3-63 characters
  return f'{bucket_prefix}-{uuid.uuid4()}'

# print(create_bucket_name('test_name'))

def create_bucket(bucket_prefix):
  session = boto3.session.Session(profile_name = 'devops-trainee')  # generate a session in current region
  current_region = session.region_name or 'us-east-2'  # fallback if None
  print(f"Current region detected: {current_region!r}")  # Debug print added here
  s3_client = session.client("s3", region_name=current_region)
  bucket_name = create_bucket_name(bucket_prefix)  # generates a bucket name using the prefix
  if current_region == 'us-east-1':
    bucket_response = s3_client.create_bucket(  # creates the bucket 
      Bucket=bucket_name)
  else:
    bucket_response = s3_client.create_bucket(
      Bucket=bucket_name,
      CreateBucketConfiguration={
        'LocationConstraint': current_region}) 

  print(bucket_name, current_region)
  return bucket_name, bucket_response

if __name__ == '__main__':
  # create_bucket('firstpythonbucket' )
  