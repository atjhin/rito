import os
from dotenv import load_dotenv
import boto3

# get working directory

load_dotenv()
# === Configuration ===
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_REGION = os.environ.get("S3_REGION")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")

assert S3_BUCKET is not None, "S3_BUCKET environment variable is not set."
assert S3_REGION is not None, "S3_REGION environment variable is not set."
assert S3_ACCESS_KEY is not None, "S3_ACCESS_KEY environment variable is not set."
assert S3_SECRET_KEY is not None, "S3_SECRET_KEY environment variable is not set."

base_dir = os.path.dirname(__file__)

def upload_sample_fanfiction_to_s3():
    client = boto3.client(
        "s3",
        region_name=S3_REGION,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
    )
    
    sample_fanfictions_dir = os.path.join(base_dir, "sample_fanfictions")
    
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(sample_fanfictions_dir):
        for filename in files:
            if filename.endswith(".txt"):
                file_path = os.path.join(root, filename)
                
                # Get the relative path from sample_fanfictions_dir
                relative_path = os.path.relpath(file_path, sample_fanfictions_dir)
                
                # Convert Windows backslashes to forward slashes for S3
                s3_key = f"sample_fanfictions/{relative_path}".replace("\\", "/")
                
                # Use upload_file instead of put_object for better performance
                client.upload_file(file_path, S3_BUCKET, s3_key)
                
                print(f"Uploaded {relative_path} to S3 bucket {S3_BUCKET} with key {s3_key}")

if __name__ == "__main__":
    upload_sample_fanfiction_to_s3()