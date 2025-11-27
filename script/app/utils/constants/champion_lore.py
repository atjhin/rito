from app.database.fetch_from_s3 import fetch_champion_data_from_s3
from app.utils.lore_summarizer import summarize_lore

def get_lore(name, story_context=None):
    """
    Fetch champion lore from S3 and optionally summarize it based on story context.
    
    Args:
        name: Champion name
        story_context: Optional story scenario for contextual summarization
        
    Returns:
        Full lore if no story_context provided, otherwise summarized lore
    """
    name = name.replace(" ", "_")
    lore = fetch_champion_data_from_s3(name, "background")
    
    if not lore:
        return f"{name} is a champion from League of Legends."
    
    # If story context is provided, summarize the lore
    if story_context:
        return summarize_lore(name, lore, story_context)
    
    return lore


def get_sample_fanfiction():
    """
    Fetch sample fanfiction from S3.
    
    Returns:
        Sample fanfiction text
    """
    fanfiction = fetch_champion_data_from_s3("sample_fanfiction", "fanfiction", source="sample_fanfiction")
    
    if not fanfiction:
        return "No sample fanfiction available."
    
    return fanfiction