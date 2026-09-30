"""
FEEDBACK / GRADING endpoints
  POST /api/submissions/<id>/grade      (teacher)  gradeSubmission
  GET  /api/submissions/<id>/feedback   (owner)    getSubmissionFeedback
"""
from flask import Blueprint, current_app, g, jsonify, request

from backend.middleware.auth_middleware import require_auth, require_role
from backend.services import grading_service

grading_bp = Blueprint("grading", __name__, url_prefix="/api")


@grading_bp.post("/submissions/<submission_id>/grade")
@require_auth
@require_role("teacher")
def grade_submission(submission_id):
    data = request.get_json(silent=True) or {}
    db = current_app.config["DB"]
    submission = grading_service.grade_submission(
        db, g.current_user["user_id"], submission_id, data.get("marks"), data.get("feedback"))
    return jsonify(submission)


@grading_bp.get("/submissions/<submission_id>/feedback")
@require_auth
def get_feedback(submission_id):
    db = current_app.config["DB"]
    return jsonify(grading_service.get_feedback(db, g.current_user, submission_id))
