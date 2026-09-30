"""
Automated backend tests. Mirrors the 25 test cases required by the brief.
Run with:  PYTHONPATH=. pytest tests/ -v
"""
import io

from tests.conftest import future_iso, past_iso, register

PDF = b"%PDF-1.4\nsample\n%%EOF"


def upload(client, headers, assignment_id, filename="homework.pdf", content=PDF):
    return client.post(
        f"/api/assignments/{assignment_id}/submit",
        data={"file": (io.BytesIO(content), filename)},
        headers=headers, content_type="multipart/form-data",
    )


# 1. Student registration
def test_student_registration(client):
    r = register(client, "Rohit Kumar", "rohit@example.edu", "StudentPass123", "student")
    assert r.status_code == 201
    assert r.get_json()["user"]["role"] == "student"


# 2. Teacher login
def test_teacher_login(client, teacher_headers):
    r = client.post("/api/login", json={"email": "asha@example.edu", "password": "TeachPass123"})
    assert r.status_code == 200
    assert r.get_json()["user"]["role"] == "teacher"


# 3. Invalid login
def test_invalid_login(client, student_headers):
    r = client.post("/api/login", json={"email": "rohit@example.edu", "password": "wrong-password"})
    assert r.status_code == 401


# 4. Student dashboard authorization (teacher cannot open student dashboard)
def test_teacher_cannot_open_student_dashboard(client, teacher_headers):
    r = client.get("/api/dashboard/student", headers=teacher_headers)
    assert r.status_code == 403


# 5. Teacher dashboard authorization (student cannot open teacher dashboard)
def test_student_cannot_open_teacher_dashboard(client, student_headers):
    r = client.get("/api/dashboard/teacher", headers=student_headers)
    assert r.status_code == 403


# 6. Teacher creates assignment
def test_teacher_creates_assignment(client, teacher_headers, course_id):
    r = client.post("/api/assignments", json={
        "course_id": course_id, "title": "A1", "deadline": future_iso(), "max_marks": 50,
    }, headers=teacher_headers)
    assert r.status_code == 201
    assert r.get_json()["title"] == "A1"


# 7. Student views assignment
def test_student_views_assignment(client, student_headers, assignment_id):
    r = client.get(f"/api/assignments/{assignment_id}", headers=student_headers)
    assert r.status_code == 200


# 8. Valid PDF upload
def test_valid_pdf_upload(client, student_headers, assignment_id):
    r = upload(client, student_headers, assignment_id)
    assert r.status_code == 201
    assert r.get_json()["submission_status"] == "SUBMITTED"


# 9. Invalid file extension
def test_invalid_extension_rejected(client, student_headers, assignment_id):
    r = upload(client, student_headers, assignment_id, filename="virus.exe", content=b"MZ...")
    assert r.status_code == 415


# 10. Oversized file
def test_oversized_file_rejected(client, student_headers, assignment_id):
    big = b"%PDF-1.4\n" + b"0" * (6 * 1024 * 1024)
    r = upload(client, student_headers, assignment_id, filename="big.pdf", content=big)
    assert r.status_code == 413


# 11. On-time submission
def test_on_time_submission(client, student_headers, assignment_id):
    r = upload(client, student_headers, assignment_id)
    assert r.get_json()["submission_status"] == "SUBMITTED"


# 12. Late submission
def test_late_submission(client, teacher_headers, student_headers, course_id):
    r = client.post("/api/assignments", json={
        "course_id": course_id, "title": "Late Test", "deadline": past_iso(days=1), "max_marks": 100,
    }, headers=teacher_headers)
    late_assignment_id = r.get_json()["assignment_id"]
    r = upload(client, student_headers, late_assignment_id)
    assert r.status_code == 201
    assert r.get_json()["submission_status"] == "LATE"


# 13. Resubmission
def test_resubmission_creates_new_version(client, student_headers, assignment_id):
    upload(client, student_headers, assignment_id)
    r2 = upload(client, student_headers, assignment_id, filename="v2.pdf")
    assert r2.get_json()["version"] == 2


