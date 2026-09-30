"""
Cloud-Based Student Assignment Submission & Feedback Portal - backend entry point.

Run locally with:
    python -m backend.app
or with the Flask CLI:
    flask --app backend.app run --port 8000
"""
import logging

from flask import Flask, jsonify

from backend.config import Settings
from backend.middleware.error_handler import register_error_handlers
from backend.routes.assignment_routes import assignment_bp
from backend.routes.auth_routes import auth_bp
from backend.routes.course_routes import course_bp
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.grading_routes import grading_bp
from backend.routes.submission_routes import submission_bp
from cloud.database_service import DatabaseService
from cloud.storage_service import build_storage_backend


def create_app(settings: Settings = None) -> Flask:
    settings = settings or Settings.from_env()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    app.config["DB"] = DatabaseService(settings)
    app.config["STORAGE"] = build_storage_backend(settings)
    app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # hard cap; per-assignment limit checked again in code

    # CORS: only the configured frontend origin(s) may call this API with credentials.
    try:
        from flask_cors import CORS
        CORS(app, origins=list(settings.cors_origins), supports_credentials=True)
    except ImportError:
        @app.after_request
        def _basic_cors(resp):
            origin = settings.cors_origins[0] if settings.cors_origins else "*"
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            return resp

    register_error_handlers(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(assignment_bp)
    app.register_blueprint(submission_bp)
    app.register_blueprint(grading_bp)
    app.register_blueprint(dashboard_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "cloud_provider": settings.cloud_provider})

    return app


app = create_app()

if __name__ == "__main__":
    settings = app.config["SETTINGS"]
    app.run(host="0.0.0.0", port=8000, debug=(settings.app_env == "local"))
