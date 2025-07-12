"""Test suite for the password_rotator utility functions.

This module tests utility functions used in password rotation and backup.
It includes:
- Mocking of AWS Secrets Manager and S3 using moto
- Testing of secret retrieval and updates
- Temporary file creation validation
- S3 upload functionality
- Password generation via external API
- Full secret backup and password rotation workflow
"""

import json
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


@pytest.fixture
def aws_setup():
    """Mock AWS Secrets Manager and S3 for isolated tests.

    This fixture:
    - Creates a mock Secrets Manager client with a secret named 'Users'
    - Creates a mock S3 bucket named 'test-bucket'

    Yields:
        None: Used for pytest fixture execution.
    """
    with mock_aws():
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
    """Test that get_secret() returns a valid dictionary.

    Args:
        aws_setup (fixture): Sets up mocked AWS Secrets Manager.

    Asserts:
        - Return type is a dict.
        - Contains expected keys.
    """
    secret = get_secret()
    assert isinstance(secret, dict)
    assert "alice@example.com" in secret


def test_update_secret(aws_setup):
    """Test that update_secret() properly updates the stored secret.

    Args:
        aws_setup (fixture): Sets up mocked AWS Secrets Manager.

    Asserts:
        - Secret data is updated in mock Secrets Manager.
    """
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
    """Test that create_temp_file() creates a file with the correct content.

    Asserts:
        - The created file contains the expected JSON string.
    """
    content = json.dumps({"user": "pass"})
    filename = create_temp_file(1, "testfile.json", content)

    with open(filename, "r", encoding="utf-8") as f:
        contents = f.read()
        assert content in contents


def test_s3_upload_and_read_back(aws_setup):
    """Test uploading and reading a file to/from mocked S3.

    Args:
        aws_setup (fixture): Sets up mocked AWS Secrets Manager and S3.

    Asserts:
        - The uploaded content is correctly stored in mock S3.
    """
    content = json.dumps({"foo": "bar"})
    file_path = create_temp_file(1, "foo.json", content)

    s3_upload(file_path, "test-bucket", "backups/foo.json")

    s3 = boto3.client("s3", region_name="us-east-1")
    result = s3.get_object(Bucket="test-bucket", Key="backups/foo.json")
    result_content = result["Body"].read().decode("utf-8")

    assert content in result_content


def test_api_pull_returns_password():
    """Test that api_pull() returns a valid password string.

    Asserts:
        - Return type is str.
        - Length is at least 8 characters.
    """
    result = api_pull()
    assert isinstance(result, str)
    assert len(result) >= 8


def rotate_and_backup_users(bucket_name: str, object_name: str) -> None:
    """Backs up current secrets to S3 and rotates user passwords.

    Args:
        bucket_name (str): The name of the S3 bucket to upload to.
        object_name (str): The S3 object key under which to store the backup.

    Returns:
        None
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
