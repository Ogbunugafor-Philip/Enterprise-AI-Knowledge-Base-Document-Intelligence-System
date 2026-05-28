import shutil
from pathlib import Path
from uuid import UUID

UPLOAD_BASE_DIR = Path("uploads")


def ensure_upload_directory(path: Path | None = None) -> Path:
    directory = path or UPLOAD_BASE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_upload_path(
    organization_id: UUID,
    department_id: UUID | None,
    document_id: UUID,
    filename: str,
) -> Path:
    safe_name = Path(filename).name
    department_part = str(department_id) if department_id else "general"
    return UPLOAD_BASE_DIR / str(organization_id) / department_part / str(document_id) / safe_name


async def save_uploaded_file(file, destination: Path) -> Path:
    ensure_upload_directory(destination.parent)
    with destination.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)
    return destination


def delete_file(path: str | Path) -> None:
    file_path = Path(path)
    if file_path.exists() and file_path.is_file():
        file_path.unlink()


def get_file_path(document_id: UUID, base_dir: Path = UPLOAD_BASE_DIR) -> Path | None:
    matches = list(base_dir.glob(f"**/{document_id}/*"))
    return matches[0] if matches else None


def quarantine_file(path: str | Path) -> Path:
    source = Path(path)
    quarantine_dir = ensure_upload_directory(UPLOAD_BASE_DIR / "quarantine")
    destination = quarantine_dir / source.name
    if source.exists():
        shutil.move(str(source), destination)
    return destination
