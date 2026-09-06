"""
Safe local file storage for student uploads (resumes, etc.).

- Files live under UPLOAD_DIR/resumes/{student_id}/ — one directory per
  student.
- The ORIGINAL filename is never used as the on-disk filename — only a
  fresh uuid4 + whitelisted extension, so there's no path-traversal via a
  crafted filename, and no collision between students.
- resolve_resume_path() re-validates the resolved path is actually inside
  the student's own directory before returning it.
"""
import uuid
from pathlib import Path

from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def _resume_dir(student_id: int) -> Path:
    base = Path(settings.UPLOAD_DIR).resolve() / "resumes" / str(student_id)
    base.mkdir(parents=True, exist_ok=True)
    return base


def save_resume(student_id: int, original_filename: str, content: bytes) -> str:
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {ext}")

    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = _resume_dir(student_id) / safe_name
    dest.write_bytes(content)

    return str(Path("resumes") / str(student_id) / safe_name)


def resolve_resume_path(student_id: int, stored_path: str):
    base_dir = _resume_dir(student_id)
    candidate = (Path(settings.UPLOAD_DIR).resolve() / stored_path).resolve()
    if base_dir not in candidate.parents and candidate != base_dir:
        return None
    if not candidate.is_file():
        return None
    return candidate


def delete_resume(student_id: int, stored_path: str) -> None:
    path = resolve_resume_path(student_id, stored_path)
    if path is not None:
        path.unlink(missing_ok=True)