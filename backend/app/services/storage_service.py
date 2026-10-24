"""
Object Storage Abstraction Service.

Supports:
1. AWS S3
2. Cloudflare R2 (S3-compatible via endpoint_url)
3. Mock Storage Adapter (for zero-cloud local testing and CI)

Enforces:
- Private buckets by default
- Server-generated object keys
- Short-lived signed URLs with strict TTLs
- Object head byte inspection for signature validation
"""
import abc
import hmac
import hashlib
import time
import urllib.parse
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

from app.core.config import Settings, get_settings

try:
    import boto3
    from botocore.client import Config
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    ClientError = Exception


@dataclass
class UploadTicket:
    upload_url: str
    object_key: str
    bucket: str
    expires_in_seconds: int
    headers: Dict[str, str]


@dataclass
class ObjectMetadata:
    object_key: str
    content_length: int
    content_type: Optional[str] = None
    etag: Optional[str] = None


class BaseStorageService(abc.ABC):
    """Abstract interface for secure cloud object storage."""

    @abc.abstractmethod
    def generate_upload_url(
        self,
        object_key: str,
        content_type: str,
        max_size_bytes: int,
        expires_in: int = 900,
    ) -> UploadTicket:
        """Generate a short-lived pre-signed PUT URL for direct client-to-storage transfer."""
        pass

    @abc.abstractmethod
    def generate_download_url(
        self,
        object_key: str,
        filename: Optional[str] = None,
        disposition: str = "inline",
        expires_in: int = 900,
    ) -> str:
        """Generate a short-lived pre-signed GET URL for secure media access."""
        pass

    @abc.abstractmethod
    def get_object_metadata(self, object_key: str) -> Optional[ObjectMetadata]:
        """Fetch stored object metadata (size, content type) without downloading payload."""
        pass

    @abc.abstractmethod
    def get_object_header_bytes(self, object_key: str, byte_count: int = 512) -> Optional[bytes]:
        """Fetch the first N bytes of the object for magic byte signature validation."""
        pass

    @abc.abstractmethod
    def delete_object(self, object_key: str) -> bool:
        """Delete an object from private bucket."""
        pass


class MockStorageService(BaseStorageService):
    """
    In-Memory / Deterministic Mock Storage Adapter.
    Enables thorough automated testing and offline development without cloud credentials.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.bucket = settings.S3_BUCKET_NAME
        self.secret_key = settings.JWT_SECRET_KEY.encode("utf-8")
        # In-memory storage of objects: object_key -> bytes
        self._mock_objects: Dict[str, bytes] = {}
        # Metadata storage: object_key -> {content_type, size}
        self._mock_metadata: Dict[str, Dict[str, Any]] = {}

    def store_mock_object(self, object_key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Utility for test suites to simulate a completed upload directly into mock storage."""
        self._mock_objects[object_key] = data
        self._mock_metadata[object_key] = {
            "content_length": len(data),
            "content_type": content_type,
            "etag": hashlib.md5(data).hexdigest(),
        }

    def _sign_url(self, path: str, expires_at: int, operation: str) -> str:
        msg = f"{operation}:{path}:{expires_at}".encode("utf-8")
        sig = hmac.new(self.secret_key, msg, hashlib.sha256).hexdigest()
        base = self.settings.MEDIA_PUBLIC_BASE_URL or "https://mock-storage.edtech.local"
        return f"{base}/{self.bucket}/{path}?operation={operation}&expires={expires_at}&signature={sig}"

    def generate_upload_url(
        self,
        object_key: str,
        content_type: str,
        max_size_bytes: int,
        expires_in: int = 900,
    ) -> UploadTicket:
        expires_at = int(time.time()) + expires_in
        signed_url = self._sign_url(object_key, expires_at, "PUT")
        return UploadTicket(
            upload_url=signed_url,
            object_key=object_key,
            bucket=self.bucket,
            expires_in_seconds=expires_in,
            headers={
                "Content-Type": content_type,
            },
        )

    def generate_download_url(
        self,
        object_key: str,
        filename: Optional[str] = None,
        disposition: str = "inline",
        expires_in: int = 900,
    ) -> str:
        expires_at = int(time.time()) + expires_in
        signed_url = self._sign_url(object_key, expires_at, "GET")
        if filename:
            safe_filename = urllib.parse.quote(filename)
            signed_url += f"&disposition={disposition}&filename={safe_filename}"
        return signed_url

    def get_object_metadata(self, object_key: str) -> Optional[ObjectMetadata]:
        if object_key not in self._mock_objects:
            return None
        meta = self._mock_metadata.get(object_key, {})
        return ObjectMetadata(
            object_key=object_key,
            content_length=len(self._mock_objects[object_key]),
            content_type=meta.get("content_type"),
            etag=meta.get("etag"),
        )

    def get_object_header_bytes(self, object_key: str, byte_count: int = 512) -> Optional[bytes]:
        data = self._mock_objects.get(object_key)
        if data is None:
            return None
        return data[:byte_count]

    def delete_object(self, object_key: str) -> bool:
        if object_key in self._mock_objects:
            del self._mock_objects[object_key]
            self._mock_metadata.pop(object_key, None)
            return True
        return False


