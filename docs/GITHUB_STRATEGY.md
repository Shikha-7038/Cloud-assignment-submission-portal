# GitHub Repository & Commit Strategy

A project with one giant "initial commit" reads as copy-pasted. A project
with a real, incremental commit history reads as built. This doc gives you
a commit plan and a screenshot checklist so your GitHub repo backs up the
project report and your resume claims.

## Repository setup

```bash
cd Cloud-Based-Assignment-Submission-Portal
git init
git add .gitignore
git commit -m "chore: initial project structure and gitignore"
```

Suggested repo name: `cloud-assignment-submission-portal`. Add a short
description and topics on GitHub (`cloud-computing`, `flask`, `react`,
`rest-api`, `jwt-auth`, `supabase`) so it's discoverable and signals the
stack at a glance.

## Suggested commit sequence

Commit in this order (or close to it) so the history tells the same story
as the architecture — infrastructure, then auth, then core features, then
polish, then docs:

1. `chore: project scaffolding (backend/, frontend/, cloud/, tests/)`
2. `feat: config layer reading all settings from environment variables`
3. `feat: cloud database service (SQLite local / Postgres cloud)`
4. `feat: cloud object storage service (local disk / Supabase Storage)`
5. `feat: JWT auth service + password hashing`
6. `feat: auth middleware — require_auth and require_role`
7. `feat: user registration and login endpoints`
8. `feat: course and assignment CRUD endpoints`
9. `feat: assignment submission workflow with file validation`
10. `feat: resubmission versioning and duplicate-submission handling`
11. `feat: deadline enforcement using server clock`
12. `feat: grading and feedback endpoints`
13. `feat: student and teacher dashboards`
14. `feat: centralized error handling middleware`
15. `feat: rate limiting on login`
16. `test: automated workflow tests covering all required scenarios`
17. `feat: React frontend — auth pages and routing`
18. `feat: React frontend — student dashboard and submission flow`
19. `feat: React frontend — teacher dashboard, assignment creation, grading`
20. `style: design pass on frontend (typography, layout, status badges)`
21. `docs: README, architecture, API reference, security, deployment docs`
22. `docs: add screenshots and demo walkthrough`
23. `ci: add GitHub Actions workflow to run pytest on push` *(see below)*

If you're building this over multiple days for a course, spread these
commits across those days with real timestamps rather than backdating or
squashing everything into one session — a commit history spread over a
believable timeframe is itself part of the proof.

## Suggested GitHub Actions workflow (optional but recommended)

Add `.github/workflows/tests.yml`:
```yaml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: PYTHONPATH=. pytest tests/ -v
        env:
          SECRET_KEY: ci-test-secret-key
          TEACHER_INVITE_CODE: TEACH-2026
```
This gives your repo a green checkmark badge and a real CI/CD story for
your resume ("added a GitHub Actions pipeline that runs the test suite on
every push").

## Screenshot checklist

Save these into `screenshots/` with these exact filenames — the README and
`docs/LOCAL_SETUP_WALKTHROUGH.md` both reference them:

- `01-register-teacher.png`
- `02-register-student.png`
- `03-teacher-dashboard-empty.png`
- `04-create-assignment.png`
- `05-student-dashboard-pending.png`
- `06-student-upload-success.png`
- `07-invalid-file-error.png`
- `08-late-submission-badge.png`
- `09-teacher-submissions-list.png`
- `10-grading-form.png`
- `11-student-feedback-view.png`
- `12-logout-redirect.png`
- `13-api-health-check.png` — browser or curl output of `GET /api/health`
- `14-pytest-passing.png` — terminal output of the full test run
- `15-deployed-app.png` *(after completing `docs/DEPLOYMENT.md`)*

## README badges (optional polish)

Once CI is set up, add to the top of `README.md`:
```markdown
![Tests](https://github.com/<you>/cloud-assignment-submission-portal/actions/workflows/tests.yml/badge.svg)
```
