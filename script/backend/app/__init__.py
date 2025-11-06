from flask import Flask
from dotenv import load_dotenv
import os


from .database.fetch_from_s3 import get_champs_and_models_txt

def create_app():
    get_champs_and_models_txt(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

    app = Flask(__name__)

    from .routes import bp
    app.register_blueprint(bp)

    return app
