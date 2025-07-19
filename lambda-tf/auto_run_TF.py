import os
import subprocess
import json
import boto3
from moto.stepfunctions.parser.asl.component.intrinsic.functionname.function_name import FunctionName

os.environ['AWS_PROFILE'] = 'devops-trainee'


# os.environ["AWS_ACCESS_KEY_ID"] = "your-access-key"
# os.environ["AWS_SECRET_ACCESS_KEY"] = "your-secret-key"
# os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


def run_terraform():
    try:
        # Initialize Terraform
        subprocess.run(["terraform", "init"], check=True)

        # (Optional) Review the execution plan
        subprocess.run(["terraform", "plan"], check=True)

        # Apply the Terraform plan automatically (auto-approve avoids prompt)
        subprocess.run(["terraform", "apply", "-auto-approve"], check=True)

        print("Terraform deployment successful.")
    except subprocess.CalledProcessError as e:
        print(f"Terraform failed with error: {e}")
        exit(1)


def invoke_lambda():
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        response = lambda_client.invoke(
            FunctionName='THETerraformLambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({})
        )
        payload = response['Payload'].read()
        print(f'Lambda invoked succesfully!: {payload.decode()}')
    except Exception as e:
        print(f'***FAILED***: {e}')


if __name__ == "__main__":
    run_terraform()
    invoke_lambda()
