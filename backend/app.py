"""
DataCleaner - Flask Application Entry Point
"""
import os
import threading
import numpy as np
from flask import Flask
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from config.settings import Config
from utils.logger import setup_logger
from routes.upload import upload_bp
from routes.clean import clean_bp
from routes.download import download_bp


class NumpyJSONProvider(DefaultJSONProvider):
    """Serialises numpy scalar types (int64, float64) that pandas returns."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def create_app():
    app = Flask(__name__, template_folder="../frontend/templates",
                static_folder="../frontend/static")
    app.json_provider_class = NumpyJSONProvider
    app.json = NumpyJSONProvider(app)
    app.config.from_object(Config)
    CORS(app)

    setup_logger(app)

    # Ensure required directories exist
    for folder in [Config.UPLOAD_FOLDER, Config.CLEANED_FOLDER,
                   Config.REPORTS_FOLDER, Config.LOGS_FOLDER]:
        os.makedirs(folder, exist_ok=True)

    # Register blueprints
    app.register_blueprint(upload_bp,   url_prefix="/api")
    app.register_blueprint(clean_bp,    url_prefix="/api")
    app.register_blueprint(download_bp, url_prefix="/api")

    # Serve the frontend
    from flask import send_from_directory
    @app.route("/")
    def index():
        return send_from_directory("../frontend", "index.html")

    # Start background cleanup thread
    from utils.helpers import start_cleanup_thread
    start_cleanup_thread(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
