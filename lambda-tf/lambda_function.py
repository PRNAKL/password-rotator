"""Handles automated AWS Secrets Manager password rotation and backup to S3 via AWS Lambda.

This script:
1. Pulls new secure passwords via external API.
2. Retrieves existing secrets from Secrets Manager.
3. Backs up the current secrets to S3 in JSON format.
4. Rotates each user's password.
5. Updates the secret in Secrets Manager.

All configurations such as SECRET_NAME and BUCKET_NAME must be set in environment variables via Terraform.
"""

import json
import os
import uuid
import logging

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
        RequestException: If API call fails or times out.
    """
    url = os.environ['PASSWORD_API_URL']# move to env variables on lambda
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()['pws'][0]
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise


def get_clients():
    """
    Initialize and return AWS Secrets Manager and S3 clients using the default region.

    Returns:
        tuple: (secrets_client, s3_client)
    """
    region = boto3.session.Session().region_name or 'us-east-1'
    secrets_client = boto3.client('secretsmanager', region_name=region)
    s3_client = boto3.client('s3', region_name=region)
    return secrets_client, s3_client


def fetch_current_secrets(secrets_client, secret_name):
    """
    Step 1: Fetch the current secrets from AWS Secrets Manager.

    Args:
        secrets_client (boto3 client): The Secrets Manager client.
        secret_name (str): The name of the secret.

    Returns:
        dict: Dictionary of secrets.
    """
    current = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(current['SecretString'])


def backup_to_s3(s3_client, bucket_name, secret_name, secrets):
    """
    Step 2: Backup current secrets to S3 in JSON format.

    Args:
        s3_client (boto3 client): The S3 client.
        bucket_name (str): The target S3 bucket.
        secret_name (str): Name of the secret (used in filename).
        secrets (dict): The secrets to back up.
    """
    backup_filename = f"{uuid.uuid4().hex[:6]}_{secret_name}_backup.json"
    s3_client.put_object(
        Bucket=bucket_name,
        Key=backup_filename,
        Body=json.dumps(secrets, indent=2).encode('utf-8')
    )
    logger.info(f"Backup uploaded to s3://{bucket_name}/{backup_filename}")


def rotate_passwords(secrets):
    """
    Step 3: Rotate passwords using the API for each user in the secrets.

    Args:
        secrets (dict): Current secrets mapping usernames to passwords.

    Returns:
        dict: Updated secrets with new passwords.
    """
    for email in secrets:
        secrets[email] = api_pull()
    return secrets


def update_secrets(secrets_client, secret_name, secrets):
    """
    Step 4: Update AWS Secrets Manager with rotated secrets.

    Args:
        secrets_client (boto3 client): The Secrets Manager client.
        secret_name (str): Name of the secret to update.
        secrets (dict): New secrets dictionary.
    """
    secrets_client.update_secret(
        SecretId=secret_name,
        SecretString=json.dumps(secrets)
    )
    logger.info("Secrets updated successfully.")


def lambda_handler(event, context):
    """
    AWS Lambda entry point.

    Retrieves secrets, backs them up, rotates passwords, and updates Secrets Manager.

    Returns:
        dict: Status code and response message.
    """
    secret_name = os.environ['SECRET_NAME']  # set in terraform get rid of default values
    bucket_name = os.environ['BUCKET_NAME']  # set in terraform get rid of default values

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
        logger.error(f"AWS Client error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
