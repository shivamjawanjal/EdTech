import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, utc_now

if TYPE_CHECKING:
    from app.models.identity import User
    from app.models.enrolment import Batch
    from app.models.curriculum import Subject, Lecture
    from app.models.assessment import Assignment


class DoubtThread(Base, TimestampMixin):
    __tablename__ = "doubt_threads"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'resolved', 'closed')", name="chk_doubt_threads_status"),
        Index("ix_doubt_threads_student_status", "student_id", "status"),
        Index(
            "ix_doubt_threads_open_triage",
            "status",
            "created_at",
            postgresql_where=text("status = 'open'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    lecture_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lectures.id", ondelete="SET NULL"), nullable=True
    )
    assignment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="SET NULL"), nullable=True
    )
    lecture_timestamp_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    student: Mapped["User"] = relationship("User")
    lecture: Mapped[Optional["Lecture"]] = relationship("Lecture")
    assignment: Mapped[Optional["Assignment"]] = relationship("Assignment")
    messages: Mapped[List["DoubtMessage"]] = relationship(
        "DoubtMessage", back_populates="thread", cascade="all, delete-orphan", order_by="DoubtMessage.created_at"
    )


class DoubtMessage(Base):
    __tablename__ = "doubt_messages"
    __table_args__ = (
        Index("ix_doubt_messages_thread_time", "thread_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doubt_threads.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_s3_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    thread: Mapped["DoubtThread"] = relationship("DoubtThread", back_populates="messages")
    sender: Mapped["User"] = relationship("User")


class LiveSession(Base, TimestampMixin):
    __tablename__ = "live_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'live', 'completed', 'cancelled')",
            name="chk_live_sessions_status",
        ),
        Index("ix_live_sessions_batch_time", "batch_id", "scheduled_start_time"),
        Index("ix_live_sessions_status_time", "status", "scheduled_start_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    scheduled_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    meet_url: Mapped[str] = mapped_column(String(500), nullable=False)
    recording_lecture_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lectures.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="scheduled", nullable=False)

    # Relationships
    batch: Mapped["Batch"] = relationship("Batch", back_populates="live_sessions")
    subject: Mapped[Optional["Subject"]] = relationship("Subject")
    attendance_records: Mapped[List["LiveAttendanceRecord"]] = relationship(
        "LiveAttendanceRecord", back_populates="session", cascade="all, delete-orphan"
    )


class LiveAttendanceRecord(Base):
    __tablename__ = "live_attendance_records"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_live_attendance_session_student"),
        Index("ix_live_attendance_session_verified", "session_id", "verified_participation"),
        Index("ix_live_attendance_student_session", "student_id", "session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("live_sessions.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    click_through_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    client_ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    verified_participation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    session: Mapped["LiveSession"] = relationship("LiveSession", back_populates="attendance_records")
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])
    verifier: Mapped[Optional["User"]] = relationship("User", foreign_keys=[verified_by])


class Announcement(Base):
    __tablename__ = "announcements"
    __table_args__ = (
        CheckConstraint("priority IN ('normal', 'urgent', 'pinned')", name="chk_announcements_priority"),
        Index("ix_announcements_batch_created", "batch_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batches.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    message_body: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    batch: Mapped[Optional["Batch"]] = relationship("Batch")
    author: Mapped["User"] = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index(
            "ix_notifications_user_unread",
            "user_id",
            "is_read",
            "created_at",
            postgresql_where=text("is_read = FALSE"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationship back to User
    user: Mapped["User"] = relationship("User")
