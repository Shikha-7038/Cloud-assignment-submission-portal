import hashlib
import uuid


def new_id() -> str:
    return str(uuid.uuid4())


def hash_token(token: str) -> str:
    """We store only a SHA-256 hash of revoked/logged-out tokens, never the
    raw token itself - so a leaked database dump can't be used to log back in."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
