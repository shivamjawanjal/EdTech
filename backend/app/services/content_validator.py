"""
File Content and Magic Byte Validator for Secure Media Ingestion.

Ensures uploaded files conform to allowed formats, headers, and extensions,
preventing executable/malicious file masquerading.
NOTE: Magic-byte inspection detects corruption and extension/MIME spoofing,
but is not a replacement for an active anti-malware/antivirus scanner.
"""
import os
from typing import Optional, Tuple

# Allowed MIME types and extensions per purpose
PURPOSE_RULES = {
    "lecture_video": {
        "allowed_mimes": {"video/mp4", "video/webm"},
        "allowed_extensions": {".mp4", ".webm", ".m4v"},
        "max_size_bytes": 1610612736,  # 1.5 GB
    },
    "lecture_note": {
        "allowed_mimes": {"application/pdf"},
        "allowed_extensions": {".pdf"},
        "max_size_bytes": 52428800,  # 50 MB
    },
    "submission_attachment": {
        "allowed_mimes": {
            "image/jpeg",
            "image/png",
            "image/webp",
            "application/pdf",
        },
        "allowed_extensions": {".jpg", ".jpeg", ".png", ".webp", ".pdf"},
        "max_size_bytes": 15728640,  # 15 MB
    },
}


def detect_mime_from_magic_bytes(header_bytes: bytes) -> Optional[str]:
    """
    Inspect initial byte slice (up to 512 bytes) to determine the true content format.
    Returns detected canonical MIME string or None if unknown.
    """
    if not header_bytes or len(header_bytes) < 4:
        return None

    # 1. PDF: %PDF- (0x25, 0x50, 0x44, 0x46)
    if header_bytes.startswith(b"%PDF-"):
        return "application/pdf"

    # 2. PNG: \x89PNG\r\n\x1a\n
    if header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    # 3. JPEG: \xFF\xD8\xFF
    if header_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    # 4. WebP: RIFF....WEBP
    if len(header_bytes) >= 12 and header_bytes.startswith(b"RIFF") and header_bytes[8:12] == b"WEBP":
        return "image/webp"

    # 5. WebM / Matroska: \x1a\x45\xdf\xa3
    if header_bytes.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm"

    # 6. MP4 / ISO Base Media File Format:
    # Bytes 4-8 are 'ftyp'
    if len(header_bytes) >= 12 and header_bytes[4:8] == b"ftyp":
        return "video/mp4"

    return None


def validate_file_metadata(
    purpose: str,
    file_name: str,
    declared_mime: str,
    declared_size: int,
) -> Tuple[bool, Optional[str]]:
    """
    Validate pre-upload declarations before issuing signed upload ticket.
    Returns (is_valid, error_message).
    """
    rules = PURPOSE_RULES.get(purpose)
    if not rules:
        return False, f"Invalid upload purpose: '{purpose}'"

    if declared_size <= 0:
        return False, "Declared file size must be greater than 0 bytes"

    if declared_size > rules["max_size_bytes"]:
        max_mb = rules["max_size_bytes"] // (1024 * 1024)
        return False, f"File exceeds maximum allowed size of {max_mb}MB for {purpose}"

    _, ext = os.path.splitext(file_name.lower())
    if ext not in rules["allowed_extensions"]:
        return False, f"File extension '{ext}' is not permitted for {purpose}. Allowed: {rules['allowed_extensions']}"

    canonical_declared_mime = declared_mime.lower().split(";")[0].strip()
    if canonical_declared_mime not in rules["allowed_mimes"]:
        return False, f"MIME type '{declared_mime}' is not permitted for {purpose}. Allowed: {rules['allowed_mimes']}"

    return True, None


def validate_stored_content(
    purpose: str,
    file_name: str,
    declared_mime: str,
    actual_size: int,
    header_bytes: bytes,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate actual uploaded file bytes upon upload completion.
    Returns (is_valid, detected_mime, error_message).
    """
    rules = PURPOSE_RULES.get(purpose)
    if not rules:
        return False, None, f"Invalid upload purpose: '{purpose}'"

    if actual_size <= 0:
        return False, None, "Stored object is empty (0 bytes)"

    if actual_size > rules["max_size_bytes"]:
        max_mb = rules["max_size_bytes"] // (1024 * 1024)
        return False, None, f"Stored object size ({actual_size} bytes) exceeds maximum {max_mb}MB limit"

    detected_mime = detect_mime_from_magic_bytes(header_bytes)
    if not detected_mime:
        return False, None, "Unrecognized or corrupted file format header"

    if detected_mime not in rules["allowed_mimes"]:
        return False, detected_mime, f"Detected format '{detected_mime}' is not permitted for {purpose}"

    canonical_declared_mime = declared_mime.lower().split(";")[0].strip()
    # Normalize JPEG alias (image/pjpeg, image/jpg -> image/jpeg)
    if canonical_declared_mime in ("image/jpg", "image/pjpeg"):
        canonical_declared_mime = "image/jpeg"

    if detected_mime != canonical_declared_mime:
        return (
            False,
            detected_mime,
            f"Content type mismatch: Declared as '{declared_mime}', but file header is '{detected_mime}'",
        )

    # Check extension aligns with detected MIME
    _, ext = os.path.splitext(file_name.lower())
    expected_extensions = {
        "application/pdf": {".pdf"},
        "image/jpeg": {".jpg", ".jpeg"},
        "image/png": {".png"},
        "image/webp": {".webp"},
        "video/mp4": {".mp4", ".m4v"},
        "video/webm": {".webm"},
    }.get(detected_mime, set())

    if ext not in expected_extensions:
        return (
            False,
            detected_mime,
            f"File extension '{ext}' does not match detected content type '{detected_mime}'",
        )

    return True, detected_mime, None
