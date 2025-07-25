import json
import os
import uuid
import boto3
import requests
import logging  # For logging level constants
from botocore.exceptions import ClientError

import sys
import pathlib
current_dir = pathlib.Path(__file__).parent.resolve()
parent_dir = current_dir.parent.resolve()
sys.path.insert(0, str(parent_dir))

from logger import Logger

logger = Logger()  # instantiate custom Logger


def api_pull():
    url = os.environ["API_url"]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()["pws"][0]
    except requests.exceptions.RequestException as e:
        logger.log_message(logging.ERROR, f"API request failed: {e}")
        raise


def get_clients():
    region = boto3.session.Session().region_name or "us-east-1"
    secrets_client = boto3.client("secretsmanager", region_name=region)
    s3_client = boto3.client("s3", region_name=region)
    return secrets_client, s3_client


def fetch_current_secrets(secrets_client, secret_name):
    try:
        current = secrets_client.get_secret_value(SecretId=secret_name)
        return json.loads(current["SecretString"])
    except ClientError as e:
        logger.log_message(logging.ERROR, f"Failed to fetch secrets: {e}")
        raise


def backup_to_s3(s3_client, bucket_name, secret_name, secrets):
    backup_filename = f"{uuid.uuid4().hex[:6]}_{secret_name}_backup.json"
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=backup_filename,
            Body=json.dumps(secrets, indent=2).encode("utf-8")
        )
        logger.log_message(logging.INFO, f"Backup uploaded to s3://{bucket_name}/{backup_filename}")
    except ClientError as e:
        logger.log_message(logging.ERROR, f"Failed to upload backup to S3: {e}")
        raise


def rotate_passwords(secrets):
    for email in secrets:
        secrets[email] = api_pull()
    return secrets


def update_secrets(secrets_client, secret_name, secrets):
    try:
        secrets_client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(secrets)
        )
        logger.log_message(logging.INFO, "Secrets updated successfully.")
    except ClientError as e:
        logger.log_message(logging.ERROR, f"Failed to update secrets: {e}")
        raise


def lambda_handler(_event, _context):
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
