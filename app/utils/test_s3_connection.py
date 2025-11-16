"""Utility to test AWS S3 connection using environment variables."""
import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError

def load_env():
    """Load environment variables from the appropriate .env file."""
    env = os.getenv("ENV", "development")
    env_file = ".env.production" if env == "production" else ".env.development"

    if not os.path.exists(env_file):
        raise FileNotFoundError("Environment file not found: " + env_file)

    load_dotenv(env_file)
    print(f"Variables loaded from '{env_file}'.")

def get_s3_client():
    """Initialize the S3 client using environment credentials."""
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION")
    bucket_name = os.getenv("S3_BUCKET_NAME")

    if access_key and secret_key and region:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        print("S3 client initialized with .env credentials.")
    elif not access_key and not secret_key and region:
        s3_client = boto3.client(
            's3',
            region_name=region
        )
        print("S3 client initialized with IAM role.")
    if not access_key or not secret_key:
        raise ValueError("S3 client initialization failed due to missing AWS credentials.")

    return s3_client, bucket_name

def check_s3_connection():
    """Test if the configured bucket is accessible with the current credentials."""
    try:
        load_env()
        s3_client, bucket_name = get_s3_client()

        print("\nChecking bucket access...")
        s3_client.head_bucket(Bucket=bucket_name)

        print(f"Successful connection! Access to bucket '{bucket_name}' is confirmed.")
        return True

    except NoCredentialsError:
        print("No AWS credentials found.")
        return False

    except ClientError as e:
        code = e.response["Error"]["Code"]

        if code == "403":
            print("Valid credentials, but no permission to access the bucket.")
        elif code == "404":
            print(f"The bucket '{bucket_name}' does not exist.")
        elif code == "400":
            correct_region = e.response["ResponseMetadata"]["HTTPHeaders"].get(
                "x-amz-bucket-region", "unknown"
            )
            print(f"Incorrect region. The bucket is in: {correct_region}.")
        else:
            print(f"Unknown error: {e}")
        return False

    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Starting AWS S3 connection test...\n")
    success = check_s3_connection()

    if success:
        print("\nEverything is set to use S3 in your project.")
    else:
        print("\nS3 connection failed. Check permissions or configuration.")
