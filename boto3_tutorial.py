import boto3
from botocore.exceptions import ClientError
from boto3.session import Session

def create_bucket():
    """ *** DOC STRING *** """
    try:
        session = Session()
        s3_client = session.client("s3", region_name="us-east-2")
        response = s3_client.create_bucket(Bucket='prankbucketanksandbox',
                                           CreateBucketConfiguration={
                              'LocationConstraint': 'us-east-2'})
        return response
    except ClientError as e:
        print(e)

def 

if __name__ == "__main__":

