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


def get_secret(session=None):
    """
    Retrieve the current 'Users' secret from AWS Secrets Manager.

    Connects to AWS Secrets Manager and fetches the secret value
    identified by the fixed secret name "Users" in the 'us-east-1' region.

    Args:
        session (boto3.session.Session, optional): A boto3 session object.
            If None, a new default session is created without specifying a profile.

    Returns:
        dict: Parsed JSON dictionary representing the secret's key-value pairs.

    Raises:
        botocore.exceptions.ClientError: If there is an error retrieving the secret.
    """
    secret_name = "Users"
    region_name = "us-east-1"

    if session is None:
        session = boto3.session.Session()  # Default session, no profile forced
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret_str = get_secret_value_response['SecretString']
        return json.loads(secret_str)
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise e


def update_secret(secret_name, updated_dict, session=None):
    """
    Update a secret in AWS Secrets Manager with new data.

    Sends a new JSON-encoded secret string to AWS Secrets Manager,
    replacing the existing secret value for the specified secret.

    Args:
        secret_name (str): The name or ARN of the secret to update.
        updated_dict (dict): Dictionary containing updated key-value pairs to store.
        session (boto3.session.Session, optional): A boto3 session object.
            If None, a new default session is created without specifying a profile.

    Returns:
        None

    Raises:
        botocore.exceptions.ClientError: If updating the secret fails.
    """
    if session is None:
        session = boto3.session.Session()  # Default session, no profile forced
    current_region = session.region_name or 'us-east-1'
    client = session.client(service_name='secretsmanager', region_name=current_region)

    try:
        client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(updated_dict)
        )
        print('Secret updated successfully!')
    except ClientError as e:
        print(f"Error updating secret: {e}")
        raise e


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


def s3_upload(file_path: str, bucket_name: str, object_name: str, session=None) -> None:
    """
    Upload a local file to an AWS S3 bucket at the specified object key.

    Args:
        file_path (str): The local path to the file that should be uploaded.
        bucket_name (str): The target S3 bucket name.
        object_name (str): The key (path) to assign to the uploaded object in the bucket.
        session (boto3.session.Session, optional): A boto3 session object.
            If None, a new default session is created without specifying a profile.

    Returns:
        None

    Raises:
        botocore.exceptions.ClientError: If the upload operation fails.
    """
    try:
        if session is None:
            session = boto3.session.Session()  # Default session, no profile forced
        s3 = session.client('s3')
        s3.upload_file(file_path, bucket_name, object_name)
        print(f'Uploaded {file_path} to s3://{bucket_name}/{object_name}')
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        raise e


if __name__ == '__main__':
    """
    Main script logic:
    - Retrieves the 'Users' secret from Secrets Manager.
    - Backs up the current secret to an S3 bucket as a temporary JSON file.
    - Generates new passwords via API for each user and updates the secret.
    """
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
