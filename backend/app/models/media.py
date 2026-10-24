import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any, Dict
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, utc_now

if TYPE_CHECKING:
    from app.models.identity import User


class MediaUpload(Base, TimestampMixin):
    """
    Tracks direct-to-storage upload lifecycle, validation state,
    and server-generated object keys before publication into curriculum or assessment models.
    """
    __tablename__ = "media_uploads"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'VALIDATING', 'READY', 'REJECTED')",
            name="chk_media_uploads_status",
        ),
        CheckConstraint(
            "purpose IN ('lecture_video', 'lecture_note', 'submission_attachment')",
            name="chk_media_uploads_purpose",
        ),
        CheckConstraint(
            "declared_size_bytes > 0",
            name="chk_media_uploads_declared_size_positive",
        ),
        Index("ix_media_uploads_user_purpose", "user_id", "purpose"),
        Index("ix_media_uploads_status", "status"),
        Index("ix_media_uploads_object_key", "object_key", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    bucket_name: Mapped[str] = mapped_column(String(100), nullable=False)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    declared_mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    detected_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    declared_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actual_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    upload_url_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
