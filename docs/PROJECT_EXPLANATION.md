# Project Explanation & Industry Relevance

## What is a Cloud-Based Student Assignment Submission & Feedback Portal?

It is a web application, hosted on cloud infrastructure, where a teacher
posts assignments with deadlines and students upload their work against
them. The system stores the files and all the bookkeeping around them
(who submitted what, when, at what version, with what grade and feedback)
so that neither side has to track any of it manually.

### A. Simple Explanation

Think of it as a shared, always-on locker and gradebook. A teacher drops an
assignment into the locker with a due date attached. Students walk up
(from anywhere, any device), drop their file in, and get a receipt. The
teacher opens each locker, looks at the file, writes a grade and a note,
and the student can check back any time to see it — no more "did you get
my email?" or lost pen drives.

### B. Technical Explanation

The frontend (React) never touches a database or a file system directly —
it only talks to a REST API. The backend (Flask) is the only thing that
can write to the **cloud database** (structured metadata: users, courses,
assignments, submission records, marks, feedback) or the **cloud object
storage** (the actual file bytes). Every request carries a signed JWT that
proves who the caller is (**authentication**) and what role they hold
(**authorization**), so the same API enforces "a student can upload but
not grade" without trusting the frontend to hide a button.

## Why cloud computing suits this system

- **Access from anywhere:** a student on a phone at home and a teacher in
  an office both hit the same hosted API — no VPN, no shared drive.
- **Centralization:** one source of truth instead of scattered emails and
  local folders per teacher.
- **Elastic storage:** cloud object storage grows with usage; nobody has to
  provision a bigger hard drive before finals week.
- **Managed reliability:** a managed database/storage service handles
  backups and uptime that a self-hosted file share typically wouldn't.

## How students access assignments from anywhere

They authenticate once (JWT), and every subsequent request — list
assignments, upload, check feedback — goes to the same public API endpoint
regardless of the student's location or device. Nothing is tied to a
specific machine.

## How teachers manage submissions centrally

A teacher's dashboard query (`GET /api/dashboard/teacher`) aggregates every
submission across every assignment they own in one call, instead of the
teacher opening per-student folders or inboxes one at a time.

## Why assignment files belong in object storage, not the database

Databases are optimized for small, structured, frequently-queried rows —
not multi-megabyte binary blobs. Storing a PDF as a database `BLOB` bloats
backups, slows down every query that touches that table, and doesn't scale
past a modest number of files. Object storage (a folder on disk locally, or
Supabase Storage/S3 in the cloud) is purpose-built for exactly this: cheap,
scalable, direct byte storage, addressed by a path. The database instead
keeps a `storage_path` pointer — small, fast to query, easy to index.

## Why metadata belongs in a cloud database

Metadata (who submitted, when, what version, graded or not, what mark) is
exactly the kind of structured, relational, frequently-filtered data a
database is built for — "give me every ungraded submission for this
assignment" is a single indexed query.

## How feedback moves from teacher to student

1. Teacher calls `POST /api/submissions/{id}/grade` with marks + feedback.
2. The backend validates the teacher owns that assignment and the marks
   don't exceed the maximum, then writes `marks`, `feedback`, `graded_at`,
   `graded_by` onto the submission row and flips its status to `GRADED`.
3. The student's next `GET /api/submissions/{id}/feedback` (or their
   dashboard) reads that same row — nothing is pushed or emailed; it's
   simply available the moment it's written, from the one source of truth.

## Workflow diagram

```
Teacher
   ↓
Creates Assignment
   ↓
Cloud Database
   ↓
Student Dashboard
   ↓
Student Uploads Assignment
   ↓
Cloud Object Storage
   ↓
Submission Metadata Saved
   ↓
Teacher Reviews Submission
   ↓
Marks + Feedback
   ↓
Cloud Database
   ↓
Student Views Feedback
```

---

## Industry Relevance

The same shape — auth, structured metadata store, object storage for
files, a REST API in between — is how real platforms are built:

- **Learning Management Systems** (Google Classroom, Canvas, Blackboard,
  Moodle): assignment posting, submission, grading, and analytics.
- **Universities & Schools:** replacing physical submission boxes and
  emailed attachments with an auditable digital record.
- **Corporate training platforms & employee training portals:** the same
  submit/review/feedback loop for compliance training or internal courses.
- **Online certification platforms & bootcamps:** project submissions
  graded by instructors or reviewers at scale.
- **EdTech platforms generally:** any product where "hand in work, get it
  reviewed" is core to the product.

### Business benefits

| Benefit | How this architecture delivers it |
|---|---|
| Centralized data | One database is the single source of truth for every course |
| Remote accessibility | REST API + web frontend, no location dependency |
| Scalable storage | Object storage scales independently of the app server |
| Automated submission tracking | Status (`SUBMITTED`/`LATE`/`GRADED`) computed server-side, not manually tracked |
| Reduced manual paperwork | No physical hand-in, no spreadsheet of grades |
| Centralized feedback | Feedback lives next to the submission it's about |
| Secure access | Role-based authorization on every route |
| Backup & availability | Managed cloud database/storage handle this, vs. a local folder that isn't backed up |
