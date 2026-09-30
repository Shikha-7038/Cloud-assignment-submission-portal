"""File-upload validation: extension, size, and real file content (magic bytes),
so a renamed .exe can't sneak in disguised as a .pdf."""
import os
import re

from backend.utils.errors import BadRequest, PayloadTooLarge, UnsupportedMedia

ALLOWED_EXTENSIONS = {"pdf", "docx", "zip", "png", "jpg", "jpeg", "txt"}
MAX_UPLOAD_MB_HARD_LIMIT = 25

CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "zip": "application/zip",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "txt": "text/plain",
}

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def get_extension(filename: str) -> str:
    return os.path.splitext(filename or "")[1].lstrip(".").lower()


def sanitize_filename(filename: str) -> str:
    """Strip any folder path and special characters so the name is safe to use
    inside a storage path (defends against path traversal like ../../etc)."""
    base = os.path.basename((filename or "").replace("\\", "/")).strip()
    stem, ext = os.path.splitext(base)
    stem = _UNSAFE.sub("_", stem).strip("._") or "file"
    return f"{stem[:80]}{ext.lower()}"


def content_matches_extension(ext: str, head: bytes) -> bool:
    """Compare the first bytes of the file with what the extension claims."""
    if ext == "pdf":
        return head.startswith(b"%PDF-")
    if ext == "png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if ext in ("jpg", "jpeg"):
        return head.startswith(b"\xff\xd8\xff")
    if ext in ("docx", "zip"):
        return head.startswith(b"PK\x03\x04")
    if ext == "txt":
        return b"\x00" not in head
    return False


def validate_upload(filename: str, data: bytes, allowed_types: list, max_mb: int):
    """Return (safe_filename, extension, content_type) or raise a 4xx AppError."""
    if not filename:
        raise BadRequest("No file name received.", code="NO_FILE")
    ext = get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS or ext not in allowed_types:
        raise UnsupportedMedia(
            f"File type '.{ext or '?'}' is not allowed. Allowed: {', '.join(allowed_types)}.")
    if not data:
        raise BadRequest("The uploaded file is empty.", code="EMPTY_FILE")
    limit = min(max_mb, MAX_UPLOAD_MB_HARD_LIMIT) * 1024 * 1024
    if len(data) > limit:
        raise PayloadTooLarge(f"File is larger than the {min(max_mb, MAX_UPLOAD_MB_HARD_LIMIT)} MB limit.")
    if not content_matches_extension(ext, data[:16]):
        raise UnsupportedMedia(
            f"The file content does not look like a real .{ext} file.", code="FILE_CONTENT_MISMATCH")
    return sanitize_filename(filename), ext, CONTENT_TYPES[ext]
