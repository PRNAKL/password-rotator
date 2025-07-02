import boto3
import uuid

def create_bucket_name(bucket_prefix):
    # the bucket name must be 3-63 characters
    return f'{bucket_prefix}-{uuid.uuid4()}'

def create_bucket(bucket_prefix, access_key, secret_key, region):
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    )
    
    current_region = region
    print(f"Current region detected: {current_region!r}")
    
    s3_client = session.client('s3')
    bucket_name = create_bucket_name(bucket_prefix)
    
    if current_region == 'us-east-1':
        bucket_response = s3_client.create_bucket(Bucket=bucket_name)
    else:
        bucket_response = s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': current_region}
        )
    
    print(bucket_name, current_region)
    return bucket_name, bucket_response

# Example usage:
# Replace with your actual credentials
# create_bucket('firstpythonbucket', 'YOUR_ACCESS_KEY_ID', 'YOUR_SECRET_ACCESS_KEY', 'us-east-1')
