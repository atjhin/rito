from flask import Flask
from dotenv import load_dotenv
import os


from .database.supabase_calls import get_characters

def create_app():
    basedir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(basedir, '..', '.env')
    load_dotenv(env_path)

    app = Flask(__name__)

    get_characters()

    from .routes import bp
    app.register_blueprint(bp)

    return app
