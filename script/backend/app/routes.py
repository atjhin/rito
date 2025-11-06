from flask import Blueprint, render_template, jsonify, request
from app.utils.core.logger import Logger
from app.utils.core.story_teller import StoryTeller
from app.utils.data_models.story_teller_item import StoryTellerItem
# Create a Blueprint named 'main'
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

# @bp.route('/submit-data', methods=['POST'])
# def receive_data():

#     if not request.json:
#         return jsonify({"success": False, "message": "Missing JSON data"}), 400

#     data = request.json

#     print("\n--- RECEIVED PAYLOAD FROM CLIENT ---")
#     print(data) 
#     logger = Logger()
#     story_teller = StoryTeller(
#         scenario=data.get("story", ""),
#         champions_json=data.get("champions", []),
#         logger=logger
#     )
#     assert story_teller is not None
#     print("------------------------------------\n")
#     # flush the log file to S3

#     return jsonify({"success": True, "message": "Payload received by server"}), 200


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
