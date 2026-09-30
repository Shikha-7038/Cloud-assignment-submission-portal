"""
Middleware that answers both cloud-security questions on every protected route:

  Authentication ("who are you?")     -> require_auth
  Authorization  ("what can you do?") -> require_role(...)

A student token can never reach a teacher-only route (and vice-versa) because
require_role checks the `role` claim that was signed into the JWT at login -
a student cannot edit their own token to change it without invalidating the
signature.
"""
import functools

import jwt
from flask import current_app, g, request

from cloud import auth_service, database_service
from backend.utils.errors import Unauthorized


def _extract_token() -> str:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise Unauthorized("Missing or malformed Authorization header.")
    return header.split(" ", 1)[1].strip()


def require_auth(view):
    """Verifies the JWT, rejects revoked/expired/tampered tokens, and loads
    the current user onto flask.g for the view to use."""
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        token = _extract_token()
        settings = current_app.config["SETTINGS"]
        db = current_app.config["DB"]
        try:
            payload = auth_service.decode_access_token(settings, token)
        except jwt.ExpiredSignatureError:
            raise Unauthorized("Session expired. Please log in again.", code="TOKEN_EXPIRED")
        except jwt.PyJWTError:
            raise Unauthorized("Invalid authentication token.", code="TOKEN_INVALID")

        from backend.utils.security import hash_token
        if database_service.is_token_revoked(db, hash_token(token)):
            raise Unauthorized("Session has been logged out. Please log in again.", code="TOKEN_REVOKED")

        user = database_service.get_user_by_id(db, payload["sub"])
        if not user:
            raise Unauthorized("User no longer exists.")
        g.current_user = user
        g.token = token
        return view(*args, **kwargs)
    return wrapped


def require_role(*allowed_roles):
    """Stack after @require_auth. Example: @require_role('teacher', 'admin')."""
    def decorator(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            from backend.utils.errors import Forbidden
            if g.current_user["role"] not in allowed_roles:
                raise Forbidden(
                    f"This action requires role {', '.join(allowed_roles)}.", code="ROLE_NOT_ALLOWED")
            return view(*args, **kwargs)
        return wrapped
    return decorator
