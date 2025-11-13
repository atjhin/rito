from flask import Blueprint, render_template, jsonify, request
from app.utils.core.logger import Logger
from app.utils.core.story_teller import StoryTeller
from app.utils.data_models.story_teller_item import StoryTellerItem

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Create a Blueprint named 'main'
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

#testing purposes
# @bp.route('/submit-data', methods=['POST'])
# def receive_data_test():

#     scenario = "Twisted Fate and Zed are computer science students. They are arguing about their group project."
#     json_input = [
#         {
#             "name": "Zed",
#             "personality": "Happy",
#             "models": "gemini_2_5_flash_lite"
#         },
#         {
#             "name": "TwistedFate",
#             "personality": "Sad",
#             "models": "gemini_2_5_flash_lite"
#         },
#     ]
#     logger = Logger()
#     story_teller = StoryTeller(
#         StoryTellerItem(
#             scenario=scenario, champions=json_input, logger=logger
#         )
#     )

#     assert story_teller is not None
#     story_teller.build_graph()
#     print(story_teller.invoke())  
  
#     return jsonify({"success": True, "message": "Payload received by server"}), 200


#original code below without LLM
'''
@bp.route('/submit-data', methods=['POST'])
def receive_data():
    if not request.is_json:
        return jsonify({"success": False, "message": "Expected application/json body"}), 400

    data = request.get_json(silent=True) or {}
    story = data.get("story")
    characters = data.get("characters")

    if not story or not isinstance(characters, list) or not characters:
        return jsonify({
            "success": False,
            "message": "Body must include 'story' (str) and non-empty 'characters' (list)."
        }), 400

    
    MODEL_ALIASES = {
        "gemini-2.5-flash": "gemini_2_5_flash_lite",
        "gemini-2.0-flash": "gemini_2_0_flash_lite",
       
    }
    DEFAULT_MODEL = "gemini_2_5_flash_lite"  
    
    DEFAULT_PERSONALITY = "Neutral"

    def normalize_model(m):
        if not m:
            return DEFAULT_MODEL
        m_lower = str(m).strip().lower()
        if m_lower in MODEL_ALIASES:
            return MODEL_ALIASES[m_lower]
        fallback = "".join(ch if ch.isalnum() else "_" for ch in m_lower)
        return MODEL_ALIASES.get(m_lower, fallback)

    champions = []
    for c in characters:
        name = c.get("name")
        p_raw = c.get("personality")
        personality = (
            p_raw.strip() if isinstance(p_raw, str) and p_raw.strip() else DEFAULT_PERSONALITY
        )
        models = c.get("models")

        if not name:
            return jsonify({"success": False, "message": "Each character needs a 'name'."}), 400

        # Accept list or string; normalize each, then pick first for now
        if isinstance(models, list):
            norm_models = [normalize_model(x) for x in models if x]
            model_value = norm_models[0] if norm_models else DEFAULT_MODEL
        else:
            model_value = normalize_model(models)

        champions.append({
            "name": name,
            "personality": personality,
            "models": model_value 
        })

    #print(champions)
    #print(story)

    logger = Logger()
    story_teller = StoryTeller(
        StoryTellerItem(
            scenario=story, champions=champions, logger=logger
        )
    )

    assert story_teller is not None
    story_teller.build_graph()
    print(story_teller.invoke())  
  
    return jsonify({"success": True, "message": "Payload received by server"}), 200

'''

load_dotenv()  

_GEMINI_MODEL_NAME = "gemini-2.0-flash-lite"  
_API_KEY = os.getenv("GOOGLE_API_KEY")
if not _API_KEY:
    raise RuntimeError("GOOGLE_API_KEY missing in environment")

genai.configure(api_key=_API_KEY)
_gemini_model = genai.GenerativeModel(_GEMINI_MODEL_NAME)

# -----------------------------
# Simple validators
# -----------------------------


