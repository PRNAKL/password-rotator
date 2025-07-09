'''DOCSTRING
this document fucks shit up
'''
import uuid
import boto3
from botocore.exceptions import ClientError
# s3_client = boto3.client('s3')

# s3_resource = boto3.resource('s3')

# s3_resource.meta.client.generate_presigned_url()


def create_bucket_name(bucket_prefix):
    ''' DOCSTRING'''
    # the bucket name must be 3-63 characters
    return f'{bucket_prefix}-{uuid.uuid4()}'

# print(create_bucket_name('test_name'))


def create_bucket(bucket_prefix):
    ''' DOCSTRING'''
    try:
        # generate a session in current region
        session = boto3.session.Session(profile_name='devops-trainee')
        current_region = session.region_name or 'us-east-2'  # fallback if None
        # Debug print added here
        print(f"Current region detected: {current_region!r}")
        s3_client = session.client("s3", region_name=current_region)
        # generates a bucket name using the prefix
        bucket_name = create_bucket_name(bucket_prefix)
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
    except ClientError as e:
        print(e)


# creates a randomly named file that we can use to upload to the bucket
def create_temp_file(size, file_name, file_content):
    ''' DOCSTRING'''
    # generates the name using uuid4 but only the first 0-6 characters
    random_file_name = ' '.join([str(uuid.uuid4().hex[:6]), file_name])
    with open(random_file_name, 'w', encoding='utf-8') as f:
        f.write(str(file_content) * size)
    return random_file_name


def s3_upload(file_path: str, bucket_name: str, object_name: str) -> None:
    ''' DOCSTRING'''
    try:
        session = boto3.session.Session(profile_name='devops-trainee')
        s3 = session.client('s3')
        # file_path = './bucket_names.txt'
        # bucket_name = 'firstpythonbucket-f9d567d1-46e0-4a5b-98bb-2b1e99cf4192'
        # object_name = 'first object'
        s3.upload_file(file_path, bucket_name, object_name)
    except ClientError as e:
        print(e)


if __name__ == '__main__':
    # create_bucket('firstpythonbucket')
    s3_upload('./bucket_names.txt',
              'firstpythonbucket-f9d567d1-46e0-4a5b-98bb-2b1e99cf4192',
              'first object')
