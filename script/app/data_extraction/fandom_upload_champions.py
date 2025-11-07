import boto3
import os
from dotenv import load_dotenv
from fandom_scrape import scrape_all_champions
import re
from datetime import datetime
from typing import Dict

load_dotenv()
# === Configuration ===
S3_BUCKET = os.environ.get("S3_BUCKET_NAME")
S3_REGION = os.environ.get("S3_REGION")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")

def clean_name(name: str) -> str:
    """Remove suffix '(Character)' and replace spaces with underscores."""
    return re.sub(r"\s*\(Character\)$", "", name).replace(" ", "_")

def save_new_champion_to_s3(base_dir: str, char_info: Dict, client: boto3.client("s3"), bucket=S3_BUCKET):
    champ_name = clean_name(char_info["name"])
    base_prefix = f"{base_dir}/{champ_name}/"

    date_str = datetime.now().strftime("%Y%m%d")

    bg_key = f"{base_prefix}background/{date_str}.txt"
    client.put_object(Bucket=bucket, Key=bg_key, Body=char_info.get("background", ""))

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

def update_champion_background_in_s3(base_dir: str, champ_name: str, new_background: str, max_version: int, client: boto3.client("s3"), bucket=S3_BUCKET):
    champ_name_clean = clean_name(champ_name)
    base_prefix = f"{base_dir}/{champ_name_clean}/background/"

    # check the numer of existing versions
    response = client.list_objects_v2(Bucket=bucket, Prefix=base_prefix)
    existing_versions = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.txt')]
    if len(existing_versions) >= max_version:
        print(f"Max version reached for {champ_name_clean}. Skipping update.")
        # remove the oldest version
        oldest_version = sorted(existing_versions)[0]
        client.delete_object(Bucket=bucket, Key=oldest_version)
        print(f"Removed oldest version: {oldest_version}")
    else:
        print(f"Current versions for {champ_name_clean}: {len(existing_versions)}")

    # Today's date for versioning
    date_str = datetime.now().strftime("%Y%m%d")

    # Upload new background version
    bg_key = f"{base_prefix}{date_str}.txt"
    client.put_object(Bucket=bucket, Key=bg_key, Body=new_background)
    print(f"Updated background for champion: {champ_name_clean}")




def check_champion_exists(client: boto3.client("s3"), base_dir: str, champ_name: str, bucket=S3_BUCKET) -> bool:
    """Check if a champion folder already exists in the S3 bucket."""
    prefix = f"{base_dir}/{clean_name(champ_name)}/"
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
    base_directory = "champions_fandom"
    for char in data:
        if not check_champion_exists(client, base_directory, char["name"], S3_BUCKET):
            # Add new champion
            save_new_champion_to_s3(base_directory, char, client, S3_BUCKET)
            print(f"Saved new champion {char['name']} to S3.")
        else:
            # Example: update background with max 3 versions
            new_background = char.get("background", "").strip()
            if new_background and new_background != "":
                update_champion_background_in_s3(base_directory, char["name"], new_background, max_version=3, client=client, bucket=S3_BUCKET)
            else:
                print(f"No new background to update for {char['name']}.")
