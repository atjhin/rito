import os
import json
from supabase import create_client, Client

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

def create_story(data):
    """Creates a story in the 'story_board' table."""
    supabase = initialize_supabase()  # Ensure supabase client is initialized

    character1 = data.get("character1")
    character2 = data.get("character2")
    context = data.get("context", "")

    # Insert new story data into Supabase table
    response = supabase.table("story_board").insert({
        "character1": character1,
        "character2": character2,
        "context": context
    }).execute()

    return response.data

def get_characters():
    """Fetches characters from the 'characters' table and saves to a JSON file."""
    supabase = initialize_supabase()  # Ensure supabase client is initialized

    # Fetch characters from the 'characters' table
    response = supabase.table("characters").select("*").execute()

    # Create a directory to store the data
    os.makedirs("temp_data", exist_ok=True)

    # Save the characters data to a JSON file
    with open("temp_data/characters.json", "w") as f:
        json.dump(response.data, f, indent=4)
    
    return response.data
