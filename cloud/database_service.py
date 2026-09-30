"""
CLOUD DATABASE SERVICE
=======================
This module is the single place that talks to the structured "cloud
database". It stores everything that is naturally tabular/queryable:
users, courses, assignments, and submission METADATA (marks, feedback,
status, file references). It never stores the assignment file bytes
themselves - those live in cloud OBJECT STORAGE (see storage_service.py);
this table only keeps a `storage_path` / `file_url` pointer to them.

Two interchangeable backends, selected purely by DATABASE_URL / CLOUD_PROVIDER:

  - LOCAL / FREE:  SQLite file on disk. Zero setup, ships with Python.
                   Used for CLOUD_PROVIDER=local (the default, for grading
                   and local development without any account).
  - CLOUD:         PostgreSQL (e.g. a free-tier Supabase Postgres database).
                   Used for CLOUD_PROVIDER=supabase. Same SQL (both are
                   ANSI-SQL/psycopg2-`%s` style placeholders), same functions
                   below - only the driver connection changes.

Every query is parameterized (never uses string formatting for values) to
prevent SQL injection.
"""
import os
import sqlite3
import threading
from contextlib import contextmanager

from backend.config import Settings
from backend.utils.security import new_id
from backend.utils.time_utils import to_iso, utcnow

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id         TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    course_id       TEXT PRIMARY KEY,
    course_name     TEXT NOT NULL,
    teacher_id      TEXT NOT NULL REFERENCES users(user_id),
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assignments (
    assignment_id       TEXT PRIMARY KEY,
    course_id           TEXT NOT NULL REFERENCES courses(course_id),
    title               TEXT NOT NULL,
    description         TEXT DEFAULT '',
    deadline            TEXT NOT NULL,
    max_marks           REAL NOT NULL DEFAULT 100,
    allowed_file_types  TEXT NOT NULL DEFAULT 'pdf,docx',
    max_file_size_mb    INTEGER NOT NULL DEFAULT 10,
    allow_resubmission  INTEGER NOT NULL DEFAULT 1,
    reject_late         INTEGER NOT NULL DEFAULT 0,
    created_by          TEXT NOT NULL REFERENCES users(user_id),
    created_at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assignments_course ON assignments(course_id);

CREATE TABLE IF NOT EXISTS submissions (
    submission_id       TEXT PRIMARY KEY,
    assignment_id       TEXT NOT NULL REFERENCES assignments(assignment_id),
    student_id          TEXT NOT NULL REFERENCES users(user_id),
    file_name            TEXT NOT NULL,
    file_url             TEXT NOT NULL,
    storage_path         TEXT NOT NULL,
    version               INTEGER NOT NULL DEFAULT 1,
    submitted_at          TEXT NOT NULL,
    submission_status    TEXT NOT NULL DEFAULT 'SUBMITTED',
    marks                 REAL,
    feedback              TEXT,
    graded_at             TEXT,
    graded_by             TEXT REFERENCES users(user_id)
);
CREATE INDEX IF NOT EXISTS idx_submissions_assignment ON submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_submissions_student ON submissions(student_id);

CREATE TABLE IF NOT EXISTS revoked_tokens (
    token_hash   TEXT PRIMARY KEY,
    revoked_at   TEXT NOT NULL
);
"""


class DatabaseService:
    """Thread-safe wrapper around either sqlite3 (local) or psycopg2 (cloud
    Postgres/Supabase). Exposes plain Python-dict-returning query helpers so
    the rest of the app never has to know which backend is active."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = "postgres" if settings.database_url.startswith(("postgres://", "postgresql://")) else "sqlite"
        self._lock = threading.Lock()
        if self.provider == "sqlite":
            path = settings.database_url.replace("sqlite:///", "")
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        else:
            # Cloud PostgreSQL (e.g. Supabase). psycopg2 is only imported here
            # so that local/free-tier users never need to install it.
            import psycopg2
            import psycopg2.extras
            self._psycopg2 = psycopg2
            self._extras = psycopg2.extras
            self._conn = psycopg2.connect(settings.database_url)
            self._conn.autocommit = True
        self._init_schema()

    def _qmark(self, sql: str) -> str:
        """SQLite uses '?' placeholders, Postgres uses '%s'. Write queries in
        this module using '?' and this converts them for Postgres."""
        return sql.replace("?", "%s") if self.provider == "postgres" else sql

    def _init_schema(self):
        statements = [s.strip() for s in _SCHEMA.split(";") if s.strip()]
        with self._lock:
            cur = self._conn.cursor()
            for stmt in statements:
                cur.execute(self._qmark(stmt))
            if self.provider == "sqlite":
                self._conn.commit()

    @contextmanager
    def _cursor(self):
        with self._lock:
            if self.provider == "postgres":
                cur = self._conn.cursor(cursor_factory=self._extras.RealDictCursor)
            else:
                cur = self._conn.cursor()
            try:
                yield cur
                if self.provider == "sqlite":
                    self._conn.commit()
            except Exception:
                if self.provider == "sqlite":
                    self._conn.rollback()
                raise

    def execute(self, sql: str, params: tuple = ()):
        with self._cursor() as cur:
            cur.execute(self._qmark(sql), params)

    def fetchone(self, sql: str, params: tuple = ()):
        with self._cursor() as cur:
            cur.execute(self._qmark(sql), params)
            row = cur.fetchone()
            return dict(row) if row is not None else None

    def fetchall(self, sql: str, params: tuple = ()):
        with self._cursor() as cur:
            cur.execute(self._qmark(sql), params)
            return [dict(r) for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Repository functions - one clear function per query, used by backend/services
# ---------------------------------------------------------------------------

def create_user(db: DatabaseService, name: str, email: str, password_hash: str, role: str) -> dict:
    user = {
        "user_id": new_id(), "name": name, "email": email.lower().strip(),
        "password_hash": password_hash, "role": role, "created_at": to_iso(utcnow()),
    }
    db.execute(
        "INSERT INTO users (user_id, name, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user["user_id"], user["name"], user["email"], user["password_hash"], user["role"], user["created_at"]),
    )
    return user


def get_user_by_email(db: DatabaseService, email: str):
    return db.fetchone("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))


def get_user_by_id(db: DatabaseService, user_id: str):
    return db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))


def create_course(db: DatabaseService, course_name: str, teacher_id: str) -> dict:
    course = {"course_id": new_id(), "course_name": course_name, "teacher_id": teacher_id,
              "created_at": to_iso(utcnow())}
    db.execute("INSERT INTO courses (course_id, course_name, teacher_id, created_at) VALUES (?, ?, ?, ?)",
               (course["course_id"], course["course_name"], course["teacher_id"], course["created_at"]))
    return course


def list_courses(db: DatabaseService):
    return db.fetchall("SELECT * FROM courses ORDER BY created_at DESC")


def get_course(db: DatabaseService, course_id: str):
    return db.fetchone("SELECT * FROM courses WHERE course_id = ?", (course_id,))


def create_assignment(db: DatabaseService, **fields) -> dict:
    fields = {"assignment_id": new_id(), "created_at": to_iso(utcnow()), **fields}
    db.execute(
        """INSERT INTO assignments
           (assignment_id, course_id, title, description, deadline, max_marks,
            allowed_file_types, max_file_size_mb, allow_resubmission, reject_late,
            created_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (fields["assignment_id"], fields["course_id"], fields["title"], fields.get("description", ""),
         fields["deadline"], fields.get("max_marks", 100), fields.get("allowed_file_types", "pdf,docx"),
         fields.get("max_file_size_mb", 10), int(fields.get("allow_resubmission", True)),
         int(fields.get("reject_late", False)), fields["created_by"], fields["created_at"]),
    )
    return fields


def update_assignment(db: DatabaseService, assignment_id: str, fields: dict):
    if not fields:
        return
    cols = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [assignment_id]
    db.execute(f"UPDATE assignments SET {cols} WHERE assignment_id = ?", tuple(values))


def delete_assignment(db: DatabaseService, assignment_id: str):
    db.execute("DELETE FROM submissions WHERE assignment_id = ?", (assignment_id,))
    db.execute("DELETE FROM assignments WHERE assignment_id = ?", (assignment_id,))


def get_assignment(db: DatabaseService, assignment_id: str):
    return db.fetchone("SELECT * FROM assignments WHERE assignment_id = ?", (assignment_id,))


def list_assignments(db: DatabaseService, course_id: str = None):
    if course_id:
        return db.fetchall("SELECT * FROM assignments WHERE course_id = ? ORDER BY deadline ASC", (course_id,))
    return db.fetchall("SELECT * FROM assignments ORDER BY deadline ASC")


def create_submission(db: DatabaseService, **fields) -> dict:
    fields = {"submission_id": new_id(), **fields}
    db.execute(
        """INSERT INTO submissions
           (submission_id, assignment_id, student_id, file_name, file_url, storage_path,
            version, submitted_at, submission_status, marks, feedback, graded_at, graded_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (fields["submission_id"], fields["assignment_id"], fields["student_id"], fields["file_name"],
         fields["file_url"], fields["storage_path"], fields.get("version", 1), fields["submitted_at"],
         fields.get("submission_status", "SUBMITTED"), None, None, None, None),
    )
    return fields


def get_submission(db: DatabaseService, submission_id: str):
    return db.fetchone("SELECT * FROM submissions WHERE submission_id = ?", (submission_id,))


def list_submissions_for_assignment(db: DatabaseService, assignment_id: str):
    return db.fetchall("SELECT * FROM submissions WHERE assignment_id = ? ORDER BY submitted_at DESC",
                        (assignment_id,))


def list_submissions_for_student(db: DatabaseService, student_id: str):
    return db.fetchall("SELECT * FROM submissions WHERE student_id = ? ORDER BY submitted_at DESC", (student_id,))


def get_submission_for_student_assignment(db: DatabaseService, assignment_id: str, student_id: str):
    """Latest submission by this student for this assignment, used for
    resubmission-version numbering and duplicate-submission checks."""
    return db.fetchone(
        """SELECT * FROM submissions WHERE assignment_id = ? AND student_id = ?
           ORDER BY version DESC LIMIT 1""",
        (assignment_id, student_id),
    )


def grade_submission(db: DatabaseService, submission_id: str, marks: float, feedback: str, graded_by: str,
                      graded_at: str):
    db.execute(
        """UPDATE submissions SET marks = ?, feedback = ?, graded_by = ?, graded_at = ?,
           submission_status = 'GRADED' WHERE submission_id = ?""",
        (marks, feedback, graded_by, graded_at, submission_id),
    )


def revoke_token(db: DatabaseService, token_hash: str, revoked_at: str):
    db.execute("INSERT OR REPLACE INTO revoked_tokens (token_hash, revoked_at) VALUES (?, ?)"
               if db.provider == "sqlite" else
               "INSERT INTO revoked_tokens (token_hash, revoked_at) VALUES (?, ?) "
               "ON CONFLICT (token_hash) DO NOTHING",
               (token_hash, revoked_at))


def is_token_revoked(db: DatabaseService, token_hash: str) -> bool:
    return db.fetchone("SELECT 1 FROM revoked_tokens WHERE token_hash = ?", (token_hash,)) is not None
