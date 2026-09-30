# Testing

## How to run the tests

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. pytest tests/ -v
```

There's also a standalone, dependency-light smoke test that exercises the
same core workflow without pytest, useful for a quick sanity check:

```bash
PYTHONPATH=. python3 tests/smoke_test.py
```

## Test Case Table

All 25 cases live in `tests/test_workflow.py` (pytest) and are mirrored by
`tests/smoke_test.py`, which was run directly against the live Flask app
during development. Every row below reflects an actual verified run, not a
projected result.

| # | Test Case | Expected Result | Actual Result |
|---|---|---|---|
| 1 | Student registration | 201, student account created | ✅ Pass |
| 2 | Teacher login | 200, teacher session token issued | ✅ Pass |
| 3 | Invalid login (wrong password) | 401 `INVALID_CREDENTIALS` | ✅ Pass |
| 4 | Teacher opens student-only dashboard | 403 `ROLE_NOT_ALLOWED` | ✅ Pass |
| 5 | Student opens teacher-only dashboard | 403 `ROLE_NOT_ALLOWED` | ✅ Pass |
| 6 | Teacher creates assignment | 201, assignment record created | ✅ Pass |
| 7 | Student views assignment | 200, assignment details returned | ✅ Pass |
| 8 | Valid PDF upload | 201, `submission_status = SUBMITTED` | ✅ Pass |
| 9 | Invalid file extension (`.exe`) | 415 `INVALID_FILE_TYPE` | ✅ Pass |
| 10 | Oversized file (over assignment limit) | 413 `FILE_TOO_LARGE` | ✅ Pass |
| 11 | On-time submission | `submission_status = SUBMITTED` | ✅ Pass |
| 12 | Late submission (deadline in the past, late allowed) | 201, `submission_status = LATE` | ✅ Pass |
| 13 | Resubmission | New row created with `version = 2` | ✅ Pass |
| 14 | Student views own submission | 200 | ✅ Pass |
| 15 | Student attempts to view another student's submission | 403 `FORBIDDEN` | ✅ Pass |
| 16 | Teacher views all submissions for their assignment | 200, all versions listed | ✅ Pass |
| 17 | Teacher grades a submission | 200, `submission_status = GRADED` | ✅ Pass |
| 18 | Marks entered above assignment maximum | 400 `MARKS_EXCEED_MAX` | ✅ Pass |
| 19 | Student views feedback after grading | 200, correct marks + feedback text returned | ✅ Pass |
| 20 | Student attempts to grade a submission | 403 `ROLE_NOT_ALLOWED` | ✅ Pass |
| 21 | File retrieval / download | 200, correct file bytes returned | ✅ Pass |
| 22 | Simulated cloud storage failure | 500 `INTERNAL_ERROR`, no stack trace leaked, no orphaned DB row | ✅ Pass |
| 23 | Simulated cloud database failure | 500 `INTERNAL_ERROR`, no stack trace leaked | ✅ Pass |
| 24 | Logout | 200, token revoked | ✅ Pass |
| 25 | Protected route accessed after logout | 401 `TOKEN_REVOKED` | ✅ Pass |

## Additional workflow coverage (beyond the 25 required cases)

The standalone smoke test additionally verified, live against the running
app: teacher self-registration blocked without a valid invite code, a full
resubmission → grading → feedback round trip with real marks/feedback text,
and both dashboards reflecting the correct aggregate counts after a mixed
set of submitted/late/graded records. All passed.

## Manual (UI) testing checklist

Beyond the automated API tests, walk through this list in the browser
before recording your demo screenshots (see
`docs/GITHUB_STRATEGY.md#screenshot-checklist`):

- [ ] Register as a teacher with the invite code from `.env`
- [ ] Register as a student (no invite code needed)
- [ ] Teacher creates a course, then an assignment with a near-future deadline
- [ ] Student sees the assignment on their dashboard
- [ ] Student uploads a valid file → status shows "Submitted"
- [ ] Student tries an unsupported file type → sees a clear error, no crash
- [ ] Teacher sees the submission appear in their dashboard/assignment view
- [ ] Teacher grades it with marks + feedback
- [ ] Student sees the grade and feedback on their dashboard
- [ ] Student resubmits (if allowed) → version increments, old version still visible to the teacher
- [ ] Student logs out, tries to hit a protected page directly → redirected to login
