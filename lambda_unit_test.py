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
    """Mock AWS Secrets Manager and S3 using Moto."""
    with mock_aws():
        # Optionally you can omit profile_name to avoid profile lookup
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
    """
    Test that get_secret() returns a valid dictionary.

    Args:
        aws_setup (boto3.Session): A mocked boto3 session with Secrets Manager configured.

    Asserts:
        - The returned value is a dictionary.
        - The dictionary contains the key 'alice@example.com'.
    """
    secret = get_secret(session=aws_setup)
    assert isinstance(secret, dict)
    assert 'alice@example.com' in secret

def test_update_secret(aws_setup):
    """
    Test that update_secret() properly updates the stored secret.

    Args:
        aws_setup (boto3.Session): A mocked boto3 session with Secrets Manager configured.

    Asserts:
        - The updated secret contains the new password for 'alice@example.com'.
    """
    new_data = {'alice@example.com': 'newpass1', 'bob@example.com': 'newpass2'}
    update_secret('Users', new_data, session=aws_setup)
    client = aws_setup.client('secretsmanager')
    updated = client.get_secret_value(SecretId='Users')['SecretString']
    assert json.loads(updated)['alice@example.com'] == 'newpass1'

def test_create_temp_file_creates_file():
    """
    Test that create_temp_file() writes the correct JSON content to a file.

    Asserts:
        - The file content matches the JSON string provided.
    """
    content = json.dumps({'user': 'pass'})
    filename = create_temp_file(1, 'testfile.json', content)
    with open(filename, 'r', encoding='utf-8') as f:
        assert content in f.read()

def test_s3_upload_and_read_back(aws_setup):
    """
    Test uploading a file to S3 and reading it back from the mock bucket.

    Args:
        aws_setup (boto3.Session): A mocked boto3 session with S3 configured.

    Asserts:
        - The content uploaded to S3 is retrievable and matches the original.
    """
    content = json.dumps({'foo': 'bar'})
    file_path = create_temp_file(1, 'foo.json', content)
    s3_upload(file_path, 'test-bucket', 'backups/foo.json', session=aws_setup)
    result = aws_setup.client('s3').get_object(Bucket='test-bucket', Key='backups/foo.json')
    assert content in result['Body'].read().decode('utf-8')

def test_api_pull_returns_password():
    """
    Test that api_pull() returns a valid password string.

    Asserts:
        - The returned password is a string.
        - The length of the password is at least 8 characters.
    """
    result = api_pull()
    assert isinstance(result, str)
    assert len(result) >= 8