# Resume, LinkedIn & Interview Prep

## Resume bullets

Pick 2–4 depending on space. Each is written to be true of this exact
codebase — verify before using, and swap in real deployed URLs once you've
completed `docs/DEPLOYMENT.md`.

- Built a full-stack cloud assignment submission portal (React, Flask,
  PostgreSQL/Supabase) with JWT authentication, role-based authorization,
  and a provider-agnostic cloud storage layer supporting local disk or
  Supabase Storage without code changes.
- Designed a REST API with 20+ endpoints covering auth, CRUD, file upload
  validation, and role/ownership-based access control, tested with an
  automated 25-case pytest suite covering core flows and simulated
  infrastructure failures.
- Implemented server-side deadline enforcement, resubmission versioning,
  and file-content validation (magic-byte checking, not just extension
  matching) to close common security gaps in file-upload systems.
- Deployed the application using a free-tier cloud stack (Supabase for
  database/storage, Render/Vercel for hosting), and documented a parallel
  AWS-mapped deployment path (RDS, S3, Lambda/API Gateway, Cognito).

## LinkedIn post draft

> Just shipped a Cloud-Based Student Assignment Submission & Feedback
> Portal — a full-stack project built to actually demonstrate cloud
> computing concepts, not just simulate them.
>
> Students submit assignments (with real file validation, deadline
> enforcement using the server clock, and resubmission versioning);
> teachers review, grade, and leave feedback. Behind it: a REST API in
> Flask, JWT-based auth with real role-based authorization, and a cloud
> layer that runs against either free local resources or a managed
> Postgres + object storage backend (Supabase) — same code, one config
> change.
>
> Also wrote a 25-case automated test suite, including simulated cloud
> database/storage failures, to make sure it fails gracefully instead of
> just working on the happy path.
>
> Repo: [link] · Docs: architecture, API reference, security notes, and a
> deployment guide (free-tier + an AWS-mapped path) all included.
>
> #CloudComputing #FullStackDevelopment #React #Flask #Supabase

## Interview Q&A prep

**"Walk me through the architecture."**
React frontend talks only to a REST API (Flask). The API is the sole
authority for both the cloud database (structured metadata: users,
assignments, submission records) and cloud object storage (the actual
files) — the frontend never touches either directly. I built both the
database and storage layer behind a small interface so the exact same
backend code runs against local SQLite/disk or a managed Postgres/Supabase
backend, switched entirely by environment variables.

**"Why not store the files in the database?"**
Databases are optimized for small, structured, frequently queried rows —
storing multi-megabyte blobs there bloats every backup and slows down
queries that don't even touch that column. Object storage is built for
exactly this; the database just keeps a path reference to where the file
actually lives.

**"How did you handle authentication vs. authorization?"**
Authentication is "who are you" — a JWT issued at login, verified on every
request. Authorization is "what can you do" — the user's role is a signed
claim inside that same token, and every protected route checks it
server-side with a decorator. I went a step further than role checking
alone: for things like grading or viewing a submission, the service layer
also checks *ownership* — a valid teacher token isn't enough to grade
someone else's assignment, they have to be the teacher who created it.

**"How do you know a student can't fake an on-time submission?"**
Deadline comparisons always use `datetime.now(timezone.utc)` computed on
the server at the moment the request is processed — the client never
supplies a timestamp that's trusted for this decision. Changing your
laptop's clock has no effect on the server's.

**"What happens if the file upload succeeds but the database write fails
right after?"** [good one to have a real answer to]
Storage is written to before the database row — if the database write then
fails, the exception is caught by the centralized error handler and the
client gets a clean 500, with no partial database record pointing at
nothing. The uploaded object is effectively orphaned in storage at that
point; a production system would add a periodic cleanup job for
storage objects with no matching database row, which I documented as a
known follow-up rather than building for a student-scale deployment.

**"How would this scale to 100,000 students?"**
The backend is stateless — no session state lives on the process, only in
the shared database/storage — so I could run many instances behind a load
balancer without code changes. The database would need to move off SQLite
to managed Postgres (already supported), and dashboard aggregation, which I
currently do in Python for simplicity, would move to SQL-side `GROUP BY`
queries or a scheduled pre-aggregation job. Large uploads would move to
direct-to-storage pre-signed uploads so big files stop passing through the
application server at all. Full breakdown in my `docs/SCALABILITY.md`.

**"What was the hardest bug or design decision?"**
Getting resubmission right — the first version overwrote the previous
submission's row, which silently destroyed grading history the moment a
student resubmitted after being graded. I redesigned it around a `version`
column so every submission remains a permanent row, and the "latest
submission" is just a max-version query rather than the only copy that
ever existed.

**"What would you add with more time?"**
Malware scanning on uploads (current validation checks type and content
signature, not malicious payloads of a valid type), deadline reminder
notifications, and moving from hand-rolled JWT to a managed auth provider
like Supabase Auth or Cognito if this needed to support things like
password reset flows and social login without me maintaining that code
myself.
