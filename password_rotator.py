"""Handles password rotation and backup of AWS Secrets to S3"""

import json
import uuid
import boto3
from botocore.exceptions import ClientError
import requests


def api_pull():
    """Pulls a list of passwords from the API into a JSON format"""
    api_url = 'https://makemeapassword.ligos.net/api/v1/alphanumeric/json?c=1&l=12&sym=T'
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get('pws')
    except requests.exceptions.RequestException as e:
        print(f'API request failed: {e}')
        raise e


def get_secret():
    """Retrieves the current 'Users' secret from AWS Secrets Manager"""
    secret_name = "Users"
    region_name = "us-east-1"

    session = boto3.session.Session(profile_name='devops-trainee')
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name)
        secret_str = get_secret_value_response['SecretString']
        return json.loads(secret_str)
    except ClientError as e:
        raise e


def update_secret(secret_name, updated_dict):
    """Updates the specified secret with a new user-password dictionary"""
    session = boto3.session.Session(profile_name='devops-trainee')
    current_region = session.region_name or 'us-east-2'
    client = session.client(service_name='secretsmanager',
                            region_name=current_region)

    try:
        client.put_secret_value(
            SecretId=secret_name,
            SecretString=json.dumps(updated_dict)
        )
        print('Secret updated successfully!')
    except ClientError as e:
        print(f'Error! {e}')


def create_temp_file(size, file_name, file_content):
    """Creates a temporary file with randomized prefix containing the provided content"""
    random_file_name = '_'.join([str(uuid.uuid4().hex[:6]), file_name])
    with open(random_file_name, 'w', encoding='utf-8') as f:
        f.write(str(file_content) * size)
    return random_file_name


def s3_upload(file_path: str, bucket_name: str, object_name: str) -> None:
    """Uploads a local file to the specified S3 bucket and object key"""
    try:
        session = boto3.session.Session(profile_name='devops-trainee')
        s3 = session.client('s3')
        s3.upload_file(file_path, bucket_name, object_name)
        print(f'Uploaded {file_path} to s3://{bucket_name}/{object_name}')
    except ClientError as e:
        print(e)


if __name__ == '__main__':
    """Backs up existing secret to S3 and rotates all passwords using API"""
    users = get_secret()

    # Backup current secret to S3
    json_data = json.dumps(users)
    temp_file_name = create_temp_file(
        size=1, file_name='users.json', file_content=json_data)
    bucket_name = 'firstpythonbucket-f9d567d1-46e0-4a5b-98bb-2b1e99cf4192'
    object_name = 'secrets/users.json'
    s3_upload(file_path=temp_file_name,
              bucket_name=bucket_name, object_name=object_name)

    # Rotate passwords
    for email in users:
        new_pass = api_pull()[0]  # Take only the first password from the list
        users[email] = new_pass

    update_secret("Users", users)
