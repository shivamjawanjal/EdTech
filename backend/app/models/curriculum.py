import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.enrolment import Course
    from app.models.assessment import Assignment, Test
    from app.models.telemetry import VideoProgress, VideoWatchSession
    from app.models.communication import DoubtThread


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("course_id", "name", name="uq_subjects_course_name"),
        Index("ix_subjects_course_order", "course_id", "order_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    icon_slug: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="subjects")
    chapters: Mapped[List["Chapter"]] = relationship(
        "Chapter", back_populates="subject", cascade="all, delete-orphan", order_by="Chapter.order_index"
    )


class Chapter(Base, TimestampMixin):
    __tablename__ = "chapters"
    __table_args__ = (
        Index("ix_chapters_subject_order", "subject_id", "order_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="chapters")
    lectures: Mapped[List["Lecture"]] = relationship(
        "Lecture", back_populates="chapter", cascade="all, delete-orphan", order_by="Lecture.order_index"
    )
    tests: Mapped[List["Test"]] = relationship(
        "Test", back_populates="chapter", cascade="all, delete-orphan"
    )


class Lecture(Base, TimestampMixin):
    __tablename__ = "lectures"
    __table_args__ = (
        CheckConstraint("duration_seconds >= 0", name="chk_lectures_duration_positive"),
        Index("ix_lectures_chapter_order", "chapter_id", "order_index"),
        Index("ix_lectures_published_at", "published_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    video_s3_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_mime_type: Mapped[Optional[str]] = mapped_column(String(50), default="video/mp4", nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="lectures")
    notes: Mapped[List["LectureNote"]] = relationship(
        "LectureNote", back_populates="lecture", cascade="all, delete-orphan", order_by="LectureNote.order_index"
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment", back_populates="lecture", cascade="all, delete-orphan"
    )


class LectureNote(Base, TimestampMixin):
    __tablename__ = "lecture_notes"
    __table_args__ = (
        CheckConstraint("file_size_bytes > 0", name="chk_lecture_notes_size_positive"),
        Index("ix_lecture_notes_lecture_order", "lecture_id", "order_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lecture_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    pdf_s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    allow_download: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationship back to Lecture
    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="notes")
