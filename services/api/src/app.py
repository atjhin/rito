"""Flask API Application Factory."""

import os

from flask import Flask

from src.config import Config


def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=str(Config.TEMPLATES_DIR),
        static_folder=str(Config.STATIC_DIR),
    )
    
    # Register blueprints
    from src.routes import bp
    app.register_blueprint(bp)
    
    return app