def _is_valid_personality(p: str) -> bool:
    """
    Personality should be short (<= 3 words), non-empty, alphabetic-ish.
    """
    if not isinstance(p, str):
        return False
    p2 = p.strip()
    if not p2:
        return False
    # keep it concise
    if len(p2.split()) > 3:
        return False
    # allow hyphens/spaces; require mostly letters
    letters = sum(ch.isalpha() for ch in p2)
    return letters >= max(3, len(p2)//2)


def _llm_refine_story_if_needed(story: str) -> str:
    """
    If story invalid -> ask Gemini to refine. If valid -> return original unchanged.
    """
    prompt = f"""
            You are validating a short scenario written by a user for a roleplay between League of Legends characters.

            User input story:
            \"\"\"{story}\"\"\"

            Instructions:
            1. If the user's input forms a coherent and meaningful sentence or phrase (even if short), RETURN IT EXACTLY as written — do NOT modify, paraphrase, or shorten it.
            2. If the input appears to be a random sequence of letters, symbols, or an incomplete sentence fragment that lacks clear meaning,
            then rewrite it into a simple, coherent, and complete scenario (1–2 sentences, under 50 words) suitable for a dialogue-driven scene.
            3. DO NOT add new characters, names, world details, or filler content.
            4. Output ONLY the final scenario text, with no commentary, quotes, or formatting.
            """

    resp = _gemini_model.generate_content(prompt)
    refined = (resp.text or "").strip()
    print(f"Refined story: {refined}")
    return refined


def _llm_infer_personality_if_needed(champ_name: str, personality: str | None) -> str:
    """
    If provided personality is valid -> return unchanged.
    If missing/invalid -> ask Gemini for the canonical/dominant personality of {champ_name} in LoL.
    """
    
    prompt = f"""
            Champion name: \"\"\"{champ_name}\"\"\"
            User-provided personality: \"\"\"{personality}\"\"\"

            Instructions:
            1. If the user's input for personality is a meaningful English word or short phrase that could describe a personality 
            (e.g., "calm", "brave", "arrogant", "determined"), KEEP IT EXACTLY as written — do not paraphrase, reword, or modify it.
            2. Only if the user's input is 'None', or a random sequence of letters/symbols (nonsensical), 
            then replace it by inferring the champion's dominant personality from League of Legends lore.
            3. When inferring, use 1–2 adjectives that best describe {champ_name}’s typical personality 
            (e.g., "Stoic", "Cunning", "Honorable", "Vengeful").
            4. Return ONLY the final personality text — no quotes, commentary, punctuation, or extra words.
            """

    resp = _gemini_model.generate_content(prompt)
    text = (resp.text or "").strip()
    # Final cleanup: keep it short
    words = text.split()
    inferred = " ".join(words[:3]) if words else "Neutral"
    # As a guard, ensure it passes validator; otherwise pick "Neutral"
    final_p = inferred if _is_valid_personality(inferred) else "Neutral"
    return final_p


@bp.route('/submit-data', methods=['POST'])
def receive_data():
    if not request.is_json:
        return jsonify({"success": False, "message": "Expected application/json body"}), 400

    data = request.get_json(silent=True) or {}
    story = data.get("story")
    characters = data.get("characters")

    if not story or not isinstance(characters, list) or not characters:
        return jsonify({
            "success": False,
            "message": "Body must include 'story' (str) and non-empty 'characters' (list)."
        }), 400

    MODEL_ALIASES = {
        "gemini-2.5-flash": "gemini_2_5_flash_lite",
        "gemini-2.0-flash": "gemini_2_0_flash_lite",
    }
    DEFAULT_MODEL = "gemini_2_5_flash_lite"
    DEFAULT_PERSONALITY = "Neutral"  

    def normalize_model(m):
        if not m:
            return DEFAULT_MODEL
        m_lower = str(m).strip().lower()
        if m_lower in MODEL_ALIASES:
            return MODEL_ALIASES[m_lower]
        return "".join(ch if ch.isalnum() else "_" for ch in m_lower)

    # Story: refine ONLY if invalid
    story_validated = _llm_refine_story_if_needed(story)

    champions = []
    for c in characters:
        name = c.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            return jsonify({"success": False, "message": "Each character needs a non-empty 'name'."}), 400
        clean_name = (
            name.replace("'", "")    
                .replace("’", "")    
                .replace(" ", "")   
                .strip()
        )
        name = clean_name
        # Personality: use LLM only if missing/invalid
        raw_personality = c.get("personality")
        personality_final = _llm_infer_personality_if_needed(name, raw_personality) or DEFAULT_PERSONALITY

        models = c.get("models")
        if isinstance(models, list):
            norm_models = [normalize_model(x) for x in models if x]
            model_value = norm_models[0] if norm_models else DEFAULT_MODEL
        else:
            model_value = normalize_model(models)

        champions.append({
            "name": name,
            "personality": personality_final,  
            "models": model_value
        })
    
    print(f"\n{'='*80}")
    print(f"Story validated: {story_validated}")
    print(f"Champions: {champions}")
    print(f"{'='*80}\n")
    
    logger = Logger()
    story_teller = StoryTeller(
        StoryTellerItem(
            scenario=story_validated,
            champions=champions,
            logger=logger
        )
    )

    assert story_teller is not None
    story_teller.build_graph()
    result = story_teller.invoke()

    return jsonify({
        "success": True,
        "message": "Payload processed",
        "result": result,
        "scenario_used": story_validated,
        "champions_used": champions
    }), 200