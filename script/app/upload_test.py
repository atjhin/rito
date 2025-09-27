import boto3
import requests
import json
import io
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


# === Function to upload only champion lore to S3 ===
def upload_champion_lore(champion_name):
    url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion/{champion_name}.json"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {champion_name}: {response.status_code}")
        return

    data = response.json()["data"][champion_name]  # champion dict

    # Only keep the lore
    champ_lore_json = {
        "name": data["name"],
        "id": data["id"],
        "title": data["title"],
        "lore": data["lore"]
    }

    # Upload to S3
    s3_key = f"{folder_prefix}{champion_name.lower()}.json"
    s3.upload_fileobj(
        io.BytesIO(json.dumps(champ_lore_json).encode("utf-8")),
        S3_BUCKET,
        s3_key
    )
    print(f"Uploaded lore for {champion_name} to {S3_BUCKET}/{s3_key}")

# === Loop over all champions and upload ===
for champ in champion_list:
    upload_champion_lore(champ)
