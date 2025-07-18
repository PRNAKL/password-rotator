"""Handles password rotation and backup of AWS Secrets to S3 via AWS Lambda."""

import json
import os
import uuid
import boto3
import requests
from botocore.exceptions import ClientError


def api_pull():
    """
    Pull a secure 12-character alphanumeric password from makemeapassword API.

    Returns:
        str: Generated password string.

    Raises:
        RequestException: If API call fails or times out.
    """
    url = 'https://makemeapassword.ligos.net/api/v1/alphanumeric/json?c=1&l=12&sym=T'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()['pws'][0]
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        raise


def lambda_handler(event, context):
    """
    Lambda entry point.

    1. Retrieve the current secret from Secrets Manager.
    2. Back it up to S3 as a JSON file.
    3. Rotate passwords for each user.
    4. Update the secret in AWS Secrets Manager.

    Environment Variables:
        SECRET_NAME: Name of the secret in Secrets Manager.
        BUCKET_NAME: Name of the S3 bucket used for backup.

    Returns:
        dict: Status code and message (JSON-encoded).
    """
    secret_name = os.environ.get('SECRET_NAME', 'Users')
    bucket_name = os.environ.get('BUCKET_NAME', 'your-bucket-name')
    region = boto3.session.Session().region_name or 'us-east-1'

    secrets_client = boto3.client('secretsmanager', region_name=region)
    s3_client = boto3.client('s3', region_name=region)

    try:
        # Step 1: Fetch the current secrets
        current = secrets_client.get_secret_value(SecretId=secret_name)
        secrets = json.loads(current['SecretString'])

        # Step 2: Backup current secrets to S3
        backup_filename = f"{uuid.uuid4().hex[:6]}_{secret_name}_backup.json"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=backup_filename,
            Body=json.dumps(secrets, indent=2).encode('utf-8')
        )
        print(f"Backup uploaded to s3://{bucket_name}/{backup_filename}")

        # Step 3: Rotate each user's password
        for email in secrets:
            secrets[email] = api_pull()

        # Step 4: Update the secret with new passwords
        secrets_client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(secrets)
        )
        print("Secrets updated successfully.")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Password rotation and backup completed."})
        }

    except ClientError as e:
        print(f"AWS Client error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

    except Exception as e:
        print(f"Unhandled error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
