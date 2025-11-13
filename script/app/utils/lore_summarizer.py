import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

_API_KEY = os.getenv("GOOGLE_API_KEY")
if not _API_KEY:
    raise RuntimeError("GOOGLE_API_KEY missing in environment")

genai.configure(api_key=_API_KEY)
_GEMINI_MODEL_NAME = "gemini-2.0-flash-lite"
_gemini_model = genai.GenerativeModel(_GEMINI_MODEL_NAME)


def summarize_lore(champion_name: str, full_lore: str, story_context: str) -> str:
    """
    Uses  LLM to create a condensed version of champion lore
    that's relevant to the given story context.
    
    Args:
        champion_name: The name of the champion
        full_lore: The complete lore text from S3
        story_context: The user's story/scenario for context
        
    Returns:
        A summarized version of the lore (max 200 words)
    """
    if not full_lore:
        return f"{champion_name} is a champion from League of Legends."
    
    prompt = f"""
    You are tasked with summarizing a League of Legends champion's lore for use in a roleplay scenario.
    
    Champion: {champion_name}
    
    Story Context:
    \"\"\"{story_context}\"\"\"
    
    Full Lore:
    \"\"\"{full_lore}\"\"\"
    
    Instructions:
    1. Create a concise summary of {champion_name}'s lore in 150-200 words maximum.
    2. Focus on personality traits, key motivations, and character essence.
    3. Prioritize information that would be relevant to the story context provided.
    4. Include their role/archetype (e.g., assassin, mage, warrior) if relevant.
    5. Maintain the champion's core identity and speaking style.
    6. Remove unnecessary world-building details unless critical to their character.
    7. Write in third person, present tense.
    8. Output ONLY the summary text with no extra commentary or formatting.
    """
    
    try:
        response = _gemini_model.generate_content(prompt)
        summarized = (response.text or "").strip()
        
        # Fallback if response is empty or too short
        if len(summarized) < 50:
            return _create_basic_summary(full_lore)
        
        return summarized
    
    except Exception as e:
        print(f"Error summarizing lore for {champion_name}: {e}")
        return _create_basic_summary(full_lore)


def _create_basic_summary(full_lore: str) -> str:
    """
    Creates a basic summary by taking the first ~200 words if LLM fails.
    """
    words = full_lore.split()
    if len(words) <= 200:
        return full_lore
    return " ".join(words[:200]) + "..."
