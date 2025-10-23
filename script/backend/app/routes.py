from flask import Blueprint, render_template, jsonify, request
from .database.supabase import create_story
# Create a Blueprint named 'main'
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/api/story', methods=['POST'])
def get_story_details():
    try:
        data = request.get_json()
        result = create_story(data)
        return jsonify(result), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
