"""Assignment management (teacher-side): create, update, delete, list."""
from cloud import database_service as dbs
from backend.utils.errors import BadRequest, Forbidden, NotFound
from backend.utils.time_utils import parse_dt, to_iso, utcnow
from backend.utils.validators import ALLOWED_EXTENSIONS


def _validate_fields(title, deadline_str, max_marks, allowed_file_types, max_file_size_mb):
    if not title or not title.strip():
        raise BadRequest("Assignment title is required.")
    try:
        deadline = parse_dt(deadline_str)
    except Exception:
        raise BadRequest("Deadline must be a valid ISO-8601 date/time.")
    if max_marks is None or float(max_marks) <= 0:
        raise BadRequest("Maximum marks must be a positive number.")
    types = [t.strip().lower() for t in (allowed_file_types or "pdf,docx").split(",") if t.strip()]
    if not types:
        raise BadRequest("At least one allowed file type is required.")
    for t in types:
        if t not in ALLOWED_EXTENSIONS:
            raise BadRequest(f"File type '.{t}' is not supported by this portal.")
    if max_file_size_mb is None or int(max_file_size_mb) <= 0:
        raise BadRequest("Maximum file size must be a positive number of MB.")
    return deadline, types


def create_assignment(db, teacher_id: str, course_id: str, title: str, description: str, deadline_str: str,
                       max_marks: float, allowed_file_types: str, max_file_size_mb: int,
                       allow_resubmission: bool = True, reject_late: bool = False):
    course = dbs.get_course(db, course_id)
    if not course:
        raise NotFound("Course not found.")
    if course["teacher_id"] != teacher_id:
        raise Forbidden("You can only create assignments for your own course.")
    deadline, types = _validate_fields(title, deadline_str, max_marks, allowed_file_types, max_file_size_mb)
    return dbs.create_assignment(
        db, course_id=course_id, title=title.strip(), description=(description or "").strip(),
        deadline=to_iso(deadline), max_marks=float(max_marks), allowed_file_types=",".join(types),
        max_file_size_mb=int(max_file_size_mb), allow_resubmission=bool(allow_resubmission),
        reject_late=bool(reject_late), created_by=teacher_id,
    )


def update_assignment(db, teacher_id: str, assignment_id: str, updates: dict):
    assignment = dbs.get_assignment(db, assignment_id)
    if not assignment:
        raise NotFound("Assignment not found.")
    if assignment["created_by"] != teacher_id:
        raise Forbidden("You can only edit assignments you created.")

    clean = {}
    if "title" in updates:
        if not updates["title"].strip():
            raise BadRequest("Title cannot be empty.")
        clean["title"] = updates["title"].strip()
    if "description" in updates:
        clean["description"] = updates["description"]
    if "deadline" in updates:
        clean["deadline"] = to_iso(parse_dt(updates["deadline"]))
    if "max_marks" in updates:
        if float(updates["max_marks"]) <= 0:
            raise BadRequest("Maximum marks must be positive.")
        clean["max_marks"] = float(updates["max_marks"])
    if "allowed_file_types" in updates:
        types = [t.strip().lower() for t in updates["allowed_file_types"].split(",") if t.strip()]
        for t in types:
            if t not in ALLOWED_EXTENSIONS:
                raise BadRequest(f"File type '.{t}' is not supported.")
        clean["allowed_file_types"] = ",".join(types)
    if "max_file_size_mb" in updates:
        if int(updates["max_file_size_mb"]) <= 0:
            raise BadRequest("Maximum file size must be positive.")
        clean["max_file_size_mb"] = int(updates["max_file_size_mb"])
    if "allow_resubmission" in updates:
        clean["allow_resubmission"] = int(bool(updates["allow_resubmission"]))
    if "reject_late" in updates:
        clean["reject_late"] = int(bool(updates["reject_late"]))

    dbs.update_assignment(db, assignment_id, clean)
    return dbs.get_assignment(db, assignment_id)


def delete_assignment(db, teacher_id: str, assignment_id: str):
    assignment = dbs.get_assignment(db, assignment_id)
    if not assignment:
        raise NotFound("Assignment not found.")
    if assignment["created_by"] != teacher_id:
        raise Forbidden("You can only delete assignments you created.")
    dbs.delete_assignment(db, assignment_id)


def get_assignment_or_404(db, assignment_id: str):
    assignment = dbs.get_assignment(db, assignment_id)
    if not assignment:
        raise NotFound("Assignment not found.")
    return assignment


def list_assignments(db, course_id: str = None):
    return dbs.list_assignments(db, course_id)
