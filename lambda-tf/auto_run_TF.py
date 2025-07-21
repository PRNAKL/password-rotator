import os
import subprocess
import json
import boto3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more detailed logs
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

os.environ['AWS_PROFILE'] = 'devops-trainee'

# os.environ["AWS_ACCESS_KEY_ID"] = "your-access-key"
# os.environ["AWS_SECRET_ACCESS_KEY"] = "your-secret-key"
# os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


def run_terraform():
    try:
        logging.info("Initializing Terraform...")
        subprocess.run(["terraform", "init"], check=True)

        logging.info("Planning Terraform changes...")
        subprocess.run(["terraform", "plan"], check=True)

        logging.info("Applying Terraform plan...")
        subprocess.run(["terraform", "apply", "-auto-approve"], check=True)

        logging.info("Terraform deployment successful.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Terraform failed with error: {e}")
        exit(1)


def invoke_lambda():
    try:
        logging.info("Invoking Lambda function 'THETerraformLambda'...")
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        response = lambda_client.invoke(
            FunctionName='THETerraformLambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({})
        )
        payload = response['Payload'].read()
        logging.info(f"Lambda invoked successfully! Response payload: {payload.decode()}")
    except Exception as e:
        logging.error(f"Failed to invoke Lambda: {e}")


if __name__ == "__main__":
    run_terraform()
    invoke_lambda()
