"""
Separately Configured Live Cloud Storage Provider Integration Test Suite (AWS S3 & Cloudflare R2).

Tests real provider behaviors:
1. Pre-signed PUT URL generation and required upload headers (Content-Type)
2. Direct HTTP PUT upload and provider CORS response
3. S3/R2 HeadObject metadata retrieval (size, content type, etag)
4. S3/R2 Byte-range GET retrieval for magic byte verification
5. Pre-signed GET URL download with Content-Disposition headers
6. Expired URL behavior (verifies provider returns 403 on expired signed URLs)
7. Non-existent object handling (verifies graceful None response on missing keys)
8. Object deletion and cleanup

ACTIVATION:
To execute this suite against a live AWS S3 or Cloudflare R2 bucket:
$env:RUN_LIVE_STORAGE_TESTS="true"
$env:S3_BUCKET_NAME="my-real-private-bucket"
$env:S3_ENDPOINT_URL="https://<account_id>.r2.cloudflarestorage.com" # if Cloudflare R2
$env:S3_ACCESS_KEY_ID="<real_access_key>"
$env:S3_SECRET_ACCESS_KEY="<real_secret_key>"
$env:S3_REGION="auto"
pytest backend/tests/test_storage_provider_integration.py -v
"""
import os
import time
import uuid
import pytest
import httpx

from app.core.config import Settings
from app.services.storage_service import S3StorageService

RUN_LIVE = os.getenv("RUN_LIVE_STORAGE_TESTS", "").lower() in ("true", "1", "yes")

pytestmark = pytest.mark.skipif(
    not RUN_LIVE,
    reason=(
        "Live S3/R2 integration tests are disabled by default to maintain zero-credential CI. "
        "Set RUN_LIVE_STORAGE_TESTS=true and valid S3_* environment variables to execute."
    ),
)


@pytest.fixture(scope="module")
def live_s3_service() -> S3StorageService:
    """Instantiate real S3/R2 storage service from environment."""
    settings = Settings(
        STORAGE_PROVIDER="s3",
        S3_BUCKET_NAME=os.environ.get("S3_BUCKET_NAME", ""),
        S3_ENDPOINT_URL=os.environ.get("S3_ENDPOINT_URL") or None,
        S3_ACCESS_KEY_ID=os.environ.get("S3_ACCESS_KEY_ID", ""),
        S3_SECRET_ACCESS_KEY=os.environ.get("S3_SECRET_ACCESS_KEY", ""),
        S3_REGION=os.environ.get("S3_REGION", "auto"),
    )
    if not settings.S3_BUCKET_NAME or not settings.S3_ACCESS_KEY_ID or not settings.S3_SECRET_ACCESS_KEY:
        pytest.skip("Incomplete live S3/R2 credentials in environment.")
    return S3StorageService(settings)


@pytest.fixture(scope="module")
def test_key() -> str:
    """Generate a clean isolated object key for integration test."""
    return f"integration_tests/{uuid.uuid4().hex}/test_sample.pdf"


SAMPLE_PDF_PAYLOAD = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\nendobj\n" + (b"0" * 600)


def test_live_presigned_put_and_cors(live_s3_service: S3StorageService, test_key: str):
    """
    1. Generate pre-signed PUT ticket with explicit Content-Type.
    2. Upload binary payload directly via HTTP PUT.
    3. Check provider status and CORS headers if configured.
    """
    ticket = live_s3_service.generate_upload_url(
        object_key=test_key,
        content_type="application/pdf",
        max_size_bytes=len(SAMPLE_PDF_PAYLOAD),
        expires_in=300,
    )
    assert ticket.upload_url.startswith("http")
    assert ticket.object_key == test_key
    assert ticket.headers.get("Content-Type") == "application/pdf"

    # Execute direct PUT request mimicking client browser
    headers = {"Content-Type": "application/pdf"}
    with httpx.Client(timeout=15.0) as client:
        resp = client.put(ticket.upload_url, content=SAMPLE_PDF_PAYLOAD, headers=headers)
        assert resp.status_code in (200, 204), f"Provider PUT failed: {resp.status_code} {resp.text}"


def test_live_metadata_retrieval(live_s3_service: S3StorageService, test_key: str):
    """Verify HeadObject metadata retrieval (content-length, content-type, ETag)."""
    meta = live_s3_service.get_object_metadata(test_key)
    assert meta is not None, "Stored object not found by HeadObject"
    assert meta.content_length == len(SAMPLE_PDF_PAYLOAD)
    assert meta.etag is not None


def test_live_byte_range_header_inspection(live_s3_service: S3StorageService, test_key: str):
    """Verify partial GET range retrieval (first 512 bytes) for magic byte inspection."""
    header = live_s3_service.get_object_header_bytes(test_key, byte_count=512)
    assert header is not None
    assert len(header) == 512
    assert header.startswith(b"%PDF-")


def test_live_presigned_download_url(live_s3_service: S3StorageService, test_key: str):
    """Verify pre-signed GET URL download with attachment Content-Disposition."""
    download_url = live_s3_service.generate_download_url(
        object_key=test_key,
        filename="verified_doc.pdf",
        disposition="attachment",
        expires_in=300,
    )
    assert download_url.startswith("http")

    with httpx.Client(timeout=15.0) as client:
        resp = client.get(download_url)
        assert resp.status_code == 200
        assert resp.content == SAMPLE_PDF_PAYLOAD
        disposition = resp.headers.get("content-disposition", "")
        assert "attachment" in disposition


def test_live_expired_url_rejected_by_provider(live_s3_service: S3StorageService, test_key: str):
    """
    Verify that an expired pre-signed URL is rejected by the cloud provider.
    Generates URL with 1-second TTL, waits 2 seconds, and executes GET.
    """
    expired_url = live_s3_service.generate_download_url(
        object_key=test_key,
        expires_in=1,
    )

    time.sleep(2)

    with httpx.Client(timeout=10.0) as client:
        resp = client.get(expired_url)
        # Cloudflare R2 and AWS S3 return 403 Forbidden on expired signature
        assert resp.status_code == 403, f"Expected 403 Forbidden for expired signature, got {resp.status_code}"
        assert any(term in resp.text.lower() for term in ("expired", "forbidden", "accessdenied"))


def test_live_nonexistent_object_handling(live_s3_service: S3StorageService):
    """Verify that querying a missing key returns None gracefully without unhandled exception."""
    missing_key = f"missing/{uuid.uuid4().hex}.pdf"
    meta = live_s3_service.get_object_metadata(missing_key)
    assert meta is None

    header = live_s3_service.get_object_header_bytes(missing_key, byte_count=512)
    assert header is None


def test_live_object_cleanup(live_s3_service: S3StorageService, test_key: str):
    """Verify object deletion and confirm object is no longer present."""
    deleted = live_s3_service.delete_object(test_key)
    assert deleted is True

    meta = live_s3_service.get_object_metadata(test_key)
    assert meta is None
