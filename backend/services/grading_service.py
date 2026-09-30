"""Feedback & grading system (teacher grades, student later reads - read only)."""
from cloud import database_service as dbs
from backend.utils.errors import BadRequest, Forbidden, NotFound
from backend.utils.time_utils import to_iso, utcnow


def grade_submission(db, teacher_id: str, submission_id: str, marks: float, feedback: str):
    submission = dbs.get_submission(db, submission_id)
    if not submission:
        raise NotFound("Submission not found.")
    assignment = dbs.get_assignment(db, submission["assignment_id"])
    if not assignment or assignment["created_by"] != teacher_id:
        raise Forbidden("Only the teacher who owns this assignment can grade it.", code="NOT_ASSIGNMENT_OWNER")

    if marks is None:
        raise BadRequest("Marks are required.")
    marks = float(marks)
    if marks < 0:
        raise BadRequest("Marks cannot be negative.")
    if marks > assignment["max_marks"]:
        raise BadRequest(f"Marks cannot exceed the maximum of {assignment['max_marks']}.", code="MARKS_EXCEED_MAX")
    if not feedback or not feedback.strip():
        raise BadRequest("Written feedback is required.")

    dbs.grade_submission(db, submission_id, marks, feedback.strip(), teacher_id, to_iso(utcnow()))
    return dbs.get_submission(db, submission_id)


def get_feedback(db, user: dict, submission_id: str):
    from backend.services.submission_service import get_submission_with_access_check
    submission = get_submission_with_access_check(db, user, submission_id)
    return {
        "submission_id": submission["submission_id"],
        "status": submission["submission_status"],
        "marks": submission["marks"],
        "feedback": submission["feedback"],
        "graded_at": submission["graded_at"],
    }