# 14. Student views own submission
def test_student_views_own_submission(client, student_headers, assignment_id):
    sub_id = upload(client, student_headers, assignment_id).get_json()["submission_id"]
    r = client.get(f"/api/submissions/{sub_id}", headers=student_headers)
    assert r.status_code == 200


# 15. Student cannot view another student's submission
def test_student_cannot_view_others_submission(client, student_headers, assignment_id):
    sub_id = upload(client, student_headers, assignment_id).get_json()["submission_id"]
    other = register(client, "Priya", "priya@example.edu", "Password123", "student").get_json()["token"]
    r = client.get(f"/api/submissions/{sub_id}", headers={"Authorization": f"Bearer {other}"})
    assert r.status_code == 403


# 16. Teacher views submissions
def test_teacher_views_submissions(client, teacher_headers, student_headers, assignment_id):
    upload(client, student_headers, assignment_id)
    r = client.get(f"/api/assignments/{assignment_id}/submissions", headers=teacher_headers)
    assert r.status_code == 200 and len(r.get_json()) == 1


# 17. Teacher grades submission
def test_teacher_grades_submission(client, teacher_headers, student_headers, assignment_id):
    sub_id = upload(client, student_headers, assignment_id).get_json()["submission_id"]
    r = client.post(f"/api/submissions/{sub_id}/grade", json={"marks": 80, "feedback": "Good work"},
                     headers=teacher_headers)
    assert r.status_code == 200
    assert r.get_json()["submission_status"] == "GRADED"


# 18. Marks above maximum rejected
def test_marks_above_maximum_rejected(client, teacher_headers, student_headers, assignment_id):
    sub_id = upload(client, student_headers, assignment_id).get_json()["submission_id"]
    r = client.post(f"/api/submissions/{sub_id}/grade", json={"marks": 999, "feedback": "x"},
                     headers=teacher_headers)
    assert r.status_code == 400


# 19. Student views feedback
def test_student_views_feedback(client, teacher_headers, student_headers, assignment_id):
    sub_id = upload(client, student_headers, assignment_id).get_json()["submission_id"]
    client.post(f"/api/submissions/{sub_id}/grade", json={"marks": 70, "feedback": "Nice"}, headers=teacher_headers)
    r = client.get(f"/api/submissions/{sub_id}/feedback", headers=student_headers)
    assert r.status_code == 200 and r.get_json()["marks"] == 70


# 20. Unauthorized grading rejected
def test_unauthorized_grading_rejected(client, student_headers, assignment_id):
    sub_id = upload(client, student_headers, assignment_id).get_json()["submission_id"]
    r = client.post(f"/api/submissions/{sub_id}/grade", json={"marks": 10, "feedback": "x"},
                     headers=student_headers)
    assert r.status_code == 403


# 21. File retrieval
def test_file_download(client, student_headers, assignment_id):
    sub_id = upload(client, student_headers, assignment_id).get_json()["submission_id"]
    r = client.get(f"/api/submissions/{sub_id}/download", headers=student_headers)
    assert r.status_code == 200
    assert r.data.startswith(b"%PDF")


# 22. Cloud-storage failure -> graceful 500, not a crash/stack trace leak
def test_storage_failure_returns_clean_error(client, student_headers, assignment_id, app, monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("Simulated storage outage")
    monkeypatch.setattr(app.config["STORAGE"], "upload", boom)
    r = upload(client, student_headers, assignment_id)
    assert r.status_code == 500
    assert r.get_json()["error"]["code"] == "INTERNAL_ERROR"


# 23. Database failure -> graceful 500
def test_database_failure_returns_clean_error(client, student_headers, assignment_id, app, monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("Simulated database outage")
    monkeypatch.setattr(app.config["DB"], "execute", boom)
    r = upload(client, student_headers, assignment_id)
    assert r.status_code == 500


# 24. Logout
def test_logout(client, student_headers):
    r = client.post("/api/logout", headers=student_headers)
    assert r.status_code == 200


# 25. Protected route after logout
def test_protected_route_after_logout(client, student_headers):
    client.post("/api/logout", headers=student_headers)
    r = client.get("/api/submissions/me", headers=student_headers)
    assert r.status_code == 401
