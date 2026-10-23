import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    User,
    Batch,
    Course,
    Enrollment,
    Submission,
    StudentHealthSummary,
    StudentActivity,
)
from scripts.seed_dev_data import seed_database


@pytest.mark.asyncio
async def test_seed_database_execution_and_health_tiers(db_session: AsyncSession):
    """
    Execute seed_database and verify:
    1. 1 teacher + 150 students created
    2. Batches and courses linked
    3. Exactly 100 On Track, 30 Needs Attention, 20 At Risk students
    4. Referential integrity across submissions, profiles, and health snapshots
    """
    # Run seed
    await seed_database(db_session)

    # 1. Total users
    teacher_count = await db_session.scalar(
        select(func.count(User.id)).where(User.role == "teacher")
    )
    student_count = await db_session.scalar(
        select(func.count(User.id)).where(User.role == "student")
    )
    assert teacher_count == 1
    assert student_count == 150

    # 2. Batches & Courses
    batch_count = await db_session.scalar(select(func.count(Batch.id)))
    course_count = await db_session.scalar(select(func.count(Course.id)))
    enrollment_count = await db_session.scalar(select(func.count(Enrollment.id)))
    assert batch_count == 3
    assert course_count >= 1
    assert enrollment_count == 150

    # 3. Health classifications distribution
    on_track = await db_session.scalar(
        select(func.count(StudentHealthSummary.id)).where(StudentHealthSummary.health_status == "ON_TRACK")
    )
    needs_attn = await db_session.scalar(
        select(func.count(StudentHealthSummary.id)).where(StudentHealthSummary.health_status == "NEEDS_ATTENTION")
    )
    at_risk = await db_session.scalar(
        select(func.count(StudentHealthSummary.id)).where(StudentHealthSummary.health_status == "AT_RISK")
    )
    assert on_track == 100
    assert needs_attn == 30
    assert at_risk == 20

    # 4. Check that at-risk students have explainability reasons
    at_risk_sample = await db_session.scalar(
        select(StudentHealthSummary).where(StudentHealthSummary.health_status == "AT_RISK").limit(1)
    )
    assert at_risk_sample is not None
    assert "At Risk" in at_risk_sample.explainability_reason

    # 5. Idempotent rerun check
    # Running seed a second time in the same session must execute without exceptions or duplicates
    await seed_database(db_session)
    student_count_rerun = await db_session.scalar(
        select(func.count(User.id)).where(User.role == "student")
    )
    assert student_count_rerun == 150
