
import json

def fetch_data_from_s3(character_name, attribute, source="champions_fandom"):
    import boto3
    from botocore.exceptions import NoCredentialsError, PartialCredentialsError
    import os
    from dotenv import load_dotenv

    load_dotenv()

    bucket = os.getenv("S3_BUCKET")

    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        region_name=os.getenv("S3_REGION")
    )

    try:
        if attribute == "background":
            # Fetch the latest version based on date
            prefix = f"{source}/{character_name}/{attribute}/"
            response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if 'Contents' not in response:
                print(f"No {attribute} versions found for {character_name}.")
                return None
            versions = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.txt')]
            if not versions:
                print(f"No {attribute} versions found for {character_name}.")
                return None
            latest_version = sorted(versions)[-1]
            key = latest_version

        else:
            key = f"{source}/{character_name}/{attribute}.txt"
        obj = s3.get_object(Bucket=bucket, Key=key)
        data = obj['Body'].read().decode('utf-8')

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
    
def get_all_characters_from_s3(source="champions_fandom"):
    import boto3
    from botocore.exceptions import NoCredentialsError, PartialCredentialsError
    import os
    from dotenv import load_dotenv
    import json

    basedir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(basedir, '.env')
    load_dotenv(env_path)

    bucket = os.getenv("S3_BUCKET")

    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        region_name=os.getenv("S3_REGION")
    )

    try:
        prefix = f"{source}/"
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')
        if 'CommonPrefixes' not in response:
            print("No characters found.")
            return []
        characters = [cp['Prefix'].split('/')[-2] for cp in response['CommonPrefixes']]
        return characters
    except (NoCredentialsError, PartialCredentialsError):
        print("Error: AWS credentials not found or incomplete.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    

    
if __name__ == "__main__":
    # character = "Ahri"  # Example character
    # attribute = "background"  # Example attribute

    # data = fetch_data_from_s3(character, attribute)
    # if data:
    #     print(f"{attribute.capitalize()} of {character}:\n{data}")

    all_characters = get_all_characters_from_s3()

    # save to file
    with open("../temp_data/characters_from_s3.json", "w") as f:
        json.dump(all_characters, f, indent=4)