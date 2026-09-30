"""Quick smoke test (not pytest) to sanity check the whole workflow end to end."""
import io
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///./data/smoke_test.db"
os.environ["LOCAL_STORAGE_DIR"] = "./data/smoke_uploads"
os.environ["SECRET_KEY"] = "smoke-test-secret-key-not-for-prod"
os.environ["TEACHER_INVITE_CODE"] = "TEACH-2026"

for f in ["./data/smoke_test.db"]:
    if os.path.exists(f):
        os.remove(f)
import shutil
shutil.rmtree("./data/smoke_uploads", ignore_errors=True)

from backend.app import create_app  # noqa: E402

app = create_app()
client = app.test_client()


def j(resp):
    return resp.get_json()


def expect(cond, msg):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {msg}")
    if not cond:
        raise SystemExit(1)


# 1. Register teacher
r = client.post("/api/register", json={
    "name": "Dr. Asha Rao", "email": "asha@example.edu", "password": "TeachPass123",
    "role": "teacher", "teacher_invite_code": "TEACH-2026",
})
expect(r.status_code == 201, "Teacher registration")
teacher_token = j(r)["token"]
teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

# 2. Register student
r = client.post("/api/register", json={
    "name": "Rohit Kumar", "email": "rohit@example.edu", "password": "StudentPass123", "role": "student",
})
expect(r.status_code == 201, "Student registration")
student_token = j(r)["token"]
student_headers = {"Authorization": f"Bearer {student_token}"}

# 2b. Student cannot self-register as teacher without invite code
r = client.post("/api/register", json={
    "name": "Fake Teacher", "email": "fake@example.edu", "password": "Password123", "role": "teacher",
})
expect(r.status_code == 401, "Registering as teacher without invite code is rejected")

# 3. Invalid login
r = client.post("/api/login", json={"email": "rohit@example.edu", "password": "wrong"})
expect(r.status_code == 401, "Invalid login rejected")

# 4. Student cannot open teacher-only endpoint
r = client.post("/api/courses", json={"course_name": "CS101"}, headers=student_headers)
expect(r.status_code == 403, "Student blocked from teacher-only course creation")

# 5. Teacher creates a course
r = client.post("/api/courses", json={"course_name": "Cloud Computing 101"}, headers=teacher_headers)
expect(r.status_code == 201, "Teacher creates course")
course_id = j(r)["course_id"]

# 6. Teacher creates an assignment with a deadline in the future
import datetime
future = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2)).isoformat().replace("+00:00", "Z")
r = client.post("/api/assignments", json={
    "course_id": course_id, "title": "Assignment 1: Cloud Basics",
    "description": "Write a short report.", "deadline": future, "max_marks": 100,
    "allowed_file_types": "pdf,docx", "max_file_size_mb": 5,
}, headers=teacher_headers)
expect(r.status_code == 201, "Teacher creates assignment")
assignment_id = j(r)["assignment_id"]

# 7. Student views assignment
r = client.get(f"/api/assignments/{assignment_id}", headers=student_headers)
expect(r.status_code == 200, "Student views assignment")

# 8. Student uploads a valid PDF
pdf_bytes = b"%PDF-1.4\n%mock pdf content for testing\n%%EOF"
r = client.post(
    f"/api/assignments/{assignment_id}/submit",
    data={"file": (io.BytesIO(pdf_bytes), "homework.pdf")},
    headers=student_headers, content_type="multipart/form-data",
)
expect(r.status_code == 201, "Valid PDF upload accepted")
submission_id = j(r)["submission_id"]
expect(j(r)["submission_status"] == "SUBMITTED", "On-time submission marked SUBMITTED")

# 9. Invalid extension rejected
r = client.post(
    f"/api/assignments/{assignment_id}/submit",
    data={"file": (io.BytesIO(b"echo malicious"), "virus.exe")},
    headers=student_headers, content_type="multipart/form-data",
)
expect(r.status_code == 415, "Invalid file extension rejected")

# 10. Oversized file rejected (assignment limit is 5MB)
big = b"%PDF-1.4\n" + b"0" * (6 * 1024 * 1024)
r = client.post(
    f"/api/assignments/{assignment_id}/submit",
    data={"file": (io.BytesIO(big), "big.pdf")},
    headers=student_headers, content_type="multipart/form-data",
)
expect(r.status_code == 413, "Oversized file rejected")

# 11. Resubmission creates version 2
r = client.post(
    f"/api/assignments/{assignment_id}/submit",
    data={"file": (io.BytesIO(pdf_bytes), "homework_v2.pdf")},
    headers=student_headers, content_type="multipart/form-data",
)
expect(r.status_code == 201 and j(r)["version"] == 2, "Resubmission creates version 2")
submission_id_v2 = j(r)["submission_id"]

# 12. Student sees own submissions
r = client.get("/api/submissions/me", headers=student_headers)
expect(r.status_code == 200 and len(j(r)) == 2, "Student sees own submissions (2 versions)")

# 13. Another student cannot view this student's submission
r = client.post("/api/register", json={
    "name": "Priya Singh", "email": "priya@example.edu", "password": "Password123", "role": "student",
})
other_student_headers = {"Authorization": f"Bearer {j(r)['token']}"}
r = client.get(f"/api/submissions/{submission_id_v2}", headers=other_student_headers)
expect(r.status_code == 403, "Other student cannot view private submission")

# 14. Teacher views submissions for assignment
r = client.get(f"/api/assignments/{assignment_id}/submissions", headers=teacher_headers)
expect(r.status_code == 200 and len(j(r)) == 2, "Teacher sees both submission versions")

# 15. Unauthorized grading rejected (student tries to grade)
r = client.post(f"/api/submissions/{submission_id_v2}/grade",
                 json={"marks": 90, "feedback": "Great job"}, headers=student_headers)
expect(r.status_code == 403, "Student cannot grade a submission")

# 16. Marks above maximum rejected
r = client.post(f"/api/submissions/{submission_id_v2}/grade",
                 json={"marks": 150, "feedback": "Too high"}, headers=teacher_headers)
expect(r.status_code == 400, "Marks above maximum rejected")

# 17. Teacher grades submission correctly
r = client.post(f"/api/submissions/{submission_id_v2}/grade",
                 json={"marks": 88, "feedback": "Well structured, good use of cloud concepts."},
                 headers=teacher_headers)
expect(r.status_code == 200 and j(r)["submission_status"] == "GRADED", "Teacher grades submission")

# 18. Student views feedback
r = client.get(f"/api/submissions/{submission_id_v2}/feedback", headers=student_headers)
expect(r.status_code == 200 and j(r)["marks"] == 88, "Student views marks and feedback")

# 19. Student downloads own submission
r = client.get(f"/api/submissions/{submission_id_v2}/download", headers=student_headers)
expect(r.status_code == 200 and r.data.startswith(b"%PDF"), "Student downloads own submission file")

# 20. Dashboards
r = client.get("/api/dashboard/student", headers=student_headers)
expect(r.status_code == 200 and j(r)["graded_assignments"] == 1, "Student dashboard reflects graded assignment")

r = client.get("/api/dashboard/teacher", headers=teacher_headers)
expect(r.status_code == 200 and j(r)["total_submissions"] == 2, "Teacher dashboard reflects submissions")

# 21. Logout then protected route fails
r = client.post("/api/logout", headers=student_headers)
expect(r.status_code == 200, "Logout succeeds")
r = client.get("/api/submissions/me", headers=student_headers)
expect(r.status_code == 401, "Protected route rejected after logout")

print("\nALL SMOKE TESTS PASSED")
