import os

from flask import Flask

from src.services.s3 import get_champs_and_models_txt
from src.config.settings import Config


def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=str(Config.BASE_DIR / "templates"),
        static_folder=str(Config.BASE_DIR / "static"),
    )
    
    # Fetch champions list from S3 and save to static folder
    get_champs_and_models_txt(str(app.static_folder))
    
    # Register blueprints
    from src.routes import bp
    app.register_blueprint(bp)
    
    return app

