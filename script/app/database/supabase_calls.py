import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
# Global supabase client, initialized once and used throughout
supabase: Client = None


def initialize_supabase():
    """Initialize the Supabase client."""
    global supabase

    if supabase is None:  # Only initialize once
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_ADMIN_KEY = os.getenv("SUPABASE_ADMIN_KEY")

        if not SUPABASE_URL:
            raise ValueError("SUPABASE_URL is not set in environment variables.")
        if not SUPABASE_ADMIN_KEY:
            raise ValueError("SUPABASE_ADMIN_KEY is not set in environment variables.")

        # Create and store the Supabase client globally
        supabase = create_client(SUPABASE_URL, SUPABASE_ADMIN_KEY)

        if supabase is None:
            raise ValueError("Failed to initialize Supabase client.")
    
    return supabase


def get_characters():
    """Fetches characters from the 'characters' table and saves to a JSON file."""
    supabase = initialize_supabase()  # Ensure supabase client is initialized

    # Fetch characters from the 'characters' table
    response = supabase.table("characters").select("*").execute()

    # Create a directory to store the data
    os.makedirs("temp_data", exist_ok=True)

    # Save the characters data to a JSON file
    with open("temp_data/characters_from_supabase.json", "w") as f:
        json.dump(response.data, f, indent=4)
    
    return response.data

def insert_character(name: str):
    """Inserts a new character into the 'characters' table."""
    supabase = initialize_supabase()  # Ensure supabase client is initialized

    character_data = {
        "name": name
    }
    
    response = supabase.table("characters").insert(character_data).execute()
    return response.data


def upload_characters_from_s3():
    print(f"Current working directory: {os.getcwd()}")
    supabase_characters = get_characters()
    temp_characters_path = "temp_data/characters_from_s3.json"
    with open(temp_characters_path, "r") as f:
        s3_characters = json.load(f)

    # Insert characters from S3 into Supabase if they don't already exist
    existing_names = {char['name'] for char in supabase_characters}
    for char_name in s3_characters:
        if char_name not in existing_names:
            insert_character(char_name)
            print(f"Inserted character: {char_name}")
        else:
            print(f"Character already exists: {char_name}")
    return

def get_character_by_name(name: str):
    """Fetch a character by name from the 'characters' table."""
    supabase = initialize_supabase()  # Ensure supabase client is initialized

    # replace space with underscore
    name = name.replace(" ", "_")
    response = supabase.table("characters").select("*").eq("name", name).execute()
    return response.data

if __name__ == "__main__":
    # upload_characters_from_s3()
    # Example usage
    character = get_character_by_name("Ahri")
    print(character[0]['id'] if character else "Character not found.")