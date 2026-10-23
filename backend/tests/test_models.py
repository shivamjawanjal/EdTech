import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, hash_token
from app.models import (
    User,
    StudentProfile,
    RefreshToken,
    Batch,
    Course,
    CourseBatch,
    Enrollment,
    Subject,
    Chapter,
    Lecture,
    Assignment,
    Submission,
    SubmissionAttachment,
    Test,
    Question,
    TestAttempt,
    TestAnswer,
    LiveSession,
    LiveAttendanceRecord,
    Notification,
)


@pytest.mark.asyncio
async def test_user_creation_and_role_constraint(db_session: AsyncSession):
    """Verify that users can be created with valid roles and reject invalid roles via check constraint."""
    valid_user = User(
        phone="+919811111111",
        email="student.test@edtechweb.local",
        hashed_password=hash_password("SecurePassword123!"),
        full_name="Test Student",
        role="student",
    )
    db_session.add(valid_user)
    await db_session.flush()
    assert valid_user.id is not None
    assert valid_user.role == "student"
    assert valid_user.is_active is True
    assert valid_user.created_at.tzinfo is not None  # Timezone-aware

    # Attempt invalid role
    invalid_user = User(
        phone="+919822222222",
        email="invalid.role@edtechweb.local",
        hashed_password="hash",
        full_name="Invalid Role User",
        role="admin",  # Invalid role
    )
    db_session.add(invalid_user)
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_security_credentials_never_plaintext(db_session: AsyncSession):
    """Verify that password hashes and refresh tokens are strictly persisted as secure hashes."""
    raw_password = "TeacherPasswordSecret999!"
    raw_token = "high_entropy_refresh_token_string_abc_123"

    pw_hash = hash_password(raw_password)
    assert pw_hash != raw_password
    assert verify_password(raw_password, pw_hash) is True

    tok_hash = hash_token(raw_token)
    assert tok_hash != raw_token

    user = User(
        phone="+919833333333",
        email="security.test@edtechweb.local",
        hashed_password=pw_hash,
        full_name="Security Audit User",
        role="teacher",
    )
    db_session.add(user)
    await db_session.flush()

    token_record = RefreshToken(
        user_id=user.id,
        token_hash=tok_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(token_record)
    await db_session.flush()

    # Query back from DB
    result = await db_session.execute(select(User).where(User.id == user.id))
    fetched_user = result.scalar_one()
    assert fetched_user.hashed_password.startswith("$2b$")

    tok_result = await db_session.execute(select(RefreshToken).where(RefreshToken.user_id == user.id))
    fetched_token = tok_result.scalar_one()
    assert fetched_token.token_hash == tok_hash


@pytest.mark.asyncio
async def test_course_to_batch_many_to_many(db_session: AsyncSession):
    """Verify that a course can be associated with multiple batches via course_batches."""
    b1 = Batch(name="Test Batch A", academic_year="2026-2027")
    b2 = Batch(name="Test Batch B", academic_year="2026-2027")
    c = Course(title="Shared STEM Course", slug="shared-stem-course-test")
    db_session.add_all([b1, b2, c])
    await db_session.flush()

    # Associate course with both batches
    cb1 = CourseBatch(course_id=c.id, batch_id=b1.id)
    cb2 = CourseBatch(course_id=c.id, batch_id=b2.id)
    db_session.add_all([cb1, cb2])
    await db_session.flush()

    # Duplicate association should violate uniqueness
    cb_dup = CourseBatch(course_id=c.id, batch_id=b1.id)
    db_session.add(cb_dup)
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_submission_versioning_and_latest_constraint(db_session: AsyncSession):
    """Verify that resubmission attempts are versioned and only one is_latest=True exists per student."""
    teacher = User(
        phone="+919844444441",
        email="t.sub@edtechweb.local",
        hashed_password=hash_password("pw"),
        full_name="Teacher Sub",
        role="teacher",
    )
    student = User(
        phone="+919844444442",
        email="s.sub@edtechweb.local",
        hashed_password=hash_password("pw"),
        full_name="Student Sub",
        role="student",
    )
    course = Course(title="Sub Course", slug="sub-course-test")
    db_session.add_all([teacher, student, course])
    await db_session.flush()

    subject = Subject(course_id=course.id, name="Math", code="MTH")
    db_session.add(subject)
    await db_session.flush()

    chapter = Chapter(subject_id=subject.id, title="Ch1", order_index=1)
    db_session.add(chapter)
    await db_session.flush()

    lecture = Lecture(chapter_id=chapter.id, title="L1", order_index=1)
    db_session.add(lecture)
    await db_session.flush()

    assignment = Assignment(
        lecture_id=lecture.id,
        title="HW 1",
        instructions="Worksheet",
        max_marks=10,
        deadline=datetime.now(timezone.utc) + timedelta(days=2),
    )
    db_session.add(assignment)
    await db_session.flush()

    # Attempt 1: resubmission requested (is_latest=False)
    sub1 = Submission(
        assignment_id=assignment.id,
        student_id=student.id,
        attempt_number=1,
        is_latest=False,
        status="resubmission_requested",
        teacher_feedback="Blurry image, please re-upload",
    )
    # Attempt 2: new submission (is_latest=True)
    sub2 = Submission(
        assignment_id=assignment.id,
        student_id=student.id,
        attempt_number=2,
        is_latest=True,
        status="submitted",
    )
    db_session.add_all([sub1, sub2])
    await db_session.flush()
    assert sub1.id is not None
    assert sub2.id is not None

    # Adding a second is_latest=True for the same assignment and student must violate partial unique index
    sub_invalid_latest = Submission(
        assignment_id=assignment.id,
        student_id=student.id,
        attempt_number=3,
        is_latest=True,  # Conflict with sub2
        status="submitted",
    )
    db_session.add(sub_invalid_latest)
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_live_attendance_evidence_vs_verified(db_session: AsyncSession):
    """Verify that click-through evidence is recorded distinctly from verified participation."""
    teacher = User(
        phone="+919855555551",
        email="t.live@edtechweb.local",
        hashed_password=hash_password("pw"),
        full_name="Teacher Live",
        role="teacher",
    )
    student = User(
        phone="+919855555552",
        email="s.live@edtechweb.local",
        hashed_password=hash_password("pw"),
        full_name="Student Live",
        role="student",
    )
    batch = Batch(name="Live Batch", academic_year="2026-2027")
    db_session.add_all([teacher, student, batch])
    await db_session.flush()

    session = LiveSession(
        batch_id=batch.id,
        title="Live Problem Solving",
        scheduled_start_time=datetime.now(timezone.utc) + timedelta(hours=1),
        scheduled_end_time=datetime.now(timezone.utc) + timedelta(hours=2),
        meet_url="https://meet.google.com/test-live",
    )
    db_session.add(session)
    await db_session.flush()

    # Step 1: Student clicks link -> attendance evidence recorded (verified_participation = False)
    attendance = LiveAttendanceRecord(
        session_id=session.id,
        student_id=student.id,
        client_ip="192.168.1.100",
        user_agent="Mozilla/5.0 (Mobile)",
        verified_participation=False,
    )
    db_session.add(attendance)
    await db_session.flush()
    assert attendance.verified_participation is False
    assert attendance.click_through_at is not None

    # Step 2: Teacher verifies active participation
    attendance.verified_participation = True
    attendance.verified_by = teacher.id
    attendance.verification_notes = "Active participation in question 2."
    await db_session.flush()
    assert attendance.verified_participation is True
    assert attendance.verified_by == teacher.id


@pytest.mark.asyncio
async def test_test_attempt_and_answers_relationship(db_session: AsyncSession):
    """Verify that test attempts track answers per question and enforce attempt uniqueness."""
    student = User(
        phone="+919866666661",
        email="s.test@edtechweb.local",
        hashed_password=hash_password("pw"),
        full_name="Student Test MCQ",
        role="student",
    )
    course = Course(title="Test Course", slug="test-course-slug")
    db_session.add_all([student, course])
    await db_session.flush()

    subject = Subject(course_id=course.id, name="Math", code="MTH")
    db_session.add(subject)
    await db_session.flush()

    chapter = Chapter(subject_id=subject.id, title="Ch1", order_index=1)
    db_session.add(chapter)
    await db_session.flush()

    test = Test(
        chapter_id=chapter.id,
        title="Quiz 1",
        duration_minutes=15,
        total_marks=2,
        deadline=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(test)
    await db_session.flush()

    q1 = Question(
        test_id=test.id,
        question_text="2 + 2 = ?",
        options=[{"key": "A", "text": "4"}, {"key": "B", "text": "5"}],
        correct_option="A",
        marks=1,
        order_index=1,
    )
    q2 = Question(
        test_id=test.id,
        question_text="3 x 3 = ?",
        options=[{"key": "A", "text": "9"}, {"key": "B", "text": "6"}],
        correct_option="A",
        marks=1,
        order_index=2,
    )
    db_session.add_all([q1, q2])
    await db_session.flush()

    # Attempt 1
    attempt = TestAttempt(
        test_id=test.id,
        student_id=student.id,
        attempt_number=1,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db_session.add(attempt)
    await db_session.flush()

    a1 = TestAnswer(
        attempt_id=attempt.id,
        question_id=q1.id,
        selected_option="A",
        is_correct=True,
        marks_awarded=Decimal("1.00"),
    )
    a2 = TestAnswer(
        attempt_id=attempt.id,
        question_id=q2.id,
        selected_option="B",
        is_correct=False,
        marks_awarded=Decimal("0.00"),
    )
    db_session.add_all([a1, a2])
    await db_session.flush()

    assert a1.is_correct is True
    assert a2.is_correct is False

    # Duplicate answer for same question in attempt should fail
    a1_dup = TestAnswer(attempt_id=attempt.id, question_id=q1.id, selected_option="B")
    db_session.add(a1_dup)
    with pytest.raises(IntegrityError):
        await db_session.flush()
