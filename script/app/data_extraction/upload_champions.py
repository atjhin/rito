import boto3
import os
from dotenv import load_dotenv
from fandom_scrape import scrape_all_champions
import re
from typing import Dict

load_dotenv(".env")
# === Configuration ===
S3_BUCKET = os.environ.get("S3_BUCKET_NAME")
S3_REGION = os.environ.get("S3_REGION")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")

def clean_name(name: str) -> str:
    """Remove suffix '(Character)' and replace spaces with underscores."""
    return re.sub(r"\s*\(Character\)$", "", name).replace(" ", "_")

def save_new_champion_to_s3(char_info: Dict, client: boto3.client("s3"), bucket=S3_BUCKET):
    champ_name = clean_name(char_info["name"])
    base_prefix = f"{champ_name}/"

    # Background (start at counter 1)
    bg_key = f"{base_prefix}background/1.txt"
    client.put_object(Bucket=bucket, Key=bg_key, Body=char_info.get("background", ""))

    counter_key = f"{base_prefix}bg_counter.txt"
    client.put_object(Bucket=bucket, Key=counter_key, Body="1")

    # URL
    url_key = f"{base_prefix}url.txt"
    client.put_object(Bucket=bucket, Key=url_key, Body=char_info.get("url", ""))

    # Personality
    pers_key = f"{base_prefix}personality.txt"
    client.put_object(Bucket=bucket, Key=pers_key, Body=char_info.get("personality", ""))

    # Appearance
    app_key = f"{base_prefix}appearance.txt"
    client.put_object(Bucket=bucket, Key=app_key, Body=char_info.get("appearance", ""))

    print(f"Uploaded new champion: {champ_name}")

def check_champion_exists(client: boto3.client("s3"), champ_name: str, bucket=S3_BUCKET) -> bool:
    """Check if a champion folder already exists in the S3 bucket."""
    prefix = f"{clean_name(champ_name)}/"
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1)
    return 'Contents' in response

if __name__ == "__main__":

    client = boto3.client(
    "s3",
    region_name=S3_REGION,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    )

    data = scrape_all_champions()

    for char in data:
        if not check_champion_exists(client, char["name"], S3_BUCKET):
            save_new_champion_to_s3(char, client, S3_BUCKET)
        else:
            print(f"Champion {char['name']} already exists in S3. Skipping upload.")
            continue
        