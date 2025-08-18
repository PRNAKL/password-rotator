"""Handles password rotation and backup of AWS Secrets to S3."""

import json
import os
import uuid

import boto3
import requests
from botocore.exceptions import ClientError, BotoCoreError

from lambda_src.lambda_functions.logger import Logger

logger = Logger()


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
    api_url = "https://makemeapassword.ligos.net/api/v1/alphanumeric/json?c=1&l=12&sym=T"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get("pws")[0]
    except requests.exceptions.RequestException as e:
        logger.log_message(40, f"API request failed: {e}")
        raise


def get_secret(session=None):
    """
    Retrieve the current 'Users' secret from AWS Secrets Manager.

    Assumes the AWS profile 'devops-trainee' is configured.
    Parses the returned secret string into a Python dictionary.

    Args:
        session (boto3.session.Session, optional): A boto3 session object.

    Returns:
        dict: Dictionary containing the current user-password pairs.

    Raises:
        botocore.exceptions.ClientError: If the secret cannot be retrieved.
    """
    secret_name = "Users"
    region_name = "us-east-1"

    if session is None:
        session = boto3.session.Session()
    client = session.client("secretsmanager", region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])
    except ClientError as e:
        logger.log_message(40, f"Error retrieving secret: {e}")
        raise


def update_secret(secret_name, updated_dict, session=None):
    """
    Update a given secret in AWS Secrets Manager with new data.

    Args:
        secret_name (str): The name of the secret to update.
        updated_dict (dict): Dictionary of updated key-value pairs (e.g., users and new passwords).
        session (boto3.session.Session, optional): A boto3 session object.

    Returns:
        None

    Raises:
        botocore.exceptions.ClientError: If the secret update fails.
    """
    if session is None:
        session = boto3.session.Session()
    region = session.region_name or "us-east-1"
    client = session.client("secretsmanager", region_name=region)

    try:
        client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(updated_dict)
        )
        logger.log_message(20, "Secret updated successfully!")
    except ClientError as e:
        logger.log_message(40, f"Error updating secret: {e}")
        raise


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
        str: Name of the generated temporary file.
    """
    random_file_name = f"{uuid.uuid4().hex[:6]}_{file_name}"
    with open(random_file_name, "w", encoding="utf-8") as f:
        f.write(str(file_content) * size)
    return random_file_name


def s3_upload(file_path, bucket_name, object_name, session=None):
    """
    Upload a local file to a specified AWS S3 bucket and object key.

    Args:
        file_path (str): Path to the local file to upload.
        bucket_name (str): Name of the S3 bucket.
        object_name (str): Key (i.e., path) to store the object under in S3.
        session (boto3.session.Session, optional): A boto3 session object.

    Returns:
        None

    Raises:
        botocore.exceptions.ClientError: If the upload fails.
    """
    if session is None:
        session = boto3.session.Session()
    s3 = session.client("s3")

    try:
        s3.upload_file(file_path, bucket_name, object_name)
        logger.log_message(20, f"Uploaded {file_path} to s3://{bucket_name}/{object_name}")
    except ClientError as e:
        logger.log_message(40, f"Error uploading to S3: {e}")
        raise


if __name__ == "__main__":
    # """
    # Main script logic:
    # - Retrieves the 'Users' secret from Secrets Manager.
    # - Backs up the current secret to an S3 bucket as a temporary JSON file.
    # - Generates new passwords via API for each user and updates the secret.
    # """
    try:
        users = get_secret()
        json_data = json.dumps(users)
        TEMP_FILE_NAME = create_temp_file(1, "users.json", json_data)

        S3_BUCKET_NAME = "firstpythonbucket-f9d567d1-46e0-4a5b-98bb-2b1e99cf4192"
        S3_OBJECT_KEY = "secrets/users.json"

        s3_upload(TEMP_FILE_NAME, S3_BUCKET_NAME, S3_OBJECT_KEY)
        os.remove(TEMP_FILE_NAME)

        for email in users:
            users[email] = api_pull()

        update_secret("Users", users)

    except (ClientError, BotoCoreError, requests.exceptions.RequestException) as e:
        logger.log_message(40, f"Error during password rotation process: {e}")
