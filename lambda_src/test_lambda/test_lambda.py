"""AWS Lambda handler to rotate Secrets Manager passwords and backup to S3."""

import json
import logging  # For logging level constants
import os
import uuid

import boto3
import requests
from botocore.exceptions import ClientError

from logger import Logger

logger = Logger()  # instantiate custom Logger


def api_pull():
    """Pull a secure 12-character alphanumeric password from external API.

    Returns:
        str: Generated password string.

    Raises:
        requests.exceptions.RequestException: If API call fails.
        ValueError: If API_url env var is missing.
    """
    url = os.environ.get("API_url")
    if url is None:
        logger.log_message(logging.ERROR,
                           "API_url environment variable is not set")
        raise ValueError("API_url environment variable is not set")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()["pws"][0]
    except requests.exceptions.RequestException as error:
        logger.log_message(logging.ERROR, f"API request failed: {error}")
        raise


def get_clients():
    """Initialize AWS Secrets Manager and S3 clients.

    Returns:
        tuple: (secrets_client, s3_client)
    """
    region = boto3.session.Session().region_name or "us-east-1"
    secrets_client = boto3.client("secretsmanager", region_name=region)
    s3_client = boto3.client("s3", region_name=region)
    return secrets_client, s3_client


def fetch_current_secrets(secrets_client, secret_name):
    """Fetch current secrets from AWS Secrets Manager.

    Args:
        secrets_client: Secrets Manager client.
        secret_name (str): The secret's name.

    Returns:
        dict: Secrets stored in the secret.

    Raises:
        ClientError: If unable to fetch secrets.
    """
    try:
        current = secrets_client.get_secret_value(SecretId=secret_name)
        return json.loads(current["SecretString"])
    except ClientError as error:
        logger.log_message(logging.ERROR, f"Failed to fetch secrets: {error}")
        raise


def backup_to_s3(s3_client, bucket_name, secret_name, secrets):
    """Backup current secrets to S3 as JSON file.

    Args:
        s3_client: S3 client.
        bucket_name (str): S3 bucket name.
        secret_name (str): Name of the secret.
        secrets (dict): Secrets data.
    """
    backup_filename = f"{uuid.uuid4().hex[:6]}_{secret_name}_backup.json"
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=backup_filename,
            Body=json.dumps(secrets, indent=2).encode("utf-8"),
        )
        logger.log_message(logging.INFO,
                           f"Backup uploaded to s3://{bucket_name}/"
                           f"{backup_filename}")
    except ClientError as error:
        logger.log_message(logging.ERROR,
                           f"Failed to upload backup to S3: {error}")
        raise


def rotate_passwords(secrets):
    """Generate new passwords for each user in the secrets dict.

    Args:
        secrets (dict): Current secrets.

    Returns:
        dict: Updated secrets.
    """
    for email in secrets:
        secrets[email] = api_pull()
    return secrets


def update_secrets(secrets_client, secret_name, secrets):
    """Update AWS Secrets Manager with new passwords.

    Args:
        secrets_client: Secrets Manager client.
        secret_name (str): Name of the secret.
        secrets (dict): Updated secrets.
    """
    try:
        secrets_client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(secrets)
        )
        logger.log_message(logging.INFO, "Secrets updated successfully.")
    except ClientError as error:
        logger.log_message(logging.ERROR, f"Failed to update secrets: {error}")
        raise


def lambda_handler(_event, _context):
    """AWS Lambda function handler.

    Args:
        _event: Lambda event data (ignored).
        _context: Lambda context object (ignored).

    Returns:
        dict: Response with status code and message.
    """
    secret_name = os.environ.get("SECRET_NAME")
    bucket_name = os.environ.get("BUCKET_NAME")

    if secret_name is None or bucket_name is None:
        logger.log_message(
            logging.ERROR,
            "Environment variables SECRET_NAME or BUCKET_NAME not set"
        )
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "SECRET_NAME or BUCKET_NAME env vars missing"}),
        }

    secrets_client, s3_client = get_clients()

    try:
        secrets = fetch_current_secrets(secrets_client, secret_name)
        backup_to_s3(s3_client, bucket_name, secret_name, secrets)
        updated_secrets = rotate_passwords(secrets)
        update_secrets(secrets_client, secret_name, updated_secrets)
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Password rotation and backup completed."}
            ),
        }
    except ClientError as error:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(error)}),
        }
