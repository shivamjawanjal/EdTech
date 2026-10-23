import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.identity import User


class StudentHealthSummary(Base):
    __tablename__ = "student_health_summaries"
    __table_args__ = (
        CheckConstraint(
            "health_status IN ('ON_TRACK', 'NEEDS_ATTENTION', 'AT_RISK')",
            name="chk_student_health_status",
        ),
        Index("ix_student_health_status_time", "health_status", "last_calculated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    health_status: Mapped[str] = mapped_column(String(20), default="ON_TRACK", nullable=False)
    assignment_submission_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("100.00"), nullable=False
    )
    video_watch_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("100.00"), nullable=False
    )
    test_score_average: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("75.00"), nullable=False
    )
    consecutive_missing_assignments: Mapped[int] = mapped_column(
        SmallInteger, default=0, nullable=False
    )
    days_inactive: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    explainability_reason: Mapped[str] = mapped_column(
        Text, default="Initial enrolment baseline", nullable=False
    )
    last_calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationship back to User
    student: Mapped["User"] = relationship("User", back_populates="health_summary")


class StudentActivity(Base):
    __tablename__ = "student_activities"
    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('LOGIN', 'WATCH_LECTURE', 'SUBMIT_ASSIGNMENT', 'ATTEMPT_TEST', 'JOIN_LIVE', 'ASK_DOUBT')",
            name="chk_student_activities_type",
        ),
        Index("ix_student_activities_student_time", "student_id", "created_at"),
        Index("ix_student_activities_type_time", "activity_type", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    metadata_: Mapped[Optional[Any]] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationship back to User
    student: Mapped["User"] = relationship("User")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_actor_time", "actor_id", "created_at"),
        Index("ix_audit_events_target", "target_entity_type", "target_entity_id"),
        Index("ix_audit_events_action_time", "action", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    previous_state: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    new_state: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationship back to User
    actor: Mapped["User"] = relationship("User")
