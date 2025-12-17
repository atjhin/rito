import os
import random

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv


load_dotenv()


def _get_s3_client():
    """Create and return an S3 client with credentials from environment."""
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        region_name=os.getenv("S3_REGION"),
    )


def get_champs_and_models_txt(save_path: str):
    """
    Fetch champion names from S3 and save to a local text file.
    
    Args:
        save_path: Directory path where champions.txt will be saved
    """
    bucket = os.getenv("S3_BUCKET")
    assert bucket is not None, "S3_BUCKET environment variable not set."

    s3 = _get_s3_client()

    try:
        list_of_champions = s3.list_objects_v2(
            Bucket=bucket, Prefix="champions_fandom/", Delimiter="/"
        )
        champ_names = [
            obj["Prefix"].split("/")[1].replace("_", " ")
            for obj in list_of_champions.get("CommonPrefixes", [])
        ]

    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Error fetching champions: {e}")
        return

    os.makedirs(save_path, exist_ok=True)
    with open(os.path.join(save_path, "champions.txt"), "w") as f:
        f.write("\n".join(champ_names))


def fetch_champion_data_from_s3(
    character_name: str, attribute: str, source: str = "champions_fandom"
):
    """
    Fetch specific champion data (background, etc.) from S3.
    
    Args:
        character_name: Name of the champion
        attribute: Type of data to fetch (e.g., "background")
        source: S3 prefix/source folder
        
    Returns:
        The data as a string, or None if not found
    """
    bucket = os.getenv("S3_BUCKET")
    s3 = _get_s3_client()

    try:
        if attribute == "background":
            # Fetch the latest version based on date
            prefix = f"{source}/{character_name}/{attribute}/"
            response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if "Contents" not in response:
                print(f"No {attribute} versions found for {character_name}.")
                return None
            versions = [
                obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".txt")
            ]
            if not versions:
                print(f"No {attribute} versions found for {character_name}.")
                return None
            latest_version = sorted(versions)[-1]
            key = latest_version
        else:
            key = f"{source}/{character_name}/{attribute}.txt"

        obj = s3.get_object(Bucket=bucket, Key=key)
        data = obj["Body"].read().decode("utf-8")
        return data

    except s3.exceptions.NoSuchKey:
        print(f"Error: The object {key} does not exist in bucket {bucket}.")
        return None
    except (NoCredentialsError, PartialCredentialsError):
        print("Error: AWS credentials not found or incomplete.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_all_characters_from_s3(source: str = "champions_fandom"):
    """
    Get a list of all available characters from S3.
    
    Args:
        source: S3 prefix/source folder
        
    Returns:
        List of character names
    """
    bucket = os.getenv("S3_BUCKET")
    s3 = _get_s3_client()

    try:
        prefix = f"{source}/"
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/")
        if "CommonPrefixes" not in response:
            print("No characters found.")
            return []
        characters = [cp["Prefix"].split("/")[-2] for cp in response["CommonPrefixes"]]
        return characters
    except (NoCredentialsError, PartialCredentialsError):
        print("Error: AWS credentials not found or incomplete.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def get_sample_fanfiction_from_s3():
    """
    Fetch a random sample fanfiction from S3.
    
    Returns:
        Dict with 'key', 'filename', and 'content', or None if not found
    """
    bucket = os.getenv("S3_BUCKET")
    s3 = _get_s3_client()

    try:
        path = "sample_fanfictions/"
        response = s3.list_objects_v2(Bucket=bucket, Prefix=path)

        if "Contents" not in response:
            print(f"No files found in {path}")
            return None

        # Filter out directories (keys ending with '/')
        files = [
            obj["Key"] for obj in response["Contents"] if not obj["Key"].endswith("/")
        ]

        if not files:
            print(f"No files found in {path}")
            return None

        # Pick a random file
        random_file = random.choice(files)
        print(f"Selected random file: {random_file}")

        # Download and read the file
        obj = s3.get_object(Bucket=bucket, Key=random_file)
        content = obj["Body"].read().decode("utf-8")

        return {
            "key": random_file,
            "filename": os.path.basename(random_file),
            "content": content,
        }

    except Exception as e:
        print(f"Error reading from S3: {e}")
        return None

