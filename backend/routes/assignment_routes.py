"""
ASSIGNMENT endpoints
  POST   /api/assignments            (teacher)  createAssignment
  GET    /api/assignments            (any)      getAssignments
  GET    /api/assignments/<id>       (any)      getAssignmentById
  PUT    /api/assignments/<id>       (teacher)  updateAssignment
  DELETE /api/assignments/<id>       (teacher)  deleteAssignment
"""
from flask import Blueprint, current_app, g, jsonify, request

from backend.middleware.auth_middleware import require_auth, require_role
from backend.services import assignment_service

assignment_bp = Blueprint("assignments", __name__, url_prefix="/api/assignments")


@assignment_bp.post("")
@require_auth
@require_role("teacher")
def create_assignment():
    data = request.get_json(silent=True) or {}
    db = current_app.config["DB"]
    assignment = assignment_service.create_assignment(
        db, teacher_id=g.current_user["user_id"], course_id=data.get("course_id"),
        title=data.get("title"), description=data.get("description", ""),
        deadline_str=data.get("deadline"), max_marks=data.get("max_marks", 100),
        allowed_file_types=data.get("allowed_file_types", "pdf,docx"),
        max_file_size_mb=data.get("max_file_size_mb", 10),
        allow_resubmission=data.get("allow_resubmission", True),
        reject_late=data.get("reject_late", False),
    )
    return jsonify(assignment), 201


@assignment_bp.get("")
@require_auth
def list_assignments():
    db = current_app.config["DB"]
    course_id = request.args.get("course_id")
    return jsonify(assignment_service.list_assignments(db, course_id))


@assignment_bp.get("/<assignment_id>")
@require_auth
def get_assignment(assignment_id):
    db = current_app.config["DB"]
    return jsonify(assignment_service.get_assignment_or_404(db, assignment_id))


@assignment_bp.put("/<assignment_id>")
@require_auth
@require_role("teacher")
def update_assignment(assignment_id):
    data = request.get_json(silent=True) or {}
    db = current_app.config["DB"]
    assignment = assignment_service.update_assignment(db, g.current_user["user_id"], assignment_id, data)
    return jsonify(assignment)


@assignment_bp.delete("/<assignment_id>")
@require_auth
@require_role("teacher")
def delete_assignment(assignment_id):
    db = current_app.config["DB"]
    assignment_service.delete_assignment(db, g.current_user["user_id"], assignment_id)
    return jsonify({"message": "Assignment deleted."})
