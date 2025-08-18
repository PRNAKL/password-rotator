"""Unit tests for the password rotation system.

Tests include:
- AWS Secrets Manager integration
- S3 uploads
- Temporary file handling
- External password API usage
"""
# pylint: disable=redefined-outer-name
import json
import os
import uuid

import boto3
import pytest
import requests
from moto import mock_aws
from botocore.exceptions import ClientError

from logger import Logger

# Dummy AWS credentials for Moto (used for mocking AWS services)
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

logger = Logger()

def api_pull():
    """Pull a randomly generated password from the external API."""
    api_url = (
        "https://makemeapassword.ligos.net/api/v1/alphanumeric/json?c=1&l=12&sym=T"
    )
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get("pws")[0]
    except requests.exceptions.RequestException as e:
        logger.log_message(40, f"API request failed: {e}")
        raise


def get_secret(session=None):
    """Retrieve the current 'Users' secret from AWS Secrets Manager."""
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
    """Update a given secret in AWS Secrets Manager with new data."""
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
    """Create a temporary local file with a randomized prefix."""
    random_file_name = f"{uuid.uuid4().hex[:6]}_{file_name}"
    with open(random_file_name, "w", encoding="utf-8") as f:
        f.write(str(file_content) * size)
    return random_file_name


def s3_upload(file_path, bucket_name, object_name, session=None):
    """Upload a local file to a specified AWS S3 bucket and object key."""
    if session is None:
        session = boto3.session.Session()
    s3 = session.client("s3")

    try:
        s3.upload_file(file_path, bucket_name, object_name)
        logger.log_message(
            20,
            f"Uploaded {file_path} to s3://{bucket_name}/{object_name}"
        )
    except ClientError as e:
        logger.log_message(40, f"Error uploading to S3: {e}")
        raise


@pytest.fixture
def mock_aws_session():
    """Mimics AWS Secrets Manager and S3 using Moto."""
    with mock_aws():
        session = boto3.Session(region_name='us-east-1')
        secrets = session.client('secretsmanager')
        secrets.create_secret(
            Name='Users',
            SecretString=json.dumps({
                'alice@example.com': 'oldpass1',
                'bob@example.com': 'oldpass2'
            })
        )
        session.client('s3').create_bucket(Bucket='test-bucket')
        yield session


def test_get_secret(mock_aws_session):
    """Tests that get_secret() returns the expected data."""
    logger.log_message(20, "Running test_get_secret")
    secret = get_secret(session=mock_aws_session)
    assert isinstance(secret, dict)
    assert 'alice@example.com' in secret


def test_update_secret(mock_aws_session):
    """Tests that update_secret() properly modifies the secret value."""
    logger.log_message(20, "Running test_update_secret")
    new_data = {
        'alice@example.com': 'newpass1',
        'bob@example.com': 'newpass2'
    }
    update_secret('Users', new_data, session=mock_aws_session)
    client = mock_aws_session.client('secretsmanager')
    updated = client.get_secret_value(SecretId='Users')['SecretString']
    assert json.loads(updated)['alice@example.com'] == 'newpass1'


def test_create_temp_file_creates_file():
    """Tests that create_temp_file() writes content to disk properly."""
    logger.log_message(20, "Running test_create_temp_file_creates_file")
    content = json.dumps({'user': 'pass'})
    filename = create_temp_file(1, 'testfile.json', content)
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            assert content in f.read()
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def test_s3_upload_and_read_back(mock_aws_session):
    """Tests that s3_upload() stores and retrieves a file correctly."""
    logger.log_message(
        20,
        "Running test_s3_upload_and_read_back")
    content = json.dumps({'foo': 'bar'})
    file_path = create_temp_file(1, 'foo.json', content)
    try:
        s3_upload(
            file_path,
            'test-bucket',
            'backups/foo.json',
            session=mock_aws_session
        )
        result = mock_aws_session.client('s3').get_object(
            Bucket='test-bucket',
            Key='backups/foo.json'
        )
        assert content in result['Body'].read().decode('utf-8')
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def test_api_pull_returns_password():
    """Tests that api_pull() returns a valid string password."""
    logger.log_message(20, "Running test_api_pull_returns_password")
    result = api_pull()
    assert isinstance(result, str)
    assert len(result) >= 8
