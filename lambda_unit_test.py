import json
import os
import pytest
import boto3
from moto import mock_aws

# Dummy AWS credentials for Moto
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

from password_rotator import (
    get_secret,
    update_secret,
    create_temp_file,
    s3_upload,
    api_pull,
)

@pytest.fixture
def aws_setup():
    """Mocks AWS Secrets Manager and S3 using Moto.

    Yields:
        boto3.Session: A mocked boto3 session with configured AWS clients for testing.
    """
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

def test_get_secret(aws_setup):
    """Tests that get_secret() returns a dictionary containing expected data.

    Args:
        aws_setup (boto3.Session): Mocked session with a Secrets Manager client.

    Asserts:
        bool: The returned secret is a dictionary.
        bool: The dictionary contains the key 'alice@example.com'.
    """
    secret = get_secret(session=aws_setup)
    assert isinstance(secret, dict)
    assert 'alice@example.com' in secret

def test_update_secret(aws_setup):
    """Tests that update_secret() correctly overwrites the secret value.

    Args:
        aws_setup (boto3.Session): Mocked session with a Secrets Manager client.

    Asserts:
        bool: The updated secret reflects the new password for 'alice@example.com'.
    """
    new_data = {'alice@example.com': 'newpass1', 'bob@example.com': 'newpass2'}
    update_secret('Users', new_data, session=aws_setup)
    client = aws_setup.client('secretsmanager')
    updated = client.get_secret_value(SecretId='Users')['SecretString']
    assert json.loads(updated)['alice@example.com'] == 'newpass1'

def test_create_temp_file_creates_file():
    """Tests that create_temp_file() writes the correct content to disk.

    Asserts:
        bool: The file contains the exact JSON string passed to it.
    """
    content = json.dumps({'user': 'pass'})
    filename = create_temp_file(1, 'testfile.json', content)
    with open(filename, 'r', encoding='utf-8') as f:
        assert content in f.read()

def test_s3_upload_and_read_back(aws_setup):
    """Tests that s3_upload() successfully stores and retrieves a file.

    Args:
        aws_setup (boto3.Session): Mocked session with an S3 client.

    Asserts:
        bool: The file content retrieved from S3 matches the uploaded content.
    """
    content = json.dumps({'foo': 'bar'})
    file_path = create_temp_file(1, 'foo.json', content)
    s3_upload(file_path, 'test-bucket', 'backups/foo.json', session=aws_setup)
    result = aws_setup.client('s3').get_object(Bucket='test-bucket', Key='backups/foo.json')
    assert content in result['Body'].read().decode('utf-8')

def test_api_pull_returns_password():
    """Tests that api_pull() returns a valid password string.

    Asserts:
        bool: The returned value is a string.
        bool: The string is at least 8 characters long.
    """
    result = api_pull()
    assert isinstance(result, str)
    assert len(result) >= 8
