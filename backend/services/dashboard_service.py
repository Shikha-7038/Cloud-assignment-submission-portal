"""
Dashboard queries. Kept deliberately simple (Python-side aggregation over a
handful of rows) since this is a small student project; at real scale these
would become indexed SQL GROUP BY queries or a scheduled analytics job
(see the ChatGPT-regeneration note in the original brief about a
scheduled Cloud Function aggregating an /analytics collection).
"""
from cloud import database_service as dbs
from backend.utils.time_utils import parse_dt, utcnow


def student_dashboard(db, student_id: str):
    assignments = dbs.list_assignments(db)
    # Keep only the LATEST version per assignment (a student may have several
    # submission rows for one assignment after resubmitting).
    my_subs = {}
    for s in dbs.list_submissions_for_student(db, student_id):
        existing = my_subs.get(s["assignment_id"])
        if existing is None or s["version"] > existing["version"]:
            my_subs[s["assignment_id"]] = s
    now = utcnow()

    total = len(assignments)
    submitted = late = graded = pending = 0
    upcoming = []
    recent_feedback = []

    for a in assignments:
        sub = my_subs.get(a["assignment_id"])
        if not sub:
            pending += 1
            if parse_dt(a["deadline"]) > now:
                upcoming.append({"assignment_id": a["assignment_id"], "title": a["title"], "deadline": a["deadline"]})
        else:
            if sub["submission_status"] == "GRADED":
                graded += 1
                recent_feedback.append({
                    "assignment_title": a["title"], "marks": sub["marks"],
                    "feedback": sub["feedback"], "graded_at": sub["graded_at"],
                })
            elif sub["submission_status"] == "LATE":
                late += 1
            else:
                submitted += 1

    upcoming.sort(key=lambda x: x["deadline"])
    recent_feedback.sort(key=lambda x: x["graded_at"] or "", reverse=True)
    return {
        "total_assignments": total,
        "pending_assignments": pending,
        "submitted_assignments": submitted,
        "late_assignments": late,
        "graded_assignments": graded,
        "upcoming_deadlines": upcoming[:5],
        "recent_feedback": recent_feedback[:5],
    }


def teacher_dashboard(db, teacher_id: str):
    courses = [c for c in dbs.list_courses(db) if c["teacher_id"] == teacher_id]
    course_ids = {c["course_id"] for c in courses}
    assignments = [a for a in dbs.list_assignments(db) if a["course_id"] in course_ids]

    all_subs = []
    for a in assignments:
        all_subs.extend(dbs.list_submissions_for_assignment(db, a["assignment_id"]))

    student_ids = {s["student_id"] for s in all_subs}
    pending_review = [s for s in all_subs if s["submission_status"] in ("SUBMITTED", "LATE")]
    late = [s for s in all_subs if s["submission_status"] == "LATE"]
    graded = [s for s in all_subs if s["submission_status"] == "GRADED"]
    recent = sorted(all_subs, key=lambda s: s["submitted_at"], reverse=True)[:5]

    now = utcnow()
    upcoming = sorted(
        [{"assignment_id": a["assignment_id"], "title": a["title"], "deadline": a["deadline"]}
         for a in assignments if parse_dt(a["deadline"]) > now],
        key=lambda x: x["deadline"],
    )[:5]

    return {
        "total_assignments": len(assignments),
        "total_students": len(student_ids),
        "total_submissions": len(all_subs),
        "pending_reviews": len(pending_review),
        "late_submissions": len(late),
        "graded_submissions": len(graded),
        "recent_uploads": [
            {"submission_id": s["submission_id"], "file_name": s["file_name"], "submitted_at": s["submitted_at"]}
            for s in recent
        ],
        "upcoming_deadlines": upcoming,
    }
