"""Handles password rotation and backup of AWS Secrets to S3."""

import json
import uuid
import boto3
from botocore.exceptions import ClientError
import requests


def api_pull():
    """
    Pull a randomly generated password from the external API.

    Uses the 'makemeapassword' API to fetch a single 12-character
    alphanumeric password that includes symbols.

    Returns:
        str: A randomly generated password string.

    Raises:
        requests.exceptions.RequestException: If the API call fails or times out.
    """
    api_url = 'https://makemeapassword.ligos.net/api/v1/alphanumeric/json?c=1&l=12&sym=T'
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get('pws')[0]
    except requests.exceptions.RequestException as e:
        print(f'API request failed: {e}')
        raise e


def get_secret():
    """
    Retrieve the current 'Users' secret from AWS Secrets Manager.

    Assumes the AWS profile 'devops-trainee' is configured.
    Parses the returned secret string into a Python dictionary.

    Returns:
        dict: Dictionary containing the current user-password pairs.

    Raises:
        botocore.exceptions.ClientError: If the secret cannot be retrieved.
    """
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
    """
    Update a given secret in AWS Secrets Manager with new data.

    Args:
        secret_name (str): The name of the secret to update.
        updated_dict (dict): Dictionary of updated key-value pairs (e.g., users and new passwords).

    Returns:
        None

    Raises:
        botocore.exceptions.ClientError: If the secret update fails.
    """
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
    """
    Create a temporary local file with a randomized prefix.

    The file will be filled with the provided content repeated `size` times.
    Useful for staging content (such as a secrets JSON) before uploading to S3.

    Args:
        size (int): Number of times to repeat the content string.
        file_name (str): Base name of the file to create.
        file_content (str): Content to write into the file.

    Returns:
        str: Name of the generated temporary file."""
    random_file_name = '_'.join([str(uuid.uuid4().hex[:6]), file_name])
    with open(random_file_name, 'w', encoding='utf-8') as f:
        f.write(str(file_content) * size)
    return random_file_name


def s3_upload(file_path: str, bucket_name: str, object_name: str) -> None:
    """
    Upload a local file to a specified AWS S3 bucket and object key.

    Args:
        file_path (str): Path to the local file to upload.
        bucket_name (str): Name of the S3 bucket.
        object_name (str): Key (i.e., path) to store the object under in S3.

    Returns:
        None

    Raises:
        botocore.exceptions.ClientError: If the upload fails.
    """
    try:
        session = boto3.session.Session(profile_name='devops-trainee')
        s3 = session.client('s3')
        s3.upload_file(file_path, bucket_name, object_name)
        print(f'Uploaded {file_path} to s3://{bucket_name}/{object_name}')
    except ClientError as e:
        print(e)

    """Main script logic:
    - Retrieves the 'Users' secret from Secrets Manager.
    - Backs up the current secret to an S3 bucket as a temporary JSON file.
    - Generates new passwords via API for each user and updates the secret."""


if __name__ == '__main__':
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
        new_pass = api_pull()
        users[email] = new_pass

    update_secret("Users", users)
