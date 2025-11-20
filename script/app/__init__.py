from flask import Flask
import os
from app.database.fetch_from_s3 import get_champs_and_models_txt

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    get_champs_and_models_txt(os.path.join(app.static_folder))

    from app.routes import bp
    app.register_blueprint(bp)

    return app
