"""
AUTHENTICATION & AUTHORIZATION SERVICE
========================================
Authentication answers "who are you?" - handled here with password hashing
(via werkzeug's salted scrypt hasher - never plain text, never a hardcoded
secret) and signed JWT access tokens.

Authorization answers "what are you allowed to do?" - handled by the
`require_role` decorator in backend/middleware/auth_middleware.py, which
reads the role embedded (and signed) inside the JWT this module issues.

This module is intentionally the ONLY place that creates or verifies tokens,
so the signing key and algorithm are never duplicated across the codebase.
In a Cloud=supabase deployment, this can be swapped for Supabase Auth
(email/password or OAuth) without changing any route code, because routes
only ever call `create_access_token` / `decode_access_token` /
`hash_password` / `verify_password`.
"""
from datetime import timedelta

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from backend.config import Settings
from backend.utils.time_utils import to_iso, utcnow

ALGORITHM = "HS256"


def hash_password(plain_password: str) -> str:
    return generate_password_hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, plain_password)


def create_access_token(settings: Settings, user_id: str, role: str, email: str) -> str:
    now = utcnow()
    payload = {
        "sub": user_id,
        "role": role,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(settings: Settings, token: str) -> dict:
    """Raises jwt.PyJWTError (ExpiredSignatureError / InvalidTokenError) on
    a bad or expired token - the middleware turns that into a 401."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
