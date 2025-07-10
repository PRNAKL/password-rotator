import json
import boto3
from botocore.exceptions import ClientError
import requests


def api_pull():
    """Pulls a list of passwords from the API into a JSON format"""
    api_url = 'https://makemeapassword.ligos.net/api/v1/alphanumeric/json?c=1&l=12&sym=T'
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get('pws')
    except requests.exceptions.RequestException as e:
        print(f'API request failed: {e}')
        raise e


def get_secret():
    """Retrieves the current 'Users' secret from AWS Secrets Manager"""
    secret_name = "Users"
    region_name = "us-east-1"

    session = boto3.session.Session(profile_name='devops-trainee')
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name)
        secret_str = get_secret_value_response['SecretString']
        return json.loads(secret_str)
    except ClientError as e:
        raise e


def update_secret(secret_name, updated_dict):
    """Updates the specified secret with a new user-password dictionary"""
    session = boto3.session.Session(profile_name='devops-trainee')
    current_region = session.region_name or 'us-east-2'
    client = session.client(service_name='secretsmanager',
                            region_name=current_region)

    try:
        # response =
        client.put_secret_value(
            SecretId=secret_name,
            SecretString=json.dumps(updated_dict)
        )
        print('Secret updated successfully!')
        # print(response)
    except ClientError as e:
        print(f'Error! {e}')


if __name__ == '__main__':
    """Rotates all passwords in the Users secret using the API"""
    users = get_secret()
    for email in users:
        new_pass = api_pull()[0]  # Pulls first password from list
        users[email] = new_pass
    update_secret("Users", users)
