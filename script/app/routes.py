from flask import Blueprint, render_template, jsonify, request

# Create a Blueprint named 'main'
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/api/echo', methods=['POST'])
def echo():
    data = request.get_json()
    return jsonify({"you_sent": data})
