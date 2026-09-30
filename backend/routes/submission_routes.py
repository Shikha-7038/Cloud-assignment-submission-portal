"""
SUBMISSION + FILE endpoints
  POST /api/assignments/<id>/submit         (student)  submitAssignment / resubmitAssignment
  GET  /api/submissions/me                  (student)  getMySubmissions
  GET  /api/assignments/<id>/submissions    (teacher)  view submissions for an assignment
  GET  /api/submissions/<id>                (owner)    view one submission
  GET  /api/submissions/<id>/download       (owner)    downloadSubmission
"""
from flask import Blueprint, Response, current_app, g, jsonify, request

from backend.middleware.auth_middleware import require_auth, require_role
from backend.services import submission_service
from backend.utils.errors import BadRequest

submission_bp = Blueprint("submissions", __name__, url_prefix="/api")


@submission_bp.post("/assignments/<assignment_id>/submit")
@require_auth
@require_role("student")
def submit_assignment(assignment_id):
    if "file" not in request.files:
        raise BadRequest("No file part in the request.", code="NO_FILE")
    file = request.files["file"]
    data = file.read()

    db = current_app.config["DB"]
    storage = current_app.config["STORAGE"]
    submission = submission_service.submit_assignment(
        db, storage, g.current_user["user_id"], assignment_id, file.filename, data)
    return jsonify(submission), 201


@submission_bp.get("/submissions/me")
@require_auth
@require_role("student")
def my_submissions():
    db = current_app.config["DB"]
    return jsonify(submission_service.get_my_submissions(db, g.current_user["user_id"]))


@submission_bp.get("/assignments/<assignment_id>/submissions")
@require_auth
@require_role("teacher")
def submissions_for_assignment(assignment_id):
    db = current_app.config["DB"]
    return jsonify(submission_service.get_submissions_for_assignment(db, g.current_user["user_id"], assignment_id))


@submission_bp.get("/submissions/<submission_id>")
@require_auth
def get_submission(submission_id):
    db = current_app.config["DB"]
    return jsonify(submission_service.get_submission_with_access_check(db, g.current_user, submission_id))


@submission_bp.get("/submissions/<submission_id>/download")
@require_auth
def download_submission(submission_id):
    db = current_app.config["DB"]
    storage = current_app.config["STORAGE"]
    submission = submission_service.get_submission_with_access_check(db, g.current_user, submission_id)
    data = submission_service.download_submission_file(db, storage, g.current_user, submission_id)
    return Response(
        data, mimetype="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{submission["file_name"]}"'},
    )
