"""
DASHBOARD endpoints
  GET /api/dashboard/student   (student)
  GET /api/dashboard/teacher   (teacher)
"""
from flask import Blueprint, current_app, g, jsonify

from backend.middleware.auth_middleware import require_auth, require_role
from backend.services import dashboard_service

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.get("/student")
@require_auth
@require_role("student")
def student_dashboard():
    db = current_app.config["DB"]
    return jsonify(dashboard_service.student_dashboard(db, g.current_user["user_id"]))


@dashboard_bp.get("/teacher")
@require_auth
@require_role("teacher")
def teacher_dashboard():
    db = current_app.config["DB"]
    return jsonify(dashboard_service.teacher_dashboard(db, g.current_user["user_id"]))
