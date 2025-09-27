import boto3
import requests
import json
import os
from datetime import datetime


# === Configuration ===
S3_BUCKET = os.environ.get("S3_BUCKET_NAME")
S3_REGION = os.environ.get("S3_REGION")


# Today's date (used for folder prefix)
today = datetime.today().strftime("%Y-%m-%d")
folder_prefix = f"raw/{today}/"  # e.g., raw/2025-09-27/

# Data Dragon version
versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
versions = requests.get(versions_url).json()
latest_version = versions[0]

# List of champions to save
champion_list_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json"
champions_data = requests.get(champion_list_url).json()

# Extract all champion names
champion_names = list(champions_data['data'].keys())
print(champion_names)
champion_list = champion_names[:10]  # or your full list

# === Initialize S3 client ===
s3 = boto3.client("s3",
                  region_name=S3_REGION,
                  aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                  aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))


# === Function to read all champion lore JSONs from S3 ===
def read_champion_lore_from_s3(bucket, prefix):
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    if "Contents" not in response:
        print("No objects found in S3 for prefix:", prefix)
        return

    for obj in response["Contents"]:
        key = obj["Key"]
        obj_data = s3.get_object(Bucket=bucket, Key=key)
        content = obj_data["Body"].read().decode("utf-8")
        champ_json = json.loads(content)
        print(f"Champion: {champ_json['name']}, Lore length: {len(champ_json['lore'])}")

# === Example usage ===
read_champion_lore_from_s3(S3_BUCKET, folder_prefix)
