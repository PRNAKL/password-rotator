"""Handles AWS Secrets Manager password rotation and backup to S3 via AWS Lambda.

Steps:
1. Pull a new secure password from an external API.
2. Fetch current secrets from Secrets Manager.
3. Backup current secrets to S3.
4. Rotate and update the passwords.
"""

import json
import logging
import os
import uuid

import boto3
import requests
from botocore.exceptions import ClientError

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def api_pull():
    """
    Pull a secure 12-character alphanumeric password from makemeapassword API.

    Returns:
        str: Generated password string.

    Raises:
        requests.exceptions.RequestException: If API call fails.
    """
    url = os.environ["API_url"]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()["pws"][0]
    except requests.exceptions.RequestException as e:
        logger.error("API request failed: %s", e)
        raise


def get_clients():
    """
    Initialize AWS Secrets Manager and S3 clients.

    Returns:
        tuple: (secrets_client, s3_client)
    """
    region = boto3.session.Session().region_name or "us-east-1"
    secrets_client = boto3.client("secretsmanager", region_name=region)
    s3_client = boto3.client("s3", region_name=region)
    return secrets_client, s3_client


def fetch_current_secrets(secrets_client, secret_name):
    """
    Fetch the current secrets from AWS Secrets Manager.

    Args:
        secrets_client: The Secrets Manager client.
        secret_name (str): The name of the secret.

    Returns:
        dict: Dictionary of secrets.
    """
    try:
        current = secrets_client.get_secret_value(SecretId=secret_name)
        return json.loads(current["SecretString"])
    except ClientError as e:
        logger.error("Failed to fetch secrets: %s", e)
        raise


def backup_to_s3(s3_client, bucket_name, secret_name, secrets):
    """
    Backup current secrets to S3 in JSON format.

    Args:
        s3_client: The S3 client.
        bucket_name (str): The S3 bucket name.
        secret_name (str): The secret name.
        secrets (dict): The secrets to back up.
    """
    backup_filename = f"{uuid.uuid4().hex[:6]}_{secret_name}_backup.json"
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=backup_filename,
            Body=json.dumps(secrets, indent=2).encode("utf-8")
        )
        logger.info("Backup uploaded to s3://%s/%s", bucket_name, backup_filename)
    except ClientError as e:
        logger.error("Failed to upload backup to S3: %s", e)
        raise


def rotate_passwords(secrets):
    """
    Generate new passwords for each user in the secrets.

    Args:
        secrets (dict): Current secrets.

    Returns:
        dict: Updated secrets.
    """
    for email in secrets:
        secrets[email] = api_pull()
    return secrets


def update_secrets(secrets_client, secret_name, secrets):
    """
    Update AWS Secrets Manager with new passwords.

    Args:
        secrets_client: The Secrets Manager client.
        secret_name (str): Secret name.
        secrets (dict): Updated secrets.
    """
    try:
        secrets_client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(secrets)
        )
        logger.info("Secrets updated successfully.")
    except ClientError as e:
        logger.error("Failed to update secrets: %s", e)
        raise


def lambda_handler(event, context):
    """
    Lambda entry point for password rotation and backup.

    Args:
        event: Lambda event object.
        context: Lambda context object.

    Returns:
        dict: Response with statusCode and message.
    """
    secret_name = os.environ["SECRET_NAME"]
    bucket_name = os.environ["BUCKET_NAME"]

    secrets_client, s3_client = get_clients()

    try:
        secrets = fetch_current_secrets(secrets_client, secret_name)
        backup_to_s3(s3_client, bucket_name, secret_name, secrets)
        updated_secrets = rotate_passwords(secrets)
        update_secrets(secrets_client, secret_name, updated_secrets)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Password rotation and backup completed."})
        }

    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
