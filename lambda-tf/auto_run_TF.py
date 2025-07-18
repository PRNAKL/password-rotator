import os
import subprocess

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


if __name__ == "__main__":
    run_terraform()
