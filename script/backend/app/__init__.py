from flask import Flask
from dotenv import load_dotenv
from supabase import create_client
import os

supabase = None

def create_app():
    basedir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(basedir, '..', '.env')
    load_dotenv(env_path)

    app = Flask(__name__)

    # Initialize Supabase client
    global supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ADMIN_KEY = os.getenv("SUPABASE_ADMIN_KEY")
    supabase = create_client(SUPABASE_URL, SUPABASE_ADMIN_KEY)

    from .routes import bp
    app.register_blueprint(bp)

    return app
