# Architecture

## System Architecture Diagram

```
                    ┌─────────────────────────┐
                    │   Browser (Student /     │
                    │   Teacher)                │
                    └────────────┬──────────────┘
                                 │ HTTPS
                    ┌────────────▼──────────────┐
                    │  React Frontend (Vite)     │
                    │  frontend/src/             │
                    │  - pages/  (routed screens)│
                    │  - services/api.js         │
                    │    (fetch wrapper + JWT)   │
                    └────────────┬──────────────┘
                                 │ REST (JSON / multipart)
                    ┌────────────▼──────────────┐
                    │  Flask REST API            │
                    │  backend/                  │
                    │  - routes/   (HTTP layer)  │
                    │  - middleware/ (auth, err) │
                    │  - services/ (business     │
                    │    logic, validation)      │
                    └──────┬───────────────┬─────┘
                           │               │
              ┌────────────▼───┐   ┌───────▼─────────────┐
              │ Cloud Database  │   │ Cloud Object Storage │
              │ cloud/          │   │ cloud/               │
              │ database_       │   │ storage_service.py   │
              │ service.py      │   │                      │
              │                 │   │ Local: disk folder    │
              │ Local: SQLite   │   │ Cloud: Supabase       │
              │ Cloud: Postgres │   │        Storage (S3-   │
              │        (Supabase)│  │        compatible)   │
              └─────────────────┘   └──────────────────────┘
```

The frontend never talks to the database or storage directly — only to the
REST API, which is the single enforcement point for both authentication and
authorization.

## User Roles & Permissions

| Endpoint | Student | Teacher | Anyone authenticated |
|---|---|---|---|
| `POST /api/register`, `/api/login` | ✅ | ✅ | — (public) |
| `POST /api/courses` | ❌ 403 | ✅ | — |
| `GET /api/courses` | — | — | ✅ |
| `POST /api/assignments` | ❌ 403 | ✅ (own course only) | — |
| `GET /api/assignments`, `/api/assignments/{id}` | — | — | ✅ |
| `PUT` / `DELETE /api/assignments/{id}` | ❌ 403 | ✅ (creator only) | — |
| `POST /api/assignments/{id}/submit` | ✅ | ❌ 403 | — |
| `GET /api/submissions/me` | ✅ | ❌ 403 | — |
| `GET /api/assignments/{id}/submissions` | ❌ 403 | ✅ (own assignment only) | — |
| `GET /api/submissions/{id}` | ✅ (own submission only) | ✅ (own assignment only) | — |
| `GET /api/submissions/{id}/download` | ✅ (own only) | ✅ (own assignment only) | — |
| `POST /api/submissions/{id}/grade` | ❌ 403 | ✅ (own assignment only) | — |
| `GET /api/submissions/{id}/feedback` | ✅ (own only) | ✅ (own assignment only) | — |
| `GET /api/dashboard/student` | ✅ | ❌ 403 | — |
| `GET /api/dashboard/teacher` | ❌ 403 | ✅ | — |

"Own only" checks happen in `backend/services/*.py`, not just at the route
level — e.g. `submission_service.get_submission_with_access_check` compares
`submission["student_id"]` against the caller's id for students, and the
owning teacher's id for teachers, before returning anything.

## Database Design

Implemented in `cloud/database_service.py` (schema in the `_SCHEMA` constant).

```
users
├── user_id (PK)
├── name
├── email (unique)
├── password_hash
├── role            student | teacher
└── created_at

courses
├── course_id (PK)
├── course_name
├── teacher_id (FK → users.user_id)
└── created_at

assignments
├── assignment_id (PK)
├── course_id (FK → courses.course_id)
├── title
├── description
├── deadline               ISO-8601 UTC string
├── max_marks
├── allowed_file_types     comma-separated, e.g. "pdf,docx"
├── max_file_size_mb
├── allow_resubmission     bool
├── reject_late            bool
├── created_by (FK → users.user_id)
└── created_at

submissions
├── submission_id (PK)
├── assignment_id (FK → assignments.assignment_id)
├── student_id (FK → users.user_id)
├── file_name
├── file_url               reference only — see Cloud Storage Design below
├── storage_path            actual object-storage key
├── version                 1, 2, 3... per resubmission
├── submitted_at
├── submission_status       SUBMITTED | LATE | GRADED
├── marks
├── feedback
├── graded_at
└── graded_by (FK → users.user_id)

revoked_tokens
├── token_hash (PK)         SHA-256 of a logged-out JWT, never the raw token
└── revoked_at
```

**Indexes:** `assignments.course_id`, `submissions.assignment_id`,
`submissions.student_id` are all indexed, since "list assignments for a
course," "list submissions for an assignment," and "list a student's
submissions" are the three hottest read queries in the system.

**Why a `version` column instead of overwriting on resubmission:** grading
history and the original file both need to survive a resubmission —
`get_submission_for_student_assignment` reads the highest version to decide
the next one, so nothing is ever destructively overwritten.

## Cloud Storage Design

Implemented in `cloud/storage_service.py`.

**Path convention:**
```
assignments/{assignment_id}/{student_id}/{version}_{filename}
```
This keeps every student's submissions to a given assignment grouped
together, versioned, and namespaced so two students uploading a file with
an identical name never collide.

**Access model:**
- *Local mode:* there is no route that serves the upload folder as static
  files. The only way to read a file's bytes is
  `GET /api/submissions/{id}/download`, which re-checks ownership on every
  call before reading from disk.
- *Cloud mode (Supabase Storage):* the bucket is private; uploads go through
  the service-role key server-side, and downloads use a **signed URL**
  (`SupabaseStorageBackend.get_access_url`) that expires after
  `SIGNED_URL_EXPIRE_SECONDS` (default 300s) — so a link can't be shared or
  bookmarked for permanent access.

**Why files never touch the database:** see
`docs/PROJECT_EXPLANATION.md#why-assignment-files-belong-in-object-storage-not-the-database`.

## Assignment & Submission Workflow (detailed)

```
1. Select Assignment     student picks from GET /api/assignments
2. Select File            <input type="file"> in AssignmentDetail.jsx
3. Validate File           backend/utils/validators.py: extension, size,
                            AND real file content (magic bytes) — not just
                            what the filename claims
4. Check deadline           backend/utils/time_utils.is_late() using the
                            SERVER clock, never a value from the browser
5. Check resubmission rule  reject with 409 if already submitted and
                            allow_resubmission is False
6. Upload to Cloud Storage  cloud/storage_service.py .upload()
7. Get Storage Reference    StoredFile(storage_path, file_url)
8. Save Submission Metadata cloud/database_service.py create_submission()
9. Confirmation              201 response with the full submission record
```

If step 6 (storage) or step 8 (database write) fails, the exception is
caught by `backend/middleware/error_handler.py` and turned into a generic
500 — the student sees "something went wrong, try again," not a stack
trace or a half-written record silently treated as success. See
`docs/FAILURE_HANDLING.md` for how partial-failure scenarios are handled.

## Deadline Logic

`backend/utils/time_utils.py`:

```python
def is_late(submitted_at, deadline) -> bool:
    return parse_dt(submitted_at) > parse_dt(deadline)
```

The submission's timestamp is generated server-side at the moment the
upload is processed (`utcnow()` inside `submission_service.submit_assignment`)
— never taken from a value the client could send. A student changing their
device's clock cannot make a late submission look on-time.

If `assignment.reject_late` is `True`, a late upload is rejected outright
with `400 DEADLINE_PASSED` rather than silently accepted and marked `LATE`.
