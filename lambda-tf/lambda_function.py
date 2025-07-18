# Import required modules
import boto3  # AWS SDK for Python – used to interact with AWS services
import uuid  # Used to generate unique identifiers (for passwords)
import json  # Used for parsing and formatting JSON data
import os  # Used to read environment variables set in Lambda
import requests  # Add this with your other imports


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


# AWS Lambda entry point function
def lambda_handler(event, context):
    # --- Configuration ---

    # Get the name of the Secrets Manager secret from environment variable (or use default)
    secret_name = os.environ.get('SECRET_NAME', 'example/rotating-passwords')

    # Get the name of the S3 bucket from environment variable (or use placeholder default)
    bucket_name = os.environ.get('BUCKET_NAME', 'your-bucket-name')

    # Get the AWS region from environment variable (or default to 'us-east-1')
    region_name = boto3.Session().region_name

    # --- AWS Clients ---

    # Initialize the Secrets Manager client in the given region
    secrets_client = boto3.client('secretsmanager', region_name=region_name)

    # Initialize the S3 client in the same region
    s3_client = boto3.client('s3', region_name=region_name)

    try:
        # --- Retrieve existing secrets ---

        # Fetch the current secret from AWS Secrets Manager
        get_response = secrets_client.get_secret_value(SecretId=secret_name)

        # Parse the returned secret JSON string into a Python dictionary
        current_secrets = json.loads(get_response['SecretString'])

        # --- Rotate passwords (example logic) ---

        # Prepare a new dictionary to hold the rotated passwords
        updated_secrets = {}

        # Loop through each user in the existing secret
        for user, _ in current_secrets.items():
            # Generate a new password using UUID (take first 12 characters for simplicity)
            new_pass = api_pull()

            # Store the new password in the updated dictionary
            updated_secrets[user] = new_pass

        # --- Upload backup to S3 ---

        # Prepare a filename-safe version of the secret name for S3
        backup_filename = f"{secret_name.replace('/', '_')}_backup.json"

        # Upload the current (pre-rotation) secret as a backup to S3
        s3_client.put_object(
            Bucket=bucket_name,  # S3 bucket name
            Key=backup_filename,  # S3 object key (filename)
            Body=json.dumps(current_secrets, indent=2).encode('utf-8')  # Upload as JSON-encoded bytes
        )

        # --- Update the secret in Secrets Manager ---

        # Replace the original secret with the newly rotated passwords
        secrets_client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(updated_secrets)  # Convert the updated secrets back to a JSON string
        )

        # Return a success response to the caller
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Passwords rotated and backed up successfully.'})
        }

    except Exception as e:
        # If any error occurs, catch it and return an error response with the message
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
