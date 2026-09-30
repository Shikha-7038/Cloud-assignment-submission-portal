# Cloud-Based Student Assignment Submission & Feedback Portal

A cloud-hosted portal where teachers create assignments and students submit
work, with file storage, deadline tracking, grading, and feedback all backed
by cloud infrastructure — buildable entirely on free-tier or local resources.

> Full write-ups for every topic below live in [`docs/`](docs) and
> [`reports/`](reports). This README is the map.

## Overview

Students upload assignment files through a web app; the files land in cloud
object storage while structured records (who submitted what, when, graded
how) live in a cloud database. Teachers review submissions, assign marks,
and leave written feedback that students see on their own dashboard. Every
piece — auth, storage, database, deployment — is built the way a real SaaS
product would build it, just sized for a student project and a free tier.

## Problem Statement

Paper submissions and emailed attachments get lost, are hard to search, and
give no reliable audit trail of who submitted what and when. Manually
tracking deadlines and feedback across a class does not scale past a
handful of students. This project replaces that with one authenticated,
centrally stored system both sides can trust.

## Live demo:
 https://cloud-assignment-submission-portal-red.vercel.app

## Objectives

- Give students one place to submit, track, and get feedback on assignments.
- Give teachers one place to set deadlines, review work, and grade it.
- Demonstrate real cloud computing concepts (not just a file-upload form):
  cloud database, object storage, authentication, authorization, REST APIs,
  deployment, security, and scalability.

## Features

**Teachers:** create/edit/delete assignments, set deadlines and file-type
rules, view all submissions for an assignment, download files, enter marks
and feedback, see a live dashboard of pending reviews and late work.

**Students:** register/log in, browse assignments, upload work (multiple
formats), resubmit where the teacher allows it, track submission status,
view marks and feedback, re-download anything they've submitted.

## User Roles

| Capability | Student | Teacher |
|---|---|---|
| Register / log in | ✅ | ✅ (invite-code gated) |
| Create / edit / delete assignments | ❌ | ✅ |
| Upload / resubmit own work | ✅ | — |
| View own submissions & marks | ✅ | — |
| View all submissions for their assignments | ❌ | ✅ |
| Grade & write feedback | ❌ | ✅ |
| View another student's submission | ❌ | only for their own courses |

Full permission table: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#user-roles--permissions).

## Cloud Computing Concepts

Cloud database, object storage, authentication/authorization, RBAC, REST
APIs, client-server architecture, scalability/elasticity, signed URLs,
environment-based secrets, logging, and CI/CD-ready structure are all
demonstrated in this codebase. Where each concept physically lives in the
code is mapped out in [`docs/CLOUD_CONCEPTS.md`](docs/CLOUD_CONCEPTS.md).

## Architecture

```
Student / Teacher
      ↓
React Web App  (frontend/)
      ↓
REST API — Flask  (backend/)
      ↓
  ┌───┴────┐
  ↓        ↓
Cloud DB  Object Storage   (cloud/database_service.py, cloud/storage_service.py)
  ↓
Logging / Monitoring
```

Local mode = SQLite + a disk folder, zero setup. Cloud mode = PostgreSQL
(e.g. Supabase) + Supabase Storage, same code, different `.env`. Full
diagrams: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | Python, Flask, REST APIs |
| Auth | JWT (PyJWT) + salted password hashing |
| Database | SQLite (local) / PostgreSQL via Supabase (cloud) |
| Object storage | Local disk (local) / Supabase Storage (cloud) |
| Testing | pytest |

Three build options (beginner/local, recommended cloud, advanced cloud) are
compared in [`docs/TECH_STACK_OPTIONS.md`](docs/TECH_STACK_OPTIONS.md).

## Database Design

`users → courses → assignments → submissions`, with submissions holding a
`storage_path`/`file_url` pointer rather than the file itself. Full schema,
keys, and indexing notes: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#database-design).

## Cloud Storage

Files are stored under `assignments/{assignment_id}/{student_id}/{version}_{filename}`,
served only through an authenticated download route (local mode) or a
short-lived signed URL (cloud mode) — never a public link. Details:
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#cloud-storage-design).

## Authentication & Authorization