class S3StorageService(BaseStorageService):
    """
    AWS S3 and Cloudflare R2 Provider Adapter.
    Configured via environment variables for bucket, endpoint, region, and credentials.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.bucket = settings.S3_BUCKET_NAME
        if not BOTO3_AVAILABLE:
            raise RuntimeError("boto3 is required for S3StorageService. Install boto3>=1.34.0")

        client_kwargs: Dict[str, Any] = {
            "service_name": "s3",
            "region_name": settings.S3_REGION if settings.S3_REGION != "auto" else "us-east-1",
            "config": Config(
                signature_version="s3v4",
                s3={"addressing_style": "virtual" if not settings.S3_ENDPOINT_URL else "path"},
            ),
        }

        if settings.S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        if settings.S3_ACCESS_KEY_ID and settings.S3_SECRET_ACCESS_KEY:
            client_kwargs["aws_access_key_id"] = settings.S3_ACCESS_KEY_ID
            client_kwargs["aws_secret_access_key"] = settings.S3_SECRET_ACCESS_KEY

        self.client = boto3.client(**client_kwargs)

    def generate_upload_url(
        self,
        object_key: str,
        content_type: str,
        max_size_bytes: int,
        expires_in: int = 900,
    ) -> UploadTicket:
        params = {
            "Bucket": self.bucket,
            "Key": object_key,
            "ContentType": content_type,
        }
        signed_url = self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=expires_in,
        )
        return UploadTicket(
            upload_url=signed_url,
            object_key=object_key,
            bucket=self.bucket,
            expires_in_seconds=expires_in,
            headers={
                "Content-Type": content_type,
            },
        )

    def generate_download_url(
        self,
        object_key: str,
        filename: Optional[str] = None,
        disposition: str = "inline",
        expires_in: int = 900,
    ) -> str:
        params: Dict[str, Any] = {
            "Bucket": self.bucket,
            "Key": object_key,
        }
        if filename:
            safe_name = urllib.parse.quote(filename)
            params["ResponseContentDisposition"] = f'{disposition}; filename="{safe_name}"'
        else:
            params["ResponseContentDisposition"] = disposition

        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params=params,
            ExpiresIn=expires_in,
        )

    def get_object_metadata(self, object_key: str) -> Optional[ObjectMetadata]:
        try:
            resp = self.client.head_object(Bucket=self.bucket, Key=object_key)
            return ObjectMetadata(
                object_key=object_key,
                content_length=resp["ContentLength"],
                content_type=resp.get("ContentType"),
                etag=resp.get("ETag", "").strip('"'),
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchKey", "NotFound"):
                return None
            raise

    def get_object_header_bytes(self, object_key: str, byte_count: int = 512) -> Optional[bytes]:
        try:
            resp = self.client.get_object(
                Bucket=self.bucket,
                Key=object_key,
                Range=f"bytes=0-{byte_count - 1}",
            )
            return resp["Body"].read()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchKey", "NotFound"):
                return None
            raise

    def delete_object(self, object_key: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError:
            return False


# Global singleton cache for mock storage so multiple calls retain uploaded objects in test run
_mock_storage_instance: Optional[MockStorageService] = None


def get_storage_service(settings: Optional[Settings] = None) -> BaseStorageService:
    """Factory dependency providing configured object storage service."""
    global _mock_storage_instance
    if settings is None:
        settings = get_settings()

    provider = settings.STORAGE_PROVIDER.lower()
    if provider in ("s3", "r2"):
        return S3StorageService(settings)

    if _mock_storage_instance is None:
        _mock_storage_instance = MockStorageService(settings)
    return _mock_storage_instance
