import mimetypes
import re
from pathlib import Path

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "xlsx", "xls", "png", "jpg", "jpeg", "tiff"}
EXTENSION_SIGNATURES = {
    "pdf": [b"%PDF"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "tiff": [b"II*\x00", b"MM\x00*"],
    "docx": [b"PK\x03\x04"],
    "xlsx": [b"PK\x03\x04"],
    "xls": [b"\xd0\xcf\x11\xe0"],
}


def validate_file_name(file_name: str) -> tuple[bool, str, str]:
    sanitized = Path(file_name).name.replace("\x00", "")
    sanitized = re.sub(r"[^A-Za-z0-9._ -]", "_", sanitized)
    if not sanitized or sanitized in {".", ".."} or ".." in Path(file_name).parts:
        return False, "Invalid or unsafe file name", sanitized
    return True, "File name is safe", sanitized


def validate_file_type(file_name: str, mime_type: str | None = None) -> tuple[bool, str]:
    extension = Path(file_name).suffix.lower().lstrip(".")
    if extension not in ALLOWED_EXTENSIONS:
        return False, f"File type .{extension} is not allowed"
    guessed_type, _ = mimetypes.guess_type(file_name)
    if mime_type and guessed_type and mime_type != guessed_type and not mime_type.startswith("application/octet-stream"):
        image_alias = extension in {"jpg", "jpeg"} and mime_type == "image/jpeg"
        if not image_alias:
            return False, "MIME type does not match file extension"
    return True, "File type is allowed"


def validate_file_size(file_size_bytes: int, max_size_mb: int = 50) -> tuple[bool, str]:
    if file_size_bytes <= 0:
        return False, "File is empty"
    if file_size_bytes > max_size_mb * 1024 * 1024:
        return False, f"File exceeds {max_size_mb}MB limit"
    return True, "File size is valid"


def validate_file_content(file_name: str, content: bytes) -> tuple[bool, str]:
    if not content:
        return False, "File is empty"
    extension = Path(file_name).suffix.lower().lstrip(".")
    signatures = EXTENSION_SIGNATURES.get(extension)
    if signatures and not any(content.startswith(signature) for signature in signatures):
        return False, "File content does not match declared file type"
    if extension == "txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            return False, "Text file content is not valid UTF-8"
    return True, "File content is valid"


def run_all_validations(
    file_name: str,
    file_size_bytes: int,
    content: bytes,
    mime_type: str | None = None,
    max_size_mb: int = 50,
) -> dict:
    failures: list[str] = []
    name_ok, name_reason, sanitized = validate_file_name(file_name)
    type_ok, type_reason = validate_file_type(sanitized, mime_type)
    size_ok, size_reason = validate_file_size(file_size_bytes, max_size_mb)
    content_ok, content_reason = validate_file_content(sanitized, content)
    for ok, reason in [(name_ok, name_reason), (type_ok, type_reason), (size_ok, size_reason), (content_ok, content_reason)]:
        if not ok:
            failures.append(reason)
    return {"is_valid": not failures, "sanitized_file_name": sanitized, "failures": failures}