Authentication ("who are you?") is JWT-based login; authorization ("what
can you do?") is a role claim inside that same token, checked on every
route by `backend/middleware/auth_middleware.py`. See
[`docs/SECURITY.md`](docs/SECURITY.md).

## Assignment & Submission Workflow

```
Select Assignment → Select File → Validate File → Upload to Cloud Storage
→ Get Storage Reference → Save Submission Metadata → Confirmation
```

Deadline logic, resubmission/versioning, and duplicate-submission handling
are covered in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#deadline-logic).

## Feedback & Grading

Teachers grade with marks capped at the assignment maximum and required
written feedback; students get read-only access to both. See
`backend/services/grading_service.py`.

## REST APIs

All endpoints, methods, auth requirements, and status codes are documented
in [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md).

## Folder Structure

```
Cloud-Assignment-Submission-Portal/
├── frontend/          React app (Vite)
├── backend/           Flask app: routes, services, middleware, utils
├── cloud/             The three cloud abstractions: database, storage, auth
├── tests/             pytest suite + a standalone smoke test
├── sample_files/      Dummy PDFs for manual testing
├── screenshots/        Where to save proof-of-work screenshots (see docs/GITHUB_STRATEGY.md)
├── docs/              Deep-dive write-ups referenced from this README
├── reports/           Formal project report, resume/interview material
├── requirements.txt   Backend Python dependencies
├── .env.example        Copy to .env and fill in
└── .gitignore
```

## Installation & Local Setup

```bash
# 1. Clone and enter the project
git clone https://github.com/<you>/Cloud-Based-Assignment-Submission-Portal.git
cd Cloud-Based-Assignment-Submission-Portal

# 2. Backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # defaults already work for local mode
python -m backend.app            # serves http://localhost:8000

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev                      # serves http://localhost:5173
```

Full click-by-click walkthrough (create accounts, post an assignment,
submit, grade): [`docs/LOCAL_SETUP_WALKTHROUGH.md`](docs/LOCAL_SETUP_WALKTHROUGH.md).

## Environment Variables

See [`.env.example`](.env.example) for the full list with comments. Nothing
sensitive is ever hardcoded — `backend/config.py` reads everything from the
environment and refuses to start in production without a real `SECRET_KEY`.

## Testing

```bash
PYTHONPATH=. pytest tests/ -v
```

25 required test cases (registration through failure handling) are
implemented in `tests/test_workflow.py`; the table version with expected
vs. actual results is in [`docs/TESTING.md`](docs/TESTING.md).

## Cloud Deployment

Two paths are documented in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md):
a free-tier path (Vercel/Render + Supabase) and an AWS-mapped path
(S3/CloudFront, App Runner or Lambda, RDS, Cognito, CloudWatch).

## Security

Password hashing, JWT expiry, RBAC, file-content validation (not just
extension checking), path-traversal defense, signed URLs, environment-based
secrets, rate limiting, and CORS are all implemented — details and common
student mistakes to avoid in [`docs/SECURITY.md`](docs/SECURITY.md).

## Scalability

How this same code path scales from 10 to 100,000 students (load balancing,
managed Postgres, object storage taking upload traffic off the app server,
queues for async work) is discussed in [`docs/SCALABILITY.md`](docs/SCALABILITY.md).

## Failure Handling

Every route funnels unexpected errors through one handler that never leaks
a stack trace to the client; deadline checks always use the server clock;
duplicate-submission and idempotency handling is covered in
[`docs/FAILURE_HANDLING.md`](docs/FAILURE_HANDLING.md).

## Screenshots

Once you've run through the [local setup walkthrough](docs/LOCAL_SETUP_WALKTHROUGH.md),
save screenshots into `screenshots/` using the filenames listed in
[`docs/GITHUB_STRATEGY.md`](docs/GITHUB_STRATEGY.md#screenshot-checklist).

## Results

The system was manually exercised end-to-end (registration → assignment
creation → submission → grading → feedback) plus an automated 25-case test
suite; all core and edge-case flows (late submission, resubmission,
unauthorized grading, marks-above-maximum, cross-student access) behave as
specified. See [`docs/TESTING.md`](docs/TESTING.md) for full results.

## Limitations

- No malware scanning of uploaded files (content-type/magic-byte validation
  only — see `docs/SECURITY.md` for why this matters and how to add it).
- No email/push notifications for new grades or upcoming deadlines yet.
- Dashboards aggregate in Python rather than SQL `GROUP BY`, fine at student
  scale but not how you'd do it at 100k+ rows (see `docs/SCALABILITY.md`).

## Future Improvements

Plagiarism/similarity detection, deadline reminder emails, rubric-based
grading, an admin role for user/course management, CI/CD via GitHub
Actions, containerized deployment, and automated backups.

## Learning Outcomes

Building this required working through, hands-on: the difference between a
cloud database and object storage and why each exists; the authentication
vs. authorization distinction and how to enforce it server-side, not just
hide UI; why deadlines must be checked against a server clock; how to design
a REST API around resources and status codes; and how the same codebase can
target a zero-cost local setup or a real managed cloud backend by changing
only configuration.

## Author

Built as a Cloud Computing course project. See
[`reports/RESUME_AND_INTERVIEW.md`](reports/RESUME_AND_INTERVIEW.md) for
resume bullets, LinkedIn copy, and interview prep.
