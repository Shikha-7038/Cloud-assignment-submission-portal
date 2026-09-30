# Project Report: Cloud-Based Student Assignment Submission & Feedback Portal

*Cloud Computing Course Project*

## 1. Abstract

This project implements a cloud-based portal for submitting, tracking, and
grading student assignments. Teachers create assignments with deadlines and
file-type rules; students upload their work, which is validated and stored
in cloud object storage while structured metadata (submission time,
version, grade, feedback) is written to a cloud database. Teachers review
and grade submissions; students view marks and feedback on a dashboard. The
system is built to run identically against free local resources (SQLite,
local disk) or a managed cloud backend (PostgreSQL and object storage via
Supabase), demonstrating cloud database design, object storage design,
authentication and role-based authorization, REST API design, and cloud
deployment — all with a working, tested implementation rather than a
conceptual mockup.

## 2. Introduction

### 2.1 Problem Statement
Manual and semi-digital assignment workflows (email attachments, physical
hand-ins, shared drives with no access control) do not scale past a small
class, give no reliable record of submission time, and make feedback easy
to lose track of on both sides.

### 2.2 Objectives
1. Provide students a single, authenticated place to submit and track
   assignments and read feedback.
2. Provide teachers a single place to post assignments, review submissions,
   and grade them.
3. Demonstrate, with working code, the core cloud computing concepts
   covered in the course: cloud database vs. object storage, authentication
   vs. authorization, REST API design, deployment, security, and
   scalability considerations.

### 2.3 Scope
In scope: account registration and login, role-based access, assignment
CRUD, file upload with validation, deadline/late-submission logic,
resubmission/versioning, grading and feedback, dashboards for both roles,
local and cloud deployment paths. Out of scope (see `docs/README.md`
limitations section): malware scanning, notifications, plagiarism
detection, an admin role.

## 3. Literature / Background

Learning Management Systems such as Google Classroom, Canvas, and Moodle
solve this same problem at institutional scale, using the same architectural
pattern this project implements at a smaller scale: an authenticated web
client, a REST or RPC API, a relational database for structured records,
and object storage for uploaded files. This project is a deliberately
smaller, from-scratch reimplementation of that pattern, built to make every
layer (auth, database, storage, API) visible and explainable rather than
hidden behind a third-party platform.

## 4. System Requirements

### 4.1 Functional Requirements
- Users can register as a student or teacher (teacher registration gated by
  an invite code) and log in.
- Teachers can create, edit, and delete assignments with a deadline,
  maximum marks, allowed file types, and a maximum file size.
- Students can upload a file against an assignment; the system validates
  file type, size, and actual content before accepting it.
- The system records whether a submission was on-time or late, based on
  the server clock.
- Students can resubmit where the teacher allows it; each resubmission is
  kept as a new version rather than overwriting the previous one.
- Teachers can view all submissions for their assignments, download files,
  and record marks and written feedback.
- Students can view their own submission history and any feedback received.
- Both roles have a dashboard summarizing their relevant activity.

### 4.2 Non-Functional Requirements
- **Security:** passwords hashed, JWT-based sessions with expiry and
  server-side revocation, role- and ownership-based authorization on every
  route, validated file uploads, no secrets in source control.
- **Reliability:** unexpected failures in the database or storage layer are
  caught centrally and returned as a clean error, never a raw stack trace.
- **Portability:** the same codebase runs against local, zero-cost
  resources or a managed cloud backend via configuration only.
- **Testability:** the core workflow (registration through grading and
  failure handling) is covered by an automated test suite.

## 5. System Design

### 5.1 Architecture
See `docs/ARCHITECTURE.md` for the full diagram. In summary: a React
frontend calls a Flask REST API, which is the only component permitted to
read or write the cloud database (`cloud/database_service.py`) or cloud
object storage (`cloud/storage_service.py`).

### 5.2 Database Design
Four tables — `users`, `courses`, `assignments`, `submissions` — plus a
`revoked_tokens` table supporting real logout. Full schema and indexing
rationale in `docs/ARCHITECTURE.md#database-design`.

