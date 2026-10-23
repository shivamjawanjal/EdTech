import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.identity import User
    from app.models.curriculum import Lecture


class VideoProgress(Base):
    __tablename__ = "video_progress"
    __table_args__ = (
        UniqueConstraint("student_id", "lecture_id", name="uq_video_progress_student_lecture"),
        CheckConstraint("seconds_watched >= 0", name="chk_video_progress_seconds_positive"),
        CheckConstraint("last_position_seconds >= 0", name="chk_video_progress_pos_positive"),
        CheckConstraint("completion_percentage BETWEEN 0 AND 100", name="chk_video_progress_percentage"),
        Index("ix_video_progress_lecture_completed", "lecture_id", "is_completed"),
        Index("ix_video_progress_student_heartbeat", "student_id", "last_heartbeat_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    lecture_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False
    )
    seconds_watched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_position_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_percentage: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    first_watched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    student: Mapped["User"] = relationship("User")
    lecture: Mapped["Lecture"] = relationship("Lecture")


class VideoWatchSession(Base):
    __tablename__ = "video_watch_sessions"
    __table_args__ = (
        CheckConstraint("session_duration_seconds > 0", name="chk_video_session_duration_positive"),
        Index("ix_video_watch_sessions_student_lecture", "student_id", "lecture_id", "recorded_at"),
        Index("ix_video_watch_sessions_recorded_at", "recorded_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    lecture_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False
    )
    session_start_position: Mapped[int] = mapped_column(Integer, nullable=False)
    session_end_position: Mapped[int] = mapped_column(Integer, nullable=False)
    session_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    playback_rate: Mapped[float] = mapped_column(Numeric(3, 2), default=1.00, nullable=False)
    client_ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    student: Mapped["User"] = relationship("User")
    lecture: Mapped["Lecture"] = relationship("Lecture")
