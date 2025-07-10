'''DOCSTRING
this document fucks shit up
'''
import json
import uuid
import boto3
from botocore.exceptions import ClientError
import requests
# s3_client = boto3.client('s3')

# s3_resource = boto3.resource('s3')

# s3_resource.meta.client.generate_presigned_url()


# users = {
#     "alice@example.com": "password123",
#     "bob@example.com": "securePass456",
#     "carol@example.com": "qwerty789",
#     "dave@example.com": "letMeIn321",
#     "eve@example.com": "hunter2!",
#     "frank@example.com": "passWORD987",
#     "grace@example.com": "1234secure",
#     "heidi@example.com": "myp@ssw0rd",
#     "ivan@example.com": "adminAccess1",
#     "judy@example.com": "Pa$$w0rd2025"
# }


def create_bucket_name(bucket_prefix):
    ''' DOCSTRING'''
    # the bucket name must be 3-63 characters
    return f'{bucket_prefix}-{uuid.uuid4()}'


# print(create_bucket_name('test_name'))


def create_bucket(bucket_prefix):
    ''' DOCSTRING'''
    try:
        # generate a session in current region
        session = boto3.session.Session(profile_name='devops-trainee')
        current_region = session.region_name or 'us-east-2'  # fallback if None
        # Debug print added here
        print(f"Current region detected: {current_region!r}")
        s3_client = session.client("s3", region_name=current_region)
        # generates a bucket name using the prefix
        bucket_name = create_bucket_name(bucket_prefix)
        if current_region == 'us-east-1':
            bucket_response = s3_client.create_bucket(  # creates the bucket
                Bucket=bucket_name)
        else:
            bucket_response = s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': current_region})
        print(bucket_name, current_region)
        return bucket_name, bucket_response
    except ClientError as e:
        print(e)


# creates a randomly named file that we can use to upload to the bucket
def create_temp_file(size, file_name, file_content):
    ''' DOCSTRING'''
    # generates the name using uuid4 but only the first 0-6 characters
    random_file_name = '_'.join([str(uuid.uuid4().hex[:6]), file_name])
    with open(random_file_name, 'w', encoding='utf-8') as f:
        f.write(str(file_content) * size)
    return random_file_name


def s3_upload(file_path: str, bucket_name: str, object_name: str) -> None:
    ''' DOCSTRING'''
    try:
        session = boto3.session.Session(profile_name='devops-trainee')
        s3 = session.client('s3')
        # file_path = './bucket_names.txt'
        # bucket_name = 'firstpythonbucket-f9d567d1-46e0-4a5b-98bb-2b1e99cf4192'
        # object_name = 'first object'
        s3.upload_file(file_path, bucket_name, object_name)
    except ClientError as e:
        print(e)


def api_pull():
    '''Pulls info from the API into a json'''
    api_url = 'https://makemeapassword.ligos.net/api/v1/alphanumeric/json?c=1&l=12&sym=T'
    try:
        response = requests.get(api_url, timeout=10)  # added timeout
        response.raise_for_status()
        result = response.json()
        # if response.status_code == 200:
        # print(response.json())
        # print(result.get('pws'))
        return result.get('pws')
        # else:
        #     print(f'Failed to fetch. {response.status_code}')
        #     return None
    # except requests.exceptions.Timeout:
    #     print('Request timed out.')
    #     return None
    except requests.exceptions.RequestException as e:
        print(f'API request failed: {e}')
        raise e
        # return None


def get_secret():
    secret_name = "Users"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session(profile_name='devops-trainee')
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret_str = get_secret_value_response['SecretString']
    secret_dict = json.loads(secret_str)
    return secret_dict


def update_secret(secret_name, updated_dict):
    ''''*** DOCSTRING***'''
    session = boto3.session.Session(profile_name='devops-trainee')
    current_region = session.region_name or 'us-east-2'  # fallback if None
    client = session.client(service_name='secretsmanager',
                            region_name=current_region)
    try:
        response = client.put_secret_value(
            SecretId=secret_name,
            SecretString=json.dumps(updated_dict)
        )
        print('Secret Updated Successfully!')
        # print(f'Secret updated: {response}')
    except ClientError as e:
        print(f'Error! {e}')


# fix: this was incorrectly indented inside API_pull before
if __name__ == '__main__':
    #     create_bucket('firstpythonbucket')
    #     s3_upload('./bucket_names.txt',
    #               'firstpythonbucket-f9d567d1-46e0-4a5b-98bb-2b1e99cf4192',
    #               'first object')
    # new_pass = api_pull()
    # users['alice@example.com'] = new_pass
    # print(users)
    # get_secret()
    users = get_secret()
    json_data = json.dumps(users)
    temp_file_name = create_temp_file(
        size=1, file_name='users.json', file_content=json_data)
    bucket_name = 'firstpythonbucket-f9d567d1-46e0-4a5b-98bb-2b1e99cf4192'
    object_name = 'secrets/users.json'
    s3_upload(file_path=temp_file_name,
              bucket_name=bucket_name, object_name=object_name)

    for email in users:
        new_pass = api_pull()[0:9]
        users[email] = new_pass
    # print(f'\n ***UPDATED***\n{users}')
    update_secret("Users", users)
