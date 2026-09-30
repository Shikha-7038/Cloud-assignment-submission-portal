"""COURSE endpoints (minimal - a course groups assignments under a teacher).
  POST /api/courses          (teacher)
  GET  /api/courses          (any authenticated user)
"""
from flask import Blueprint, current_app, g, jsonify, request

from cloud import database_service as dbs
from backend.middleware.auth_middleware import require_auth, require_role
from backend.utils.errors import BadRequest

course_bp = Blueprint("courses", __name__, url_prefix="/api/courses")


@course_bp.post("")
@require_auth
@require_role("teacher")
def create_course():
    data = request.get_json(silent=True) or {}
    name = (data.get("course_name") or "").strip()
    if not name:
        raise BadRequest("course_name is required.")
    db = current_app.config["DB"]
    course = dbs.create_course(db, name, g.current_user["user_id"])
    return jsonify(course), 201


@course_bp.get("")
@require_auth
def list_courses():
    db = current_app.config["DB"]
    return jsonify(dbs.list_courses(db))
