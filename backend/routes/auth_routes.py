"""
AUTH endpoints
  POST /api/register
  POST /api/login
  POST /api/logout
"""
import re

from flask import Blueprint, current_app, g, jsonify, request

from cloud import auth_service, database_service as dbs
from backend.middleware.auth_middleware import require_auth
from backend.utils.errors import BadRequest, Conflict, Unauthorized
from backend.utils.rate_limit import auth_rate_limiter
from backend.utils.security import hash_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ALLOWED_ROLES = {"student", "teacher"}


@auth_bp.post("/register")
def register():
    """
    Request:  {name, email, password, role, teacher_invite_code?}
    Response: 201 {user, token}

    A "teacher" registration additionally requires TEACHER_INVITE_CODE to
    match an environment-configured value, so random visitors cannot grant
    themselves grading powers - this is the role-based authorization story
    starting at the very first step (account creation).
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "student").strip().lower()

    if not name:
        raise BadRequest("Name is required.")
    if not _EMAIL_RE.match(email):
        raise BadRequest("A valid email address is required.")
    if len(password) < 8:
        raise BadRequest("Password must be at least 8 characters long.")
    if role not in _ALLOWED_ROLES:
        raise BadRequest("Role must be 'student' or 'teacher'.")

    settings = current_app.config["SETTINGS"]
    if role == "teacher" and settings.teacher_invite_code:
        if data.get("teacher_invite_code") != settings.teacher_invite_code:
            raise Unauthorized("Invalid teacher invite code.", code="INVALID_INVITE_CODE")

    db = current_app.config["DB"]
    if dbs.get_user_by_email(db, email):
        raise Conflict("An account with this email already exists.", code="EMAIL_TAKEN")

    password_hash = auth_service.hash_password(password)
    user = dbs.create_user(db, name, email, password_hash, role)
    token = auth_service.create_access_token(settings, user["user_id"], user["role"], user["email"])
    return jsonify({"user": _public_user(user), "token": token}), 201


@auth_bp.post("/login")
def login():
    """Request: {email, password}. Response: {user, token}.
    Rate-limited per email+IP to slow down password-guessing bots."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    settings = current_app.config["SETTINGS"]
    auth_rate_limiter.check(f"login:{email}:{request.remote_addr}", settings.auth_rate_limit_per_min)

    db = current_app.config["DB"]
    user = dbs.get_user_by_email(db, email)
    if not user or not auth_service.verify_password(password, user["password_hash"]):
        raise Unauthorized("Incorrect email or password.", code="INVALID_CREDENTIALS")

    token = auth_service.create_access_token(settings, user["user_id"], user["role"], user["email"])
    return jsonify({"user": _public_user(user), "token": token})


@auth_bp.post("/logout")
@require_auth
def logout():
    """Revokes the current token immediately (see revoked_tokens table), so
    it cannot be reused for the rest of its natural lifetime, and a later
    request to any protected route with the same token gets a 401."""
    from backend.utils.time_utils import to_iso, utcnow
    db = current_app.config["DB"]
    dbs.revoke_token(db, hash_token(g.token), to_iso(utcnow()))
    return jsonify({"message": "Logged out successfully."})


def _public_user(user: dict) -> dict:
    return {"user_id": user["user_id"], "name": user["name"], "email": user["email"], "role": user["role"]}
