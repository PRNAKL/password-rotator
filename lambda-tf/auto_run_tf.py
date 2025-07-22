"""Automates deployment and execution of a Lambda function via Terraform.

This script:
1. Initializes, plans, and applies Terraform configuration.
2. Invokes the deployed Lambda function after successful deployment.
"""

import subprocess
import sys
import json
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def run_terraform():
    """
    Run Terraform init, plan, and apply commands in sequence.
    Exits the script if any step fails.
    """
    try:
        logger.info("Initializing Terraform...")
        subprocess.run(["terraform", "init"], check=True)

        logger.info("Planning Terraform changes...")
        subprocess.run(["terraform", "plan"], check=True)

        logger.info("Applying Terraform plan...")
        subprocess.run(["terraform", "apply", "-auto-approve"], check=True)

        logger.info("Terraform deployment successful.")

    except subprocess.CalledProcessError as e:
        logger.error("Terraform failed with error: %s", e)
        sys.exit(1)


def invoke_lambda():
    """
    Invoke the deployed Lambda function called 'THETerraformLambda'.
    """
    try:
        logger.info("Invoking Lambda function 'THETerraformLambda'...")
        lambda_client = boto3.client("lambda", region_name="us-east-1")
        response = lambda_client.invoke(
            FunctionName="THETerraformLambda",
            InvocationType="RequestResponse",
            Payload=json.dumps({})
        )
        payload = response["Payload"].read()
        logger.info("Lambda invoked successfully. Response payload: %s", payload.decode())

    except (ClientError, BotoCoreError) as e:
        logger.error("AWS client error invoking Lambda: %s", e)
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error("Failed to decode Lambda response payload: %s", e)
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Unexpected error invoking Lambda: %s", e)
        sys.exit(1)
if __name__ == "__main__":
    run_terraform()
    invoke_lambda()
