"""
Flask API Routes

This service handles:
- Frontend rendering
- User input validation
- Calling the LangGraph service for story generation
"""

from __future__ import annotations

import os
import logging

from dotenv import load_dotenv
from flask import Blueprint, render_template, jsonify, request
from google import genai
from google.auth.transport.requests import Request
from google.oauth2 import id_token
import google.auth
import httpx

from src.config import Config


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Blueprint setup
# ---------------------------------------------------------------------------

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")


@bp.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "flask-api",
        "version": "1.0.0",
    })


# ---------------------------------------------------------------------------
# LLM (Google Gemini) configuration for input validation
# ---------------------------------------------------------------------------

load_dotenv()

_GEMINI_MODEL_NAME = "gemini-2.5-flash"
_API_KEY = os.getenv("GOOGLE_API_KEY")

if _API_KEY:
    _genai_client = genai.Client(api_key=_API_KEY)
else:
    _genai_client = None
    logger.warning("GOOGLE_API_KEY not set - input validation will be limited")


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
# LLM helpers for input validation
# ---------------------------------------------------------------------------


def _llm_refine_story_if_needed(story: str) -> dict:
    """
    Validates story and returns dict with validation info.
    Returns: {"valid": bool, "story": str, "feedback": str}
    """
    if _genai_client is None:
        # Skip validation if no API key
        return {"valid": True, "story": story, "feedback": ""}
    
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
        logger.error(f"[LLM] Story validation error: {e}")
        return {
            "valid": False,
            "story": story,
            "feedback": "There was an internal error while validating your story. Please try again.",
        }

    original_normalized = story.strip().rstrip(".,!?;:").lower()
    refined_normalized = refined.rstrip(".,!?;:").lower()

    is_valid = original_normalized == refined_normalized

    if is_valid:
        logger.info(f"Story validation: VALID - '{story}'")
        return {"valid": True, "story": story, "feedback": ""}
    else:
        logger.info(f"Story validation: INVALID - Original: '{story}' -> Refined: '{refined}'")
        return {
            "valid": False,
            "story": refined,
            "feedback": "Please provide a clear and coherent story outline.",
        }


def _llm_infer_personality_if_needed(champ_name: str, personality: str | None) -> str:
    """
    If provided personality is valid -> return unchanged.
    If missing/invalid -> ask Gemini for the canonical/dominant personality.
    """
    if personality and _is_valid_personality(personality):
        return personality

    if _genai_client is None:
        return "Neutral"

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
        logger.error(f"[LLM] Personality inference error for {champ_name}: {e}")
        return "Neutral"

    words = text.split()
    inferred = " ".join(words[:3]) if words else "Neutral"
    final_p = inferred if _is_valid_personality(inferred) else "Neutral"
    return final_p


# ---------------------------------------------------------------------------
# LangGraph Service Client
# ---------------------------------------------------------------------------


async def call_langgraph_service(scenario: str, champions: list) -> dict:
    """
    Call the LangGraph service to generate a story.
    
    Args:
        scenario: The story scenario
        champions: List of champion dictionaries
        
    Returns:
        Response from LangGraph service
    """
    url = f"{Config.LANGGRAPH_SERVICE_URL}/generate"
    
    payload = {
        "scenario": scenario,
        "champions": champions,
    }
    
    logger.info(f"Calling LangGraph service at {url}")
    
    async with httpx.AsyncClient(timeout=Config.LANGGRAPH_TIMEOUT) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def _get_id_token_for_cloud_run(target_url: str) -> str | None:
    """
    Get an ID token for Cloud Run service-to-service authentication.
    Returns None if running locally (no credentials).
    """
    try:
        # Get credentials from the default service account
        credentials, _ = google.auth.default()
        
        # Create a request to get an ID token
        auth_req = Request()
        
        # Get ID token for the target audience
        token = id_token.fetch_id_token(auth_req, target_url)
        return token
    except Exception as e:
        logger.debug(f"Could not get ID token (likely running locally): {e}")
        return None


def call_langgraph_service_sync(scenario: str, champions: list) -> dict:
    """
    Synchronous version of call_langgraph_service for Flask.
    Includes authentication for Cloud Run service-to-service communication.
    """
    url = f"{Config.LANGGRAPH_SERVICE_URL}/generate"
    
    payload = {
        "scenario": scenario,
        "champions": champions,
    }
    
    logger.info(f"Calling LangGraph service at {url}")
    
    # Build headers with authentication for Cloud Run
    headers = {"Content-Type": "application/json"}
    
    # Add authentication token if running in Cloud Run
    token = _get_id_token_for_cloud_run(Config.LANGGRAPH_SERVICE_URL)
    if token:
        headers["Authorization"] = f"Bearer {token}"
        logger.info("Using service-to-service authentication")
    else:
        logger.info("Running without authentication (local development)")
    
    with httpx.Client(timeout=Config.LANGGRAPH_TIMEOUT) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------


@bp.route("/submit-data", methods=["POST"])
def receive_data():
    """Handle story generation requests."""
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
        "gemini": "gemini_2_5_flash_lite",
        "grok-4": "grok_4",
    }
    DEFAULT_MODEL = "grok_4"
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
        logger.info(f"Max retries reached. Using LLM-generated story: {story_validated}")
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

    logger.info(f"Story validated: {story_validated}")
    logger.info(f"Auto-generated: {auto_generated}")
    logger.info(f"Champions: {champions}")

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

    # Call LangGraph service for story generation
    try:
        result = call_langgraph_service_sync(story_validated, champions)
        
        if result.get("success"):
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Payload processed",
                        "result": result.get("story"),
                        "scenario_used": story_validated,
                        "champions_used": champions,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": result.get("error", "Story generation failed"),
                    }
                ),
                500,
            )
            
    except httpx.TimeoutException:
        logger.error("LangGraph service timeout")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Story generation timed out. Please try again.",
                }
            ),
            504,
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"LangGraph service error: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Story generation service error: {e.response.status_code}",
                }
            ),
            502,
        )
    except Exception as e:
        logger.error(f"Unexpected error calling LangGraph service: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "An unexpected error occurred. Please try again.",
                }
            ),
            500,
        )

