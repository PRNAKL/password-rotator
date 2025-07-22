"""Handles password rotation and backup of AWS Secrets to S3."""

import json
import os
import uuid
import logging
import boto3
import requests
from botocore.exceptions import ClientError, BotoCoreError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def api_pull():
    """
    Pull a randomly generated password from the external API.

    Returns:
        str: A randomly generated password string.

    Raises:
        requests.exceptions.RequestException: If the API call fails or times out.
    """
    api_url = (
        "https://makemeapassword.ligos.net/api/v1/alphanumeric/json?c=1&l=12&sym=T"
    )
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get("pws")[0]
    except requests.exceptions.RequestException as e:
        logger.error("API request failed: %s", e)
        raise


def get_secret(session=None):
    """
    Retrieve the current 'Users' secret from AWS Secrets Manager.

    Args:
        session (boto3.session.Session, optional): A boto3 session object.

    Returns:
        dict: Parsed JSON dictionary representing the secret's key-value pairs.
    """
    secret_name = "Users"
    region_name = "us-east-1"

    if session is None:
        session = boto3.session.Session()
    client = session.client("secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        return json.loads(get_secret_value_response["SecretString"])
    except ClientError as e:
        logger.error("Error retrieving secret: %s", e)
        raise


def update_secret(secret_name, updated_dict, session=None):
    """
    Update a secret in AWS Secrets Manager with new data.

    Args:
        secret_name (str): The name or ARN of the secret to update.
        updated_dict (dict): New secret data to store.
        session (boto3.session.Session, optional): A boto3 session object.

    Returns:
        None
    """
    if session is None:
        session = boto3.session.Session()
    region = session.region_name or "us-east-1"
    client = session.client("secretsmanager", region_name=region)

    try:
        client.update_secret(
            SecretId=secret_name, SecretString=json.dumps(updated_dict)
        )
        logger.info("Secret updated successfully!")
    except ClientError as e:
        logger.error("Error updating secret: %s", e)
        raise


def create_temp_file(size, file_name, file_content):
    """
    Create a temporary local file with a randomized prefix.

    Args:
        size (int): Number of times to repeat the content string.
        file_name (str): Name of the file to create.
        file_content (str): Content to write into the file.

    Returns:
        str: Name of the generated file.
    """
    random_file_name = f"{uuid.uuid4().hex[:6]}_{file_name}"
    with open(random_file_name, "w", encoding="utf-8") as f:
        f.write(str(file_content) * size)
    return random_file_name


def s3_upload(file_path, bucket_name, object_name, session=None):
    """
    Upload a local file to an AWS S3 bucket.

    Args:
        file_path (str): Local file path.
        bucket_name (str): S3 bucket name.
        object_name (str): Key name in the bucket.
        session (boto3.session.Session, optional): A boto3 session object.

    Returns:
        None
    """
    if session is None:
        session = boto3.session.Session()
    s3 = session.client("s3")
    try:
        s3.upload_file(file_path, bucket_name, object_name)
        logger.info("Uploaded %s to s3://%s/%s", file_path, bucket_name, object_name)
    except ClientError as e:
        logger.error("Error uploading to S3: %s", e)
        raise


if __name__ == "__main__":
    # Script entry point: Rotate AWS Secrets and back them up to S3
    try:
        users = get_secret()
        json_data = json.dumps(users)
        temp_file_name = create_temp_file(1, "users.json", json_data)

        bucket_name = "firstpythonbucket-f9d567d1-46e0-4a5b-98bb-2b1e99cf4192"
        object_name = "secrets/users.json"

        s3_upload(temp_file_name, bucket_name, object_name)
        os.remove(temp_file_name)

        for email in users:
            users[email] = api_pull()

        update_secret("Users", users)

    except (ClientError, BotoCoreError, requests.exceptions.RequestException) as e:
        logger.error("Error during password rotation process: %s", e)
    except Exception as e:
        logger.error("Unexpected error during password rotation process: %s", e)
