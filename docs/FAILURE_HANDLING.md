# Failure Handling & Edge Cases

## Cloud storage temporarily unavailable
If `storage.upload(...)` raises (network blip, outage, bad credentials),
the exception propagates up through `submission_service.submit_assignment`
uncaught by business logic, and is caught by the global handler in
`backend/middleware/error_handler.py`, which:
1. Logs the full exception server-side (`logger.exception(...)`).
2. Returns a generic `500 INTERNAL_ERROR` with a friendly message —
   never the exception text or a stack trace.

Crucially, because the storage upload happens *before* the database write
in `submission_service.submit_assignment`, a storage failure means **no
database row is ever created** for that attempt — there's no dangling
metadata pointing at a file that doesn't exist. Verified in
`tests/test_workflow.py::test_storage_failure_returns_clean_error`.

## Cloud database temporarily unavailable
Same handler, same behavior — verified in
`tests/test_workflow.py::test_database_failure_returns_clean_error`. If the
database write fails *after* a successful storage upload, the file bytes
exist in storage but no submission row references them yet; a retried
upload simply creates a new object at a new version path rather than
colliding with the orphaned one. A production system at larger scale would
add a periodic cleanup job for orphaned objects with no matching database
row, but this is out of scope for a student-project deployment.

## Duplicate / accidental double submission
Handled by the **version** system, not by silently rejecting a second
click: `get_submission_for_student_assignment` finds the highest existing
version for that student+assignment and the new upload becomes
`version + 1`. If the assignment's `allow_resubmission` is `False` and a
submission already exists, the second attempt is rejected with
`409 ALREADY_SUBMITTED` rather than silently overwriting the first.

## Late submissions
Governed entirely by the server clock (`backend/utils/time_utils.utcnow`),
never a client-supplied timestamp. Two policies:
- `reject_late = False` (default): late work is still accepted, but stored
  with `submission_status = "LATE"` so the teacher can see it was late.
- `reject_late = True`: the upload is rejected outright with
  `400 DEADLINE_PASSED` before anything is written anywhere.

## Invalid or disguised file uploads
Rejected before storage or database ever see the bytes:
- Extension not in the assignment's allow-list → `415 INVALID_FILE_TYPE`.
- File larger than the assignment's (or the hard 25MB) limit →
  `413 FILE_TOO_LARGE`.
- File content doesn't match its claimed extension (e.g. a `.pdf` that
  isn't really a PDF) → `415 FILE_CONTENT_MISMATCH`.

## Unauthorized access attempts
- Wrong role for a route → `403 FORBIDDEN` / `403 ROLE_NOT_ALLOWED`.
- Right role, wrong owner (a teacher trying to grade another teacher's
  assignment; a student trying to view another student's submission) →
  `403` from the ownership check inside the relevant service function, not
  just the role decorator.
- Expired, tampered, or logged-out token → `401` with a specific code
  (`TOKEN_EXPIRED` / `TOKEN_INVALID` / `TOKEN_REVOKED`) so the frontend can
  distinguish "please log in again" from "you're not allowed to do that."

## Marks outside valid range
`grading_service.grade_submission` rejects negative marks and marks above
the assignment's `max_marks` with `400`, and requires non-empty written
feedback — a grade cannot be saved as "just a number" with no explanation.

## Concurrent grading (two teachers, one submission)
Not currently guarded with optimistic locking — the last write wins, same
as most simple CRUD systems at this scale. A production system with
multiple graders per course would add a `graded_by` conflict check or a
version/`updated_at` compare-and-swap before applying a second grade write.
Documented here as a known limitation rather than silently glossed over.

## What "graceful" means in this codebase, concretely
Every failure path in this document returns a JSON body in the same shape
(`{"error": {"code", "message"}}`) with an appropriate HTTP status — the
frontend's `services/api.js` reads `error.message` uniformly regardless of
which failure occurred, so error handling in the UI is a single code path,
not a special case per endpoint.
