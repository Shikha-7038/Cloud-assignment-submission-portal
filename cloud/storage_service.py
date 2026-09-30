"""
CLOUD OBJECT STORAGE SERVICE
=============================
This is where assignment FILES live (PDF/DOCX/ZIP/images) - never in the
database. The database only keeps a `storage_path` pointer here and a
`file_url` the student/teacher can use to fetch the bytes back.

Storage layout (mirrors real object storage conventions):

    assignments/{assignment_id}/{student_id}/{version}_{filename}

Two interchangeable backends, selected by CLOUD_PROVIDER:

  - LOCAL / FREE:  a folder on disk (`LOCAL_STORAGE_DIR`). Downloads are
                   served through an authenticated API route rather than a
                   raw static file path, so access control still applies.
  - CLOUD:         Supabase Storage (an S3-compatible object store with a
                   generous free tier). Uploads go to a private bucket and
                   downloads use short-lived SIGNED URLs rather than public
                   links, so a file cannot be fetched by guessing its path.

Either way, the rest of the app only ever calls `upload()`, `download()` and
`get_access_url()` - it does not know or care which backend is active.
"""
import os
import shutil
from dataclasses import dataclass

from backend.config import Settings


@dataclass
class StoredFile:
    storage_path: str
    file_url: str


def _object_path(assignment_id: str, student_id: str, version: int, filename: str) -> str:
    return f"assignments/{assignment_id}/{student_id}/{version}_{filename}"


class LocalStorageBackend:
    """Free, zero-setup stand-in for cloud object storage: a folder on disk."""

    def __init__(self, settings: Settings):
        self.root = settings.local_storage_dir
        os.makedirs(self.root, exist_ok=True)

    def upload(self, assignment_id: str, student_id: str, version: int, filename: str, data: bytes) -> StoredFile:
        rel_path = _object_path(assignment_id, student_id, version, filename)
        abs_path = os.path.join(self.root, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(data)
        # file_url is a stored reference only. The bytes are actually served
        # through GET /api/submissions/<id>/download, which enforces
        # authentication + ownership before it will read this path - there is
        # no route that serves local_storage_dir directly as static files.
        return StoredFile(storage_path=rel_path, file_url=f"/api/submissions/by-path/{rel_path}")

    def download(self, storage_path: str) -> bytes:
        abs_path = os.path.join(self.root, storage_path)
        if not os.path.abspath(abs_path).startswith(os.path.abspath(self.root)):
            raise FileNotFoundError("Invalid storage path")   # defends against path traversal
        with open(abs_path, "rb") as f:
            return f.read()

    def delete(self, storage_path: str) -> None:
        abs_path = os.path.join(self.root, storage_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)

    def get_access_url(self, storage_path: str, expires_in: int = 300) -> str:
        # Local mode has no real "signed URL" mechanism. Access control is
        # enforced instead by GET /api/submissions/<id>/download, which
        # checks ownership before reading this path.
        return f"/api/submissions/by-path/{storage_path}"


class SupabaseStorageBackend:
    """Real cloud object storage using Supabase Storage (S3-compatible,
    generous free tier). Requires the `requests` library and the three
    SUPABASE_* environment variables - never a hardcoded key."""

    def __init__(self, settings: Settings):
        import requests
        self._requests = requests
        self.base_url = settings.supabase_url
        self.bucket = settings.supabase_bucket
        self.service_key = settings.supabase_service_role_key
        self.expires_in = settings.signed_url_expire_seconds

    def _headers(self):
        return {"Authorization": f"Bearer {self.service_key}", "apikey": self.service_key}

    def upload(self, assignment_id: str, student_id: str, version: int, filename: str, data: bytes) -> StoredFile:
        rel_path = _object_path(assignment_id, student_id, version, filename)
        url = f"{self.base_url}/storage/v1/object/{self.bucket}/{rel_path}"
        resp = self._requests.post(url, headers=self._headers(), data=data)
        resp.raise_for_status()
        signed = self.get_access_url(rel_path, self.expires_in)
        return StoredFile(storage_path=rel_path, file_url=signed)

    def download(self, storage_path: str) -> bytes:
        url = f"{self.base_url}/storage/v1/object/{self.bucket}/{storage_path}"
        resp = self._requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.content

    def delete(self, storage_path: str) -> None:
        url = f"{self.base_url}/storage/v1/object/{self.bucket}/{storage_path}"
        self._requests.delete(url, headers=self._headers())

    def get_access_url(self, storage_path: str, expires_in: int = 300) -> str:
        """A signed URL grants temporary, private read access without making
        the bucket public - it expires automatically after `expires_in` seconds."""
        url = f"{self.base_url}/storage/v1/object/sign/{self.bucket}/{storage_path}"
        resp = self._requests.post(url, headers=self._headers(), json={"expiresIn": expires_in})
        resp.raise_for_status()
        return f"{self.base_url}/storage/v1{resp.json()['signedURL']}"


def build_storage_backend(settings: Settings):
    if settings.cloud_provider == "supabase":
        return SupabaseStorageBackend(settings)
    return LocalStorageBackend(settings)


def wipe_all_local_files(settings: Settings):
    """Test helper: only ever used by the automated test suite to reset state."""
    if os.path.isdir(settings.local_storage_dir):
        shutil.rmtree(settings.local_storage_dir)
    os.makedirs(settings.local_storage_dir, exist_ok=True)
