# REST API Reference

Base URL: `http://localhost:8000/api` locally, or your deployed backend URL.
Every response is JSON. Errors always look like:

```json
{ "error": { "code": "SOME_CODE", "message": "Human-readable explanation." } }
```

All routes except `/register`, `/login`, and `/health` require
`Authorization: Bearer <token>`.

## Auth

### `POST /register`
Create an account.

**Body:** `{ "name", "email", "password", "role": "student"|"teacher", "teacher_invite_code"? }`
**201:** `{ "user": {...}, "token": "..." }`
**Errors:** `400` invalid input, `401 INVALID_INVITE_CODE`, `409 EMAIL_TAKEN`

### `POST /login`
**Body:** `{ "email", "password" }`
**200:** `{ "user": {...}, "token": "..." }`
**Errors:** `401 INVALID_CREDENTIALS`, `429 RATE_LIMITED`

### `POST /logout` *(auth required)*
Revokes the current token immediately.
**200:** `{ "message": "Logged out successfully." }`

## Courses

### `POST /courses` *(teacher)*
**Body:** `{ "course_name" }` → **201** course object

### `GET /courses` *(any authenticated user)*
**200:** array of course objects

## Assignments

### `POST /assignments` *(teacher, must own the course)*
**Body:**
```json
{
  "course_id", "title", "description", "deadline": "ISO-8601",
  "max_marks": 100, "allowed_file_types": "pdf,docx",
  "max_file_size_mb": 10, "allow_resubmission": true, "reject_late": false
}
```
**201:** assignment object · **403** if the course isn't yours

### `GET /assignments` *(any authenticated user)*
Optional `?course_id=` filter. **200:** array of assignments.

### `GET /assignments/{id}` *(any authenticated user)*
**200:** assignment object · **404** if not found

### `PUT /assignments/{id}` *(teacher, creator only)*
Partial update — send only the fields you want to change.
**200:** updated assignment · **403** if you didn't create it

### `DELETE /assignments/{id}` *(teacher, creator only)*
Deletes the assignment and its submissions.
**200:** `{ "message": "Assignment deleted." }`

## Submissions

### `POST /assignments/{id}/submit` *(student)*
`multipart/form-data` with a `file` field.

**201:** submission object, `submission_status` is `SUBMITTED` or `LATE`
**Errors:**
- `404` assignment not found
- `415 INVALID_FILE_TYPE` / `415 FILE_CONTENT_MISMATCH` — extension not
  allowed, or the file's actual bytes don't match its extension
- `413 FILE_TOO_LARGE`
- `400 DEADLINE_PASSED` — late and the assignment rejects late work
- `409 ALREADY_SUBMITTED` — resubmission not allowed and one exists

### `GET /submissions/me` *(student)*
**200:** array of the caller's own submissions (all versions, all assignments)

### `GET /assignments/{id}/submissions` *(teacher, owner only)*
**200:** array of every submission for that assignment

### `GET /submissions/{id}` *(owner only — student who submitted it, or the teacher who owns the assignment)*
**200:** submission object · **403** otherwise

### `GET /submissions/{id}/download` *(owner only)*
**200:** raw file bytes, `Content-Disposition: attachment`

## Grading & Feedback

### `POST /submissions/{id}/grade` *(teacher, must own the assignment)*
**Body:** `{ "marks": number, "feedback": "string" }`
**200:** updated submission, `submission_status` becomes `GRADED`
**Errors:** `400` marks negative / above `max_marks` / feedback missing,
`403 NOT_ASSIGNMENT_OWNER`

### `GET /submissions/{id}/feedback` *(owner only)*
**200:** `{ "submission_id", "status", "marks", "feedback", "graded_at" }`

## Dashboards

### `GET /dashboard/student` *(student)*
**200:**
```json
{
  "total_assignments": 0, "pending_assignments": 0, "submitted_assignments": 0,
  "late_assignments": 0, "graded_assignments": 0,
  "upcoming_deadlines": [...], "recent_feedback": [...]
}
```

### `GET /dashboard/teacher` *(teacher)*
**200:**
```json
{
  "total_assignments": 0, "total_students": 0, "total_submissions": 0,
  "pending_reviews": 0, "late_submissions": 0, "graded_submissions": 0,
  "recent_uploads": [...], "upcoming_deadlines": [...]
}
```

## Misc

### `GET /health`
**200:** `{ "status": "ok", "cloud_provider": "local"|"supabase" }` — unauthenticated, safe for uptime monitors / load balancer health checks.

## Error Codes Reference

| Code | HTTP status | Meaning |
|---|---|---|
| `BAD_REQUEST` | 400 | Generic invalid input |
| `DEADLINE_PASSED` | 400 | Late submission rejected by assignment policy |
| `MARKS_EXCEED_MAX` | 400 | Marks entered above the assignment's max |
| `UNAUTHORIZED` | 401 | Missing/invalid Authorization header |
| `INVALID_CREDENTIALS` | 401 | Wrong email/password |
| `TOKEN_EXPIRED` / `TOKEN_INVALID` / `TOKEN_REVOKED` | 401 | JWT problems |
| `INVALID_INVITE_CODE` | 401 | Wrong teacher invite code at registration |
| `FORBIDDEN` / `ROLE_NOT_ALLOWED` | 403 | Authenticated but not permitted |
| `NOT_ASSIGNMENT_OWNER` | 403 | Teacher tried to grade someone else's assignment |
| `NOT_FOUND` | 404 | Resource doesn't exist |
| `EMAIL_TAKEN` | 409 | Duplicate registration |
| `ALREADY_SUBMITTED` | 409 | Resubmission not allowed |
| `FILE_TOO_LARGE` | 413 | Over the assignment's per-file limit |
| `INVALID_FILE_TYPE` / `FILE_CONTENT_MISMATCH` | 415 | Extension not allowed, or content doesn't match extension |
| `RATE_LIMITED` | 429 | Too many login attempts |
| `INTERNAL_ERROR` | 500 | Unexpected server/database/storage failure |
