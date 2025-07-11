"""Test suite for the password_rotator utility functions.

This module uses pytest and moto to:
- Mock AWS Secrets Manager and S3 services
- Verify secret retrieval and updates
- Test temp file creation
- Test password API
- Simulate full secret backup and rotation process
"""

import json
import pytest
import boto3
from moto import mock_secretsmanager, mock_s3

from password_rotator import (
    get_secret,
    update_secret,
    create_temp_file,
    s3_upload,
    api_pull,
)


@pytest.fixture
def aws_setup():
    """Mock AWS Secrets Manager and S3 for isolated tests.

    This fixture:
    - Creates a fake Secrets Manager with a secret named 'Users'
    - Creates a fake S3 bucket named 'test-bucket'
    """
    with mock_secretsmanager(), mock_s3():
        secrets = boto3.client("secretsmanager", region_name="us-east-1")
        secrets.create_secret(
            Name="Users",
            SecretString=json.dumps({
                "alice@example.com": "oldpass1",
                "bob@example.com": "oldpass2"
            })
        )

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-bucket")

        yield


def test_get_secret(aws_setup):
    """Test that `get_secret()` returns a valid user dictionary."""
    secret = get_secret()
    assert isinstance(secret, dict)
    assert "alice@example.com" in secret


def test_update_secret(aws_setup):
    """Test that `update_secret()` correctly updates the Users secret."""
    new_data = {
        "alice@example.com": "newpass1",
        "bob@example.com": "newpass2"
    }
    update_secret("Users", new_data)

    client = boto3.client("secretsmanager", region_name="us-east-1")
    updated = json.loads(client.get_secret_value(
        SecretId="Users")["SecretString"])
    assert updated["alice@example.com"] == "newpass1"


def test_create_temp_file_creates_file():
    """Test that `create_temp_file()` generates a file with expected contents."""
    content = json.dumps({"user": "pass"})
    filename = create_temp_file(1, "testfile.json", content)

    with open(filename, "r", encoding="utf-8") as f:
        contents = f.read()
        assert content in contents


def test_s3_upload_and_read_back(aws_setup):
    """Test that a file can be uploaded and read back from mock S3."""
    content = json.dumps({"foo": "bar"})
    file_path = create_temp_file(1, "foo.json", content)

    s3_upload(file_path, "test-bucket", "backups/foo.json")

    s3 = boto3.client("s3", region_name="us-east-1")
    result = s3.get_object(Bucket="test-bucket", Key="backups/foo.json")
    result_content = result["Body"].read().decode("utf-8")

    assert content in result_content


def test_api_pull_returns_password():
    """Test that `api_pull()` returns a password string from the external API."""
    result = api_pull()
    assert isinstance(result, str)
    assert len(result) >= 8


def rotate_and_backup_users(bucket_name: str, object_name: str) -> None:
    """Back up current secrets to S3 and rotate user passwords.

    Args:
        bucket_name: Name of the S3 bucket to upload to.
        object_name: S3 object key under which to store the backup.
    """
    users = get_secret()
    json_data = json.dumps(users)
    temp_file_name = create_temp_file(
        size=1, file_name='users.json', file_content=json_data)

    s3_upload(file_path=temp_file_name,
              bucket_name=bucket_name, object_name=object_name)

    for email in users:
        new_pass = api_pull()
        users[email] = new_pass

    update_secret("Users", users)


if __name__ == '__main__':
    rotate_and_backup_users(
        'firstpythonbucket-f9d567d1-46e0-4a5b-98bb-2b1e99cf4192',
        'secrets/users.json'
    )
