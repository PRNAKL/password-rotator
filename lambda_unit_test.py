"""Unit tests for the password rotation system.

Tests include:
- AWS Secrets Manager integration
- S3 uploads
- Temporary file handling
- External password API usage
"""

# pylint: disable=duplicate-code, redefined-outer-name

import json
import os

import pytest
import boto3
from moto import mock_aws

from password_rotator import (
    get_secret,
    update_secret,
    create_temp_file,
    s3_upload,
    api_pull,
)

# Dummy AWS credentials for Moto (used for mocking AWS services)
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def mock_aws_session():
    """
    Mocks AWS Secrets Manager and S3 using Moto.

    Yields:
        boto3.Session: A mocked boto3 session with configured AWS clients.
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


def test_get_secret(mock_aws_session):
    """Tests that get_secret() returns the expected data."""
    secret = get_secret(session=mock_aws_session)
    assert isinstance(secret, dict)
    assert 'alice@example.com' in secret


def test_update_secret(mock_aws_session):
    """Tests that update_secret() properly modifies the secret value."""
    new_data = {'alice@example.com': 'newpass1', 'bob@example.com': 'newpass2'}
    update_secret('Users', new_data, session=mock_aws_session)
    client = mock_aws_session.client('secretsmanager')
    updated = client.get_secret_value(SecretId='Users')['SecretString']
    assert json.loads(updated)['alice@example.com'] == 'newpass1'


def test_create_temp_file_creates_file():
    """Tests that create_temp_file() writes content to disk properly."""
    content = json.dumps({'user': 'pass'})
    filename = create_temp_file(1, 'testfile.json', content)
    with open(filename, 'r', encoding='utf-8') as f:
        assert content in f.read()


def test_s3_upload_and_read_back(mock_aws_session):
    """Tests that s3_upload() stores and retrieves a file correctly."""
    content = json.dumps({'foo': 'bar'})
    file_path = create_temp_file(1, 'foo.json', content)
    s3_upload(file_path, 'test-bucket', 'backups/foo.json', session=mock_aws_session)
    result = mock_aws_session.client('s3').get_object(Bucket='test-bucket', Key='backups/foo.json')
    assert content in result['Body'].read().decode('utf-8')


def test_api_pull_returns_password():
    """Tests that api_pull() returns a valid string password."""
    result = api_pull()
    assert isinstance(result, str)
    assert len(result) >= 8
