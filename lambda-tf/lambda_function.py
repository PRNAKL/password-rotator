import boto3
import json
import os
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


def lambda_handler(event, context):
    """
    AWS Lambda function entry point.

    Retrieves the 'Users' secret from AWS Secrets Manager, backs it up to S3,
    generates new passwords using the makemeapassword API, and updates the secret.

    Environment Variables:
        SECRET_NAME (str): Name of the secret in Secrets Manager.
        BUCKET_NAME (str): Name of the S3 bucket where the backup will be stored.

    Args:
        event (dict): AWS Lambda event input (not used).
        context (LambdaContext): AWS Lambda runtime information (not used).

    Returns:
        dict: HTTP-style response with status code and message.
    """
    secret_name = os.environ.get('SECRET_NAME', 'Users')
    bucket_name = os.environ.get('BUCKET_NAME', 'your-bucket-name')
    region_name = boto3.Session().region_name

    secrets_client = boto3.client('secretsmanager', region_name=region_name)
    s3_client = boto3.client('s3', region_name=region_name)

    try:
        # Retrieve current secrets
        get_response = secrets_client.get_secret_value(SecretId=secret_name)
        secrets = json.loads(get_response['SecretString'])

        # Backup current secrets to S3
        backup_filename = f"{secret_name.replace('/', '_')}_backup.json"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=backup_filename,
            Body=json.dumps(secrets, indent=2).encode('utf-8')
        )

        # Rotate passwords using the external API
        for user in secrets:
            secrets[user] = api_pull()

        # Update the secret in Secrets Manager
        secrets_client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(secrets)
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Password rotation and backup successful.'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
