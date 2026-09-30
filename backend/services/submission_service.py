"""
Assignment submission system (student-side).

Workflow implemented end to end, matching the brief exactly:

  Select Assignment -> Select File -> Validate File -> Upload to Cloud Storage
  -> Get Storage Reference -> Save Submission Metadata -> Confirmation

Every rule from the brief is enforced here, server-side, so a student cannot
bypass any of it by editing the browser:
  - student authentication         (enforced by the route's @require_auth)
  - assignment existence
  - deadline (server clock only - see backend/utils/time_utils.is_late)
  - file extension + size + real file content (validators.validate_upload)
  - duplicate/resubmission policy
"""
from cloud import database_service as dbs
from cloud import storage_service
from backend.utils.errors import BadRequest, Conflict, Forbidden, NotFound
from backend.utils.time_utils import is_late, to_iso, utcnow
from backend.utils.validators import validate_upload


def submit_assignment(db, storage, student_id: str, assignment_id: str, filename: str, data: bytes):
    assignment = dbs.get_assignment(db, assignment_id)
    if not assignment:
        raise NotFound("Assignment not found.")

    allowed_types = assignment["allowed_file_types"].split(",")
    safe_name, ext, _content_type = validate_upload(filename, data, allowed_types, assignment["max_file_size_mb"])

    now = utcnow()
    late = is_late(now, assignment["deadline"])
    if late and assignment["reject_late"]:
        raise BadRequest(
            "The deadline for this assignment has passed and late submissions are not accepted.",
            code="DEADLINE_PASSED",
        )

    previous = dbs.get_submission_for_student_assignment(db, assignment_id, student_id)
    if previous and not assignment["allow_resubmission"]:
        raise Conflict("You have already submitted this assignment and resubmission is not allowed.",
                        code="ALREADY_SUBMITTED")
    next_version = (previous["version"] + 1) if previous else 1

    stored = storage.upload(assignment_id, student_id, next_version, safe_name, data)
    submission = dbs.create_submission(
        db,
        assignment_id=assignment_id,
        student_id=student_id,
        file_name=safe_name,
        file_url=stored.file_url,
        storage_path=stored.storage_path,
        version=next_version,
        submitted_at=to_iso(now),
        submission_status="LATE" if late else "SUBMITTED",
    )
    return submission


def get_my_submissions(db, student_id: str):
    return dbs.list_submissions_for_student(db, student_id)


def get_submissions_for_assignment(db, teacher_id: str, assignment_id: str):
    assignment = dbs.get_assignment(db, assignment_id)
    if not assignment:
        raise NotFound("Assignment not found.")
    if assignment["created_by"] != teacher_id:
        raise Forbidden("You can only view submissions for your own assignments.")
    return dbs.list_submissions_for_assignment(db, assignment_id)


def get_submission_with_access_check(db, user: dict, submission_id: str):
    """A student may only see their OWN submission; a teacher may only see
    submissions for an assignment THEY created. This is the check that stops
    'Student cannot view another student's private submission'."""
    submission = dbs.get_submission(db, submission_id)
    if not submission:
        raise NotFound("Submission not found.")
    if user["role"] == "student":
        if submission["student_id"] != user["user_id"]:
            raise Forbidden("You can only view your own submissions.")
    elif user["role"] == "teacher":
        assignment = dbs.get_assignment(db, submission["assignment_id"])
        if not assignment or assignment["created_by"] != user["user_id"]:
            raise Forbidden("You can only view submissions for your own assignments.")
    return submission


def download_submission_file(db, storage, user: dict, submission_id: str) -> bytes:
    submission = get_submission_with_access_check(db, user, submission_id)
    return storage.download(submission["storage_path"])
