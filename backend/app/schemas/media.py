import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from app.schemas.common import BaseSchema

PurposeType = Literal["lecture_video", "lecture_note", "submission_attachment"]


class MediaUploadInitRequest(BaseModel):
    purpose: PurposeType
    target_id: uuid.UUID
    file_name: str = Field(..., min_length=1, max_length=255)
    declared_size_bytes: int = Field(..., gt=0)
    declared_mime_type: str = Field(..., min_length=3, max_length=100)
    extra_metadata: Optional[Dict[str, Any]] = None

    @field_validator("file_name")
    @classmethod
    def sanitize_file_name(cls, v: str) -> str:
        # Strip path traversal characters
        cleaned = v.replace("\\", "/").split("/")[-1].strip()
        if not cleaned:
            raise ValueError("Invalid file name")
        return cleaned


class MediaUploadInitResponse(BaseModel):
    upload_id: uuid.UUID
    upload_url: str
    object_key: str
    bucket_name: str
    expires_in_seconds: int
    headers: Dict[str, str]


class MediaUploadCompleteResponse(BaseModel):
    upload_id: uuid.UUID
    status: str
    purpose: str
    target_id: uuid.UUID
    object_key: str
    actual_size_bytes: int
    detected_mime_type: str
    validated_at: datetime


class MediaPlaybackResponse(BaseModel):
    playback_url: str
    expires_in_seconds: int
    mime_type: Optional[str]
    title: str
    duration_seconds: int


class MediaDownloadResponse(BaseModel):
    download_url: str
    expires_in_seconds: int
    file_name: str
    file_size_bytes: Optional[int] = None
