from flask import Blueprint, render_template, jsonify, request
from app.utils.core.logger import Logger
from app.utils.core.story_teller import StoryTeller
from app.utils.data_models.story_teller_item import StoryTellerItem
# Create a Blueprint named 'main'
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/submit-data', methods=['POST'])
def receive_data_test():

    scenario = "Twisted Fate and Zed are computer science students. They are arguing about their group project."
    json_input = [
        {
            "name": "Zed",
            "personality": "Happy",
            "models": "gemini_2_5_flash_lite"
        },
        {
            "name": "TwistedFate",
            "personality": "Sad",
            "models": "gemini_2_5_flash_lite"
        },
    ]

    logger = Logger()
    story_teller = StoryTeller(
        StoryTellerItem(
            scenario=scenario, champions=json_input, logger=logger
        )
    )

    assert story_teller is not None
    story_teller.build_graph()
    print(story_teller.invoke())  
  
    return jsonify({"success": True, "message": "Payload received by server"}), 200



# @bp.route('/submit-data', methods=['POST'])
# def receive_data():
#     if not request.is_json:
#         return jsonify({"success": False, "message": "Expected application/json body"}), 400

#     data = request.get_json(silent=True) or {}
#     story = data.get("story")
#     characters = data.get("characters")

#     if not story or not isinstance(characters, list) or not characters:
#         return jsonify({
#             "success": False,
#             "message": "Body must include 'story' (str) and non-empty 'characters' (list)."
#         }), 400

    
#     MODEL_ALIASES = {
#         "gemini-2.5-flash": "gemini_2_5_flash_lite",
#         "gemini-2.0-flash": "gemini_2_0_flash_lite",
       
#     }
#     DEFAULT_MODEL = "gemini_2_5_flash_lite"  
    
#     DEFAULT_PERSONALITY = "Neutral"

#     def normalize_model(m):
#         if not m:
#             return DEFAULT_MODEL
#         m_lower = str(m).strip().lower()
#         if m_lower in MODEL_ALIASES:
#             return MODEL_ALIASES[m_lower]
#         fallback = "".join(ch if ch.isalnum() else "_" for ch in m_lower)
#         return MODEL_ALIASES.get(m_lower, fallback)

#     champions = []
#     for c in characters:
#         name = c.get("name")
#         p_raw = c.get("personality")
#         personality = (
#             p_raw.strip() if isinstance(p_raw, str) and p_raw.strip() else DEFAULT_PERSONALITY
#         )
#         models = c.get("models")

#         if not name:
#             return jsonify({"success": False, "message": "Each character needs a 'name'."}), 400

#         # Accept list or string; normalize each, then pick first for now
#         if isinstance(models, list):
#             norm_models = [normalize_model(x) for x in models if x]
#             model_value = norm_models[0] if norm_models else DEFAULT_MODEL
#         else:
#             model_value = normalize_model(models)

#         champions.append({
#             "name": name,
#             "personality": personality,
#             "models": model_value 
#         })

#     #print(champions)
#     #print(story)

#     logger = Logger()
#     story_teller = StoryTeller(
#         StoryTellerItem(
#             scenario=story, champions=champions, logger=logger
#         )
#     )

#     assert story_teller is not None
#     story_teller.build_graph()
#     print(story_teller.invoke())  
  
#     return jsonify({"success": True, "message": "Payload received by server"}), 200

