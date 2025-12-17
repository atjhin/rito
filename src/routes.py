from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Blueprint, render_template, jsonify, request
from google import genai

from src.core.logger import Logger
from src.core.story_teller import StoryTeller
from src.schemas.story_config import StoryTellerItem


# ---------------------------------------------------------------------------
# Blueprint setup
# ---------------------------------------------------------------------------

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# LLM (Google Gemini) configuration
# ---------------------------------------------------------------------------

load_dotenv()

_GEMINI_MODEL_NAME = "gemini-2.5-flash"
_API_KEY = os.getenv("GOOGLE_API_KEY")

if not _API_KEY:
    raise RuntimeError("GOOGLE_API_KEY missing in environment")

_genai_client = genai.Client(api_key=_API_KEY)


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


def _is_valid_personality(p: str) -> bool:
    """Personality should be short (<= 3 words), non-empty, alphabetic-ish."""
    if not isinstance(p, str):
        return False
    p2 = p.strip()
    if not p2:
        return False
    if len(p2.split()) > 3:
        return False
    letters = sum(ch.isalpha() for ch in p2)
    return letters >= max(3, len(p2) // 2)


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------


def _llm_refine_story_if_needed(story: str) -> dict:
    """
    Validates story and returns dict with validation info.
    Returns: {"valid": bool, "story": str, "feedback": str}
    """
    prompt = f"""
You are validating a short scenario written by a user for a roleplay between League of Legends characters.

User input story:
\"\"\"{story}\"\"\"

Instructions:
1. If the user's input forms a coherent and meaningful sentence or phrase (even if short), RETURN IT EXACTLY as written — do NOT modify, paraphrase, or shorten it. 
2. If the user made mistakes (typos, grammar), don't change the meaning; just return it as is.
3. If the input appears to be a random sequence of letters, symbols, or an incomplete sentence fragment that lacks clear meaning,
   then rewrite it into a simple, coherent, and complete scenario (1–2 sentences, under 50 words) suitable for a dialogue-driven scene.
4. DO NOT add new characters, names, world details, or filler content.
5. Output ONLY the final scenario text, with no commentary, quotes, or formatting.
"""

    try:
        resp = _genai_client.models.generate_content(
            model=_GEMINI_MODEL_NAME,
            contents=prompt,
        )
        refined = (resp.text or "").strip()
    except Exception as e:
        print(f"[LLM] Story validation error: {e}")
        return {
            "valid": False,
            "story": story,
            "feedback": "There was an internal error while validating your story. Please try again.",
        }

    original_normalized = story.strip().rstrip(".,!?;:").lower()
    refined_normalized = refined.rstrip(".,!?;:").lower()

    is_valid = original_normalized == refined_normalized

    if is_valid:
        print(f"Story validation: VALID - '{story}'")
        return {"valid": True, "story": story, "feedback": ""}
    else:
        print(f"Story validation: INVALID - Original: '{story}' -> Refined: '{refined}'")
        return {
            "valid": False,
            "story": refined,
            "feedback": "Please provide a clear and coherent story outline.",
        }


def _llm_infer_personality_if_needed(champ_name: str, personality: str | None) -> str:
    """
    If provided personality is valid -> return unchanged.
    If missing/invalid -> ask Gemini for the canonical/dominant personality of {champ_name} in LoL.
    """
    if personality and _is_valid_personality(personality):
        return personality

    prompt = f"""
Champion name: \"\"\"{champ_name}\"\"\"
User-provided personality: \"\"\"{personality}\"\"\"

Instructions:
1. If the user's input for personality is a meaningful English word or short phrase that could describe a personality 
   (e.g., "calm", "brave", "arrogant", "determined"), KEEP IT EXACTLY as written — do not paraphrase, reword, or modify it.
2. Only if the user's input is 'None', missing, or a random sequence of letters/symbols (nonsensical), 
   then replace it by inferring the champion's dominant personality from League of Legends lore.
3. When inferring, use 1–2 adjectives that best describe {champ_name}'s typical personality 
   (e.g., "Stoic", "Cunning", "Honorable", "Vengeful").
4. Return ONLY the final personality text — no quotes, commentary, punctuation, or extra words.
"""

    try:
        resp = _genai_client.models.generate_content(
            model=_GEMINI_MODEL_NAME,
            contents=prompt,
        )
        text = (resp.text or "").strip()
    except Exception as e:
        print(f"[LLM] Personality inference error for {champ_name}: {e}")
        return "Neutral"

    words = text.split()
    inferred = " ".join(words[:3]) if words else "Neutral"
    final_p = inferred if _is_valid_personality(inferred) else "Neutral"
    return final_p


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------


@bp.route("/submit-data", methods=["POST"])
def receive_data():
    if not request.is_json:
        return jsonify({"success": False, "message": "Expected application/json body"}), 400

    data = request.get_json(silent=True) or {}
    story = data.get("story")
    characters = data.get("characters")
    retry_count = data.get("retry_count", 0)

    if not story or not isinstance(characters, list) or not characters:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Body must include 'story' (str) and non-empty 'characters' (list).",
                }
            ),
            400,
        )

    MODEL_ALIASES = {
        "gemini": "gemini-2.5-flash-lite",
        "grok-4": "grok_4",
    }
    DEFAULT_MODEL = "gemini-2.5-flash-lite"
    DEFAULT_PERSONALITY = "Neutral"

    def normalize_model(m):
        if not m:
            return DEFAULT_MODEL
        m_lower = str(m).strip().lower()
        if m_lower in MODEL_ALIASES:
            return MODEL_ALIASES[m_lower]
        return "".join(ch if ch.isalnum() else "_" for ch in m_lower)

    # Story validation
    validation_result = _llm_refine_story_if_needed(story)

    # If invalid and under 3 retries, ask user to retry
    if not validation_result["valid"] and retry_count < 3:
        return (
            jsonify(
                {
                    "success": False,
                    "needs_retry": True,
                    "retry_count": retry_count + 1,
                    "feedback": validation_result["feedback"],
                    "message": "Please provide a valid story outline.",
                }
            ),
            200,
        )

    # After 3 retries or if valid, proceed
    if retry_count >= 3 and not validation_result["valid"]:
        story_validated = validation_result["story"]
        auto_generated = True
        print(f"Max retries reached. Using LLM-generated story: {story_validated}")
    else:
        story_validated = validation_result["story"]
        auto_generated = False

    champions = []
    for c in characters:
        name = c.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            return (
                jsonify({"success": False, "message": "Each character needs a non-empty 'name'."}),
                400,
            )

        clean_name = name.replace("'", "").replace("'", "").replace(" ", "").strip()
        raw_personality = c.get("personality")
        personality_final = (
            _llm_infer_personality_if_needed(clean_name, raw_personality) or DEFAULT_PERSONALITY
        )

        models = c.get("models")
        if isinstance(models, list):
            norm_models = [normalize_model(x) for x in models if x]
            model_value = norm_models[0] if norm_models else DEFAULT_MODEL
        else:
            model_value = normalize_model(models)

        champions.append(
            {
                "name": clean_name,
                "personality": personality_final,
                "models": model_value,
            }
        )

    print(f"\n{'=' * 80}")
    print(f"Story validated: {story_validated}")
    print(f"Auto-generated: {auto_generated}")
    print(f"Champions: {champions}")
    print(f"{'=' * 80}\n")

    if auto_generated:
        return (
            jsonify(
                {
                    "success": False,
                    "auto_generated": True,
                    "generated_story": story_validated,
                    "message": "Maximum retry attempts reached. We generated a story for you based on your input.",
                    "champions_used": champions,
                }
            ),
            200,
        )

    # Build and run the LangGraph story teller
    logger = Logger()
    story_teller = StoryTeller(
        StoryTellerItem(
            scenario=story_validated,
            champions=champions,
            logger=logger,
        )
    )

    story_teller.build_graph()
    result = story_teller.invoke()

    return (
        jsonify(
            {
                "success": True,
                "message": "Payload processed",
                "result": result,
                "scenario_used": story_validated,
                "champions_used": champions,
            }
        ),
        200,
    )

