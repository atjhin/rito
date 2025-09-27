from flask import Flask

def create_app():
    """Application factory function."""
    app = Flask(__name__)

    # Import routes (this registers them with app)
    from . import routes

    # Register the blueprint defined in routes.py
    app.register_blueprint(routes.bp)

    return app