### 5.3 Storage Design
Files are stored under a per-assignment, per-student, per-version path and
are never made publicly accessible — access is either mediated by an
authenticated API route (local mode) or a short-lived signed URL (cloud
mode). Full detail in `docs/ARCHITECTURE.md#cloud-storage-design`.

### 5.4 API Design
A resource-oriented REST API covering auth, courses, assignments,
submissions, grading, and dashboards. Full reference in
`docs/API_REFERENCE.md`.

## 6. Implementation

### 6.1 Technology Stack
React (Vite) frontend; Python/Flask backend; JWT-based authentication;
SQLite locally / PostgreSQL (Supabase) in the cloud; local disk / Supabase
Storage for files. Rationale for this specific stack over the beginner and
advanced alternatives is discussed in `docs/TECH_STACK_OPTIONS.md`.

### 6.2 Key Implementation Details
- **Deadline enforcement** always uses the server's clock
  (`backend/utils/time_utils.utcnow`), never a client-supplied timestamp,
  so a student cannot manipulate their device clock to avoid a late flag.
- **File validation** checks extension, size, *and* the file's actual byte
  content against its claimed type (`backend/utils/validators.py`), which
  catches a disguised file that a naive extension-only check would miss.
- **Resubmission** is implemented as versioning rather than overwrite, so
  grading history and the original submission are never silently lost.
- **Authorization** is checked twice per protected action where relevant:
  once for role (`require_role`) and again for resource ownership inside
  the service layer (e.g. a teacher can only grade assignments they
  created) — a valid teacher token alone is not sufficient to grade any
  arbitrary submission.
- **Provider-agnostic cloud layer**: `cloud/database_service.py` and
  `cloud/storage_service.py` both expose the same interface regardless of
  which backend (local or managed cloud) is configured, so the rest of the
  application — routes, services, middleware — never branches on
  environment.

## 7. Testing

25 required test cases were implemented as automated tests
(`tests/test_workflow.py`) and additionally verified live against a running
instance of the app via a standalone smoke test
(`tests/smoke_test.py`). All 25 passed. Full results table:
`docs/TESTING.md`.

## 8. Results

The system supports the complete assignment lifecycle end-to-end:
registration → course/assignment creation → submission (including invalid,
oversized, and late cases) → resubmission with versioning → teacher review
and grading (including a marks-above-maximum rejection) → student feedback
viewing → logout with real token revocation. Simulated storage and database
outages were confirmed to fail gracefully — returning a generic error to
the client while logging full detail server-side — rather than crashing or
leaking internal information.

## 9. Discussion

### 9.1 Challenges
Getting deadline logic right required deliberately distrusting any
client-supplied timestamp and centralizing "now" on the server. Getting
file validation right required going beyond extension checking to actual
content inspection, since a renamed file will pass an extension-only check.
Designing the cloud database/storage layer to be genuinely swappable
(rather than "local for now, rewrite later for cloud") required writing to
a fixed interface (`upload/download/get_access_url`,
`execute/fetchone/fetchall`) from the very first line of business logic.

### 9.2 Limitations
See `README.md#limitations` — no malware scanning, no notifications, and
dashboard aggregation is done in Python rather than SQL, which is
appropriate at student-project scale but is explicitly called out in
`docs/SCALABILITY.md` as something that would need to change at real scale.

## 10. Conclusion

The project demonstrates a complete, working cloud application covering
the full requested scope: a cloud database, cloud object storage,
authentication and role-based authorization, a REST API, a tested backend,
a functional frontend, and two documented deployment paths (free-tier and
AWS-mapped). It is built so that every "cloud computing concept" claimed
in the accompanying documentation is traceable to a specific, running line
of code rather than described only in the abstract.

## 11. Future Work

Plagiarism/similarity detection, deadline reminder notifications,
rubric-based grading with per-criterion marks, an admin role for course and
user management, CI/CD via GitHub Actions (workflow provided in
`docs/GITHUB_STRATEGY.md`), and moving dashboard aggregation to SQL-side
queries for larger-scale deployments.

## 12. References

- Flask documentation — flask.palletsprojects.com
- PyJWT documentation — pyjwt.readthedocs.io
- Supabase documentation — supabase.com/docs
- React documentation — react.dev
- OWASP file upload security guidance — owasp.org
