import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os
from dotenv import load_dotenv

load_dotenv()

def get_champs_and_models_txt(save_path: str):

    bucket = os.getenv("S3_BUCKET")

    assert bucket is not None, "S3_BUCKET environment variable not set."

    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        region_name=os.getenv("S3_REGION")
    )

    try: 
        list_of_champions = s3.list_objects_v2(Bucket=bucket, Prefix="champions_fandom/", Delimiter='/')
        champ_names = [obj['Prefix'].split('/')[1].replace('_', ' ') for obj in list_of_champions.get('CommonPrefixes', [])]

    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Error fetching champions: {e}")

    os.makedirs(save_path, exist_ok=True)
    with open(os.path.join(save_path, "champions.txt"), "w") as f:
        f.write("\n".join(champ_names))