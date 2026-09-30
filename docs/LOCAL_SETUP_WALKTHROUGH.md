# Local Setup Walkthrough

Runs entirely locally — SQLite database, disk-based file storage, no cloud
account required. This is `CLOUD_PROVIDER=local`, the default in
`.env.example`.

## 1. Backend

```bash
cd Cloud-Based-Assignment-Submission-Portal
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # defaults already work locally
python -m backend.app
```
You should see Flask start on `http://localhost:8000`. Visit
`http://localhost:8000/api/health` — you should get
`{"status": "ok", "cloud_provider": "local"}`.

## 2. Frontend

In a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173`.

## 3. Walk through the full workflow

1. **Register a teacher.** Use the invite code from your `.env`
   (`TEACHER_INVITE_CODE`, default `TEACH-2026`). *Screenshot: registration form.*
2. **Register a student** in a second browser (or an incognito window, so
   you can be logged in as both at once). *Screenshot: registration form.*
3. **As the teacher:** create a course, then create an assignment with a
   deadline a few minutes in the future so you can test both on-time and
   late submission. *Screenshot: assignment creation form; teacher dashboard
   showing the new assignment.*
4. **As the student:** open the assignment, upload a file from
   `sample_files/`. *Screenshot: successful submission with "Submitted"
   status.*
5. **Try an invalid upload** — a `.exe` or a file over the size limit — and
   confirm you get a clear error, not a crash. *Screenshot: the error
   message.*
6. **Wait for the deadline to pass**, then submit again (if resubmission is
   allowed) — confirm the new submission is marked "Late."
   *Screenshot: late status badge.*
7. **As the teacher:** open the assignment, see both submission versions,
   download one, grade it with marks and feedback.
   *Screenshot: submissions list; grading form.*
8. **As the student:** refresh the dashboard, see the grade and feedback.
   *Screenshot: feedback shown on student dashboard.*
9. **Log out**, try to navigate directly to a dashboard URL — confirm
   you're redirected to login. *Screenshot: login redirect.*

Save each screenshot into `screenshots/` using the filenames listed in
`docs/GITHUB_STRATEGY.md#screenshot-checklist` — they double as your
proof-of-work commits and your project report figures.

## 4. Run the automated tests

```bash
PYTHONPATH=. pytest tests/ -v
```
All 25 cases should pass — see `docs/TESTING.md` for what each one checks.

## Switching to cloud mode later

Once the local flow works end to end, follow `docs/DEPLOYMENT.md` to point
the exact same code at Supabase Postgres + Supabase Storage by changing
only your `.env` file — no code changes required.
