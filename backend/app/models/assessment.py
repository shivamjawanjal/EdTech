import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List, Any
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, utc_now

if TYPE_CHECKING:
    from app.models.identity import User
    from app.models.curriculum import Lecture, Chapter


class Assignment(Base, TimestampMixin):
    __tablename__ = "assignments"
    __table_args__ = (
        CheckConstraint("max_marks > 0", name="chk_assignments_max_marks_positive"),
        Index("ix_assignments_lecture_id", "lecture_id"),
        Index("ix_assignments_deadline", "deadline"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lecture_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    question_sheet_s3_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    max_marks: Mapped[int] = mapped_column(SmallInteger, default=10, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    allow_late_submission: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    late_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="assignments")
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission", back_populates="assignment", cascade="all, delete-orphan"
    )


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", "attempt_number", name="uq_submissions_attempt"),
        CheckConstraint("attempt_number >= 1", name="chk_submissions_attempt_positive"),
        CheckConstraint("obtained_marks IS NULL OR obtained_marks >= 0", name="chk_submissions_marks_positive"),
        CheckConstraint(
            "status IN ('submitted', 'late', 'resubmission_requested', 'evaluated')",
            name="chk_submissions_status",
        ),
        Index(
            "ix_submissions_grading_queue",
            "assignment_id",
            "is_latest",
            "is_evaluated",
            postgresql_where=text("is_latest = TRUE AND is_evaluated = FALSE"),
        ),
        Index(
            "uq_submissions_single_latest",
            "assignment_id",
            "student_id",
            unique=True,
            postgresql_where=text("is_latest = TRUE"),
        ),
        Index("ix_submissions_student_latest", "student_id", "assignment_id", "is_latest"),
        Index("ix_submissions_submitted_at", "submitted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="submitted", nullable=False)
    student_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    is_evaluated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    obtained_marks: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    teacher_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    evaluated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    is_released: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="submissions")
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])
    evaluator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[evaluated_by])
    attachments: Mapped[List["SubmissionAttachment"]] = relationship(
        "SubmissionAttachment",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="SubmissionAttachment.page_order",
    )


class SubmissionAttachment(Base):
    __tablename__ = "submission_attachments"
    __table_args__ = (
        CheckConstraint(
            "file_size_bytes > 0 AND file_size_bytes <= 15728640",
            name="chk_submission_attachments_size_15mb",
        ),
        CheckConstraint(
            "mime_type IN ('image/jpeg', 'image/png', 'image/webp', 'application/pdf')",
            name="chk_submission_attachments_mime",
        ),
        CheckConstraint("page_order >= 1", name="chk_submission_attachments_order_positive"),
        Index("ix_submission_attachments_sub_order", "submission_id", "page_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False
    )
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    page_order: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationship back to Submission
    submission: Mapped["Submission"] = relationship("Submission", back_populates="attachments")


class Test(Base, TimestampMixin):
    __test__ = False
    __tablename__ = "tests"
    __table_args__ = (
        CheckConstraint(
            "duration_minutes > 0 AND duration_minutes <= 180",
            name="chk_tests_duration_valid",
        ),
        CheckConstraint("total_marks >= 0", name="chk_tests_total_marks_positive"),
        CheckConstraint(
            "pass_percentage BETWEEN 0 AND 100",
            name="chk_tests_pass_percentage_valid",
        ),
        CheckConstraint("max_attempts >= 1", name="chk_tests_max_attempts_positive"),
        Index("ix_tests_chapter_deadline", "chapter_id", "deadline"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    total_marks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pass_percentage: Mapped[int] = mapped_column(SmallInteger, default=40, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_attempts: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    solutions_released_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    results_released_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="tests")
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="test", cascade="all, delete-orphan", order_by="Question.order_index"
    )
    attempts: Mapped[List["TestAttempt"]] = relationship(
        "TestAttempt", back_populates="test", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint("correct_option IN ('A', 'B', 'C', 'D')", name="chk_questions_correct_option"),
        CheckConstraint("marks > 0", name="chk_questions_marks_positive"),
        CheckConstraint("negative_marks >= 0", name="chk_questions_negative_marks_positive"),
        Index("ix_questions_test_order", "test_id", "order_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tests.id", ondelete="CASCADE"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_image_s3_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    options: Mapped[List[Any]] = mapped_column(JSONB, nullable=False)
    correct_option: Mapped[str] = mapped_column(String(5), nullable=False)
    marks: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    negative_marks: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.00"), nullable=False)
    solution_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationship back to Test
    test: Mapped["Test"] = relationship("Test", back_populates="questions")


class TestAttempt(Base):
    __test__ = False
    __tablename__ = "test_attempts"
    __table_args__ = (
        UniqueConstraint("test_id", "student_id", "attempt_number", name="uq_test_attempts_attempt"),
        CheckConstraint("attempt_number >= 1", name="chk_test_attempts_num_positive"),
        CheckConstraint("submitted_at IS NULL OR submitted_at >= started_at", name="chk_test_attempt_timestamps"),
        Index("ix_test_attempts_test_score", "test_id", "is_completed", "score"),
        Index("ix_test_attempts_student_test", "student_id", "test_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tests.id", ondelete="RESTRICT"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0.00"), nullable=False)
    total_questions_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    correct_answers_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    incorrect_answers_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    unattempted_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    test: Mapped["Test"] = relationship("Test", back_populates="attempts")
    student: Mapped["User"] = relationship("User")
    answers: Mapped[List["TestAnswer"]] = relationship(
        "TestAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )


class TestAnswer(Base):
    __test__ = False
    __tablename__ = "test_answers"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_test_answers_attempt_question"),
        CheckConstraint("selected_option IS NULL OR selected_option IN ('A', 'B', 'C', 'D')", name="chk_test_answers_option"),
        Index("ix_test_answers_question_correct", "question_id", "is_correct"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_attempts.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False
    )
    selected_option: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    marks_awarded: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.00"), nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    attempt: Mapped["TestAttempt"] = relationship("TestAttempt", back_populates="answers")
    question: Mapped["Question"] = relationship("Question")
