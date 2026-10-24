import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.base import utc_now
from app.models.identity import User, StudentProfile
from app.models.enrolment import Course, Batch, CourseBatch, Enrollment
from app.models.curriculum import Subject, Chapter, Lecture
from app.models.assessment import (
    Assignment,
    Submission,
    SubmissionAttachment,
    Test,
    Question,
    TestAttempt,
    TestAnswer,
)


@pytest_asyncio.fixture(scope="function")
async def assessment_fixture(db_session: AsyncSession, test_teacher: User, test_student: User):
    """
    Sets up a full assessment test fixture:
    - Course owned by test_teacher
    - Subject -> Chapter -> Lecture
    - Batch -> CourseBatch -> Enrollment for test_student
    - Second teacher (other_teacher) who owns another course
    - Second student (other_student) NOT enrolled in test_teacher's course
    """
    # 1. Course owned by test_teacher
    course = Course(
        title="Class 10 Science & Mathematics",
        slug="sci-math-" + uuid.uuid4().hex[:6],
        description="Comprehensive curriculum",
        is_published=True,
        instructor_id=test_teacher.id,
    )
    db_session.add(course)
    await db_session.flush()

    # 2. Subject, Chapter, Lecture
    subject = Subject(
        course_id=course.id,
        name="Physics",
        code="PHY-101",
        order_index=1,
    )
    db_session.add(subject)
    await db_session.flush()

    chapter = Chapter(
        subject_id=subject.id,
        title="Kinematics",
        order_index=1,
        is_published=True,
    )
    db_session.add(chapter)
    await db_session.flush()

    lecture = Lecture(
        chapter_id=chapter.id,
        title="Speed and Velocity",
        order_index=1,
        duration_seconds=3600,
        is_published=True,
    )
    db_session.add(lecture)
    await db_session.flush()

    # 3. Batch and Enrollment for test_student
    batch = Batch(
        name="Batch 2026 Alpha",
        academic_year="2026-2027",
        is_active=True,
    )
    db_session.add(batch)
    await db_session.flush()

    cb = CourseBatch(course_id=course.id, batch_id=batch.id)
    db_session.add(cb)

    enr = Enrollment(student_id=test_student.id, batch_id=batch.id, status="active")
    db_session.add(enr)
    await db_session.flush()

    # 4. Other teacher and other course
    other_teacher = User(
        phone="+919811111111",
        email="other_teacher@edtech.local",
        hashed_password=hash_password("Teacher123!"),
        full_name="Prof. Other Teacher",
        role="teacher",
        is_active=True,
    )
    db_session.add(other_teacher)
    await db_session.flush()

    other_course = Course(
        title="Class 11 Chemistry",
        slug="chem-11-" + uuid.uuid4().hex[:6],
        description="Chemistry course",
        is_published=True,
        instructor_id=other_teacher.id,
    )
    db_session.add(other_course)
    await db_session.flush()

    # 5. Other student NOT enrolled
    other_student = User(
        phone="+919822222222",
        email="other_student@edtech.local",
        hashed_password=hash_password("Student123!"),
        full_name="Unenrolled Student",
        role="student",
        is_active=True,
    )
    db_session.add(other_student)
    await db_session.flush()

    return {
        "teacher": test_teacher,
        "student": test_student,
        "other_teacher": other_teacher,
        "other_student": other_student,
        "course": course,
        "subject": subject,
        "chapter": chapter,
        "lecture": lecture,
        "batch": batch,
    }


def auth_header(user: User) -> dict:
    token = create_access_token(
        subject=str(user.id),
        role=user.role,
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Assignment Lifecycle & Student Submissions Tests
# =============================================================================


@pytest.mark.asyncio
async def test_teacher_create_assignment_success(client: AsyncClient, assessment_fixture: dict):
    teacher = assessment_fixture["teacher"]
    lecture = assessment_fixture["lecture"]

    payload = {
        "lecture_id": str(lecture.id),
        "title": "Daily Assignment 1: Kinematics",
        "instructions": "Solve problems 1 to 5 from Chapter 1",
        "max_marks": 20,
        "deadline": (utc_now() + timedelta(days=2)).isoformat(),
        "allow_late_submission": True,
        "late_deadline": (utc_now() + timedelta(days=4)).isoformat(),
        "is_published": True,
    }

    res = await client.post(
        "/api/v1/assessment/assignments",
        json=payload,
        headers=auth_header(teacher),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Daily Assignment 1: Kinematics"
    assert data["max_marks"] == 20
    assert data["is_published"] is True
    assert data["lecture_id"] == str(lecture.id)


@pytest.mark.asyncio
async def test_teacher_cannot_manage_another_teachers_assignment(client: AsyncClient, assessment_fixture: dict):
    other_teacher = assessment_fixture["other_teacher"]
    lecture = assessment_fixture["lecture"]  # Belongs to test_teacher's course

    payload = {
        "lecture_id": str(lecture.id),
        "title": "Unauthorized Assignment",
        "instructions": "Should fail",
        "max_marks": 10,
        "deadline": (utc_now() + timedelta(days=2)).isoformat(),
        "allow_late_submission": False,
        "is_published": True,
    }

    res = await client.post(
        "/api/v1/assessment/assignments",
        json=payload,
        headers=auth_header(other_teacher),
    )
    assert res.status_code == 403
    assert "not authorized" in (res.json().get("error") or res.json().get("detail", ""))


@pytest.mark.asyncio
async def test_student_cannot_create_assignment(client: AsyncClient, assessment_fixture: dict):
    student = assessment_fixture["student"]
    lecture = assessment_fixture["lecture"]

    res = await client.post(
        "/api/v1/assessment/assignments",
        json={
            "lecture_id": str(lecture.id),
            "title": "Student Malicious Assignment",
            "instructions": "Hacking",
            "max_marks": 10,
            "deadline": (utc_now() + timedelta(days=1)).isoformat(),
        },
        headers=auth_header(student),
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_unenrolled_student_cannot_access_or_submit_assignment(
    client: AsyncClient, db_session: AsyncSession, assessment_fixture: dict
):
    teacher = assessment_fixture["teacher"]
    other_student = assessment_fixture["other_student"]
    lecture = assessment_fixture["lecture"]

    # Teacher creates assignment
    assignment = Assignment(
        lecture_id=lecture.id,
        title="Private Assignment",
        instructions="Enrolled students only",
        max_marks=10,
        deadline=utc_now() + timedelta(days=2),
        is_published=True,
    )
    db_session.add(assignment)
    await db_session.commit()

    # Unenrolled student tries to view
    res = await client.get(
        f"/api/v1/assessment/assignments/{assignment.id}",
        headers=auth_header(other_student),
    )
    assert res.status_code == 403

    # Unenrolled student tries to submit
    sub_res = await client.post(
        f"/api/v1/assessment/assignments/{assignment.id}/submissions",
        json={"student_content": "Unenrolled attempt"},
        headers=auth_header(other_student),
    )
    assert sub_res.status_code == 403


@pytest.mark.asyncio
async def test_student_submit_assignment_and_deadline_enforcement(
    client: AsyncClient, db_session: AsyncSession, assessment_fixture: dict
):
    student = assessment_fixture["student"]
    lecture = assessment_fixture["lecture"]

    # 1. On-time assignment
    assignment = Assignment(
        lecture_id=lecture.id,
        title="On-time Test",
        instructions="Answer questions",
        max_marks=10,
        deadline=utc_now() + timedelta(days=1),
        allow_late_submission=True,
        is_published=True,
    )
    db_session.add(assignment)
    await db_session.commit()

    res = await client.post(
        f"/api/v1/assessment/assignments/{assignment.id}/submissions",
        json={"student_content": "My detailed response to question 1."},
        headers=auth_header(student),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "submitted"
    assert data["attempt_number"] == 1
    assert data["is_evaluated"] is False

    # 2. Closed assignment (deadline passed, no late submissions allowed)
    closed_assignment = Assignment(
        lecture_id=lecture.id,
        title="Closed Assignment",
        instructions="Expired",
        max_marks=10,
        deadline=utc_now() - timedelta(hours=2),
        allow_late_submission=False,
        is_published=True,
    )
    db_session.add(closed_assignment)
    await db_session.commit()

    closed_res = await client.post(
        f"/api/v1/assessment/assignments/{closed_assignment.id}/submissions",
        json={"student_content": "Late attempt"},
        headers=auth_header(student),
    )
    assert closed_res.status_code == 400
    assert "Late submissions are not permitted" in (closed_res.json().get("error") or closed_res.json().get("detail", ""))


@pytest.mark.asyncio
async def test_teacher_grading_and_result_release_workflow(
    client: AsyncClient, db_session: AsyncSession, assessment_fixture: dict
):
    teacher = assessment_fixture["teacher"]
    student = assessment_fixture["student"]
    lecture = assessment_fixture["lecture"]

    assignment = Assignment(
        lecture_id=lecture.id,
        title="Grading Workflow Assignment",
        instructions="Submit solutions",
        max_marks=20,
        deadline=utc_now() + timedelta(days=2),
        is_published=True,
    )
    db_session.add(assignment)
    await db_session.commit()

    # Student submits
    sub_res = await client.post(
        f"/api/v1/assessment/assignments/{assignment.id}/submissions",
        json={"student_content": "Here is my solution"},
        headers=auth_header(student),
    )
    assert sub_res.status_code == 201
    submission_id = sub_res.json()["id"]

    # Teacher grades as DRAFT (is_released=False)
    grade_res = await client.post(
        f"/api/v1/assessment/submissions/{submission_id}/grade",
        json={
            "obtained_marks": "18.50",
            "teacher_feedback": "Excellent derivations, small rounding slip in Q2",
            "is_released": False,
        },
        headers=auth_header(teacher),
    )
    assert grade_res.status_code == 200
    grade_data = grade_res.json()
    assert grade_data["is_evaluated"] is True
    assert grade_data["is_released"] is False
    assert grade_data["obtained_marks"] == "18.50"

    # CRITICAL: Student checks their submission - marks & feedback MUST BE REDACTED (None)
    student_view_res = await client.get(
        f"/api/v1/assessment/assignments/{assignment.id}",
        headers=auth_header(student),
    )
    assert student_view_res.status_code == 200
    my_sub = student_view_res.json()["my_submission"]
    assert my_sub is not None
    assert my_sub["obtained_marks"] is None
    assert my_sub["teacher_feedback"] is None
    assert my_sub["is_released"] is False

    # Teacher batch releases grades
    rel_res = await client.post(
        f"/api/v1/assessment/assignments/{assignment.id}/release-grades",
        headers=auth_header(teacher),
    )
    assert rel_res.status_code == 200

    # Student checks again - marks & feedback are now REVEALED
    student_view_after_release = await client.get(
        f"/api/v1/assessment/assignments/{assignment.id}",
        headers=auth_header(student),
    )
    my_sub_rel = student_view_after_release.json()["my_submission"]
    assert my_sub_rel["is_released"] is True
    assert my_sub_rel["obtained_marks"] == "18.50"
    assert my_sub_rel["teacher_feedback"] == "Excellent derivations, small rounding slip in Q2"


@pytest.mark.asyncio
async def test_teacher_cannot_award_marks_exceeding_max(
    client: AsyncClient, db_session: AsyncSession, assessment_fixture: dict
):
    teacher = assessment_fixture["teacher"]
    student = assessment_fixture["student"]
    lecture = assessment_fixture["lecture"]

    assignment = Assignment(
        lecture_id=lecture.id,
        title="Max Marks Enforcement",
        instructions="Work",
        max_marks=10,
        deadline=utc_now() + timedelta(days=1),
        is_published=True,
    )
    db_session.add(assignment)
    await db_session.commit()

    sub = Submission(
        assignment_id=assignment.id,
        student_id=student.id,
        attempt_number=1,
        is_latest=True,
        status="submitted",
        student_content="My answer",
    )
    db_session.add(sub)
    await db_session.commit()

    # Attempt to grade 15 on a 10-mark assignment
    res = await client.post(
        f"/api/v1/assessment/submissions/{sub.id}/grade",
        json={"obtained_marks": "15.00", "teacher_feedback": "Over maximum"},
        headers=auth_header(teacher),
    )
    assert res.status_code == 400
    assert "cannot exceed assignment maximum marks" in (res.json().get("error") or res.json().get("detail", ""))


# =============================================================================
# Timed MCQ Assessment Engine & Server-Authoritative Scoring Tests
# =============================================================================


@pytest.mark.asyncio
async def test_create_mcq_test_and_add_questions(
    client: AsyncClient, assessment_fixture: dict
):
    teacher = assessment_fixture["teacher"]
    chapter = assessment_fixture["chapter"]

    # 1. Create Test
    test_payload = {
        "chapter_id": str(chapter.id),
        "title": "Kinematics Weekly Assessment",
        "description": "Timed test covering 1D kinematics",
        "duration_minutes": 30,
        "pass_percentage": 50,
        "deadline": (utc_now() + timedelta(days=7)).isoformat(),
        "max_attempts": 2,
        "is_published": True,
    }
    res = await client.post(
        "/api/v1/assessment/tests",
        json=test_payload,
        headers=auth_header(teacher),
    )
    assert res.status_code == 201
    test_id = res.json()["id"]

    # 2. Add Question 1 (Positive marks: 4, Negative: 1)
    q1_payload = {
        "question_text": "A particle moves with uniform acceleration. Which graph is linear?",
        "options": [
            {"key": "A", "text": "Velocity-Time"},
            {"key": "B", "text": "Displacement-Time"},
            {"key": "C", "text": "Acceleration-Time"},
            {"key": "D", "text": "None of the above"},
        ],
        "correct_option": "A",
        "marks": 4,
        "negative_marks": "1.00",
        "solution_explanation": "v = u + at represents a straight line in the velocity-time plane.",
        "order_index": 1,
    }
    q1_res = await client.post(
        f"/api/v1/assessment/tests/{test_id}/questions",
        json=q1_payload,
        headers=auth_header(teacher),
    )
    assert q1_res.status_code == 201
    assert q1_res.json()["marks"] == 4

    # 3. Add Question 2
    q2_payload = {
        "question_text": "What is the SI unit of acceleration?",
        "options": [
            {"key": "A", "text": "m/s"},
            {"key": "B", "text": "m/s^2"},
            {"key": "C", "text": "km/h"},
            {"key": "D", "text": "N/m"},
        ],
        "correct_option": "B",
        "marks": 2,
        "negative_marks": "0.50",
        "solution_explanation": "Acceleration is rate of change of velocity, unit m/s^2.",
        "order_index": 2,
    }
    q2_res = await client.post(
        f"/api/v1/assessment/tests/{test_id}/questions",
        json=q2_payload,
        headers=auth_header(teacher),
    )
    assert q2_res.status_code == 201


@pytest.mark.asyncio
async def test_solution_redaction_for_students(
    client: AsyncClient, db_session: AsyncSession, assessment_fixture: dict
):
    teacher = assessment_fixture["teacher"]
    student = assessment_fixture["student"]
    chapter = assessment_fixture["chapter"]

    # Create test with solutions_released_at set in the FUTURE
    test = Test(
        chapter_id=chapter.id,
        title="Solutions Secret Test",
        duration_minutes=20,
        total_marks=5,
        deadline=utc_now() + timedelta(days=2),
        is_published=True,
        solutions_released_at=utc_now() + timedelta(days=3),
    )
    db_session.add(test)
    await db_session.flush()

    q = Question(
        test_id=test.id,
        question_text="Top secret question?",
        options=[{"key": "A", "text": "Secret A"}, {"key": "B", "text": "Option B"}],
        correct_option="A",
        marks=5,
        negative_marks=Decimal("1.00"),
        solution_explanation="Secret explanation revealed only later.",
    )
    db_session.add(q)
    await db_session.commit()

    # 1. Student views test -> correct_option and solution_explanation MUST BE NULL
    student_res = await client.get(
        f"/api/v1/assessment/tests/{test.id}",
        headers=auth_header(student),
    )
    assert student_res.status_code == 200
    st_q = student_res.json()["questions"][0]
    assert st_q["correct_option"] is None
    assert st_q["solution_explanation"] is None

    # 2. Teacher views test -> correct_option and solution_explanation are VISIBLE
    teacher_res = await client.get(
        f"/api/v1/assessment/tests/{test.id}",
        headers=auth_header(teacher),
    )
    assert teacher_res.status_code == 200
    tch_q = teacher_res.json()["questions"][0]
    assert tch_q["correct_option"] == "A"
    assert tch_q["solution_explanation"] == "Secret explanation revealed only later."


@pytest.mark.asyncio
async def test_timed_attempt_lifecycle_scoring_and_negative_marking(
    client: AsyncClient, db_session: AsyncSession, assessment_fixture: dict
):
    student = assessment_fixture["student"]
    chapter = assessment_fixture["chapter"]

    # Create test: 2 questions (Q1: 4 marks / -1 neg; Q2: 2 marks / -0.5 neg)
    test = Test(
        chapter_id=chapter.id,
        title="Scoring Test",
        duration_minutes=15,
        total_marks=6,
        pass_percentage=50,
        deadline=utc_now() + timedelta(days=2),
        max_attempts=2,
        is_published=True,
    )
    db_session.add(test)
    await db_session.flush()

    q1 = Question(
        test_id=test.id,
        question_text="Question 1",
        options=[{"key": "A", "text": "Correct A"}, {"key": "B", "text": "Wrong B"}],
        correct_option="A",
        marks=4,
        negative_marks=Decimal("1.00"),
        order_index=1,
    )
    q2 = Question(
        test_id=test.id,
        question_text="Question 2",
        options=[{"key": "A", "text": "Wrong A"}, {"key": "B", "text": "Correct B"}],
        correct_option="B",
        marks=2,
        negative_marks=Decimal("0.50"),
        order_index=2,
    )
    db_session.add_all([q1, q2])
    await db_session.commit()

    # 1. Start timed attempt (Server Authoritative)
    start_res = await client.post(
        f"/api/v1/assessment/tests/{test.id}/attempts/start",
        headers=auth_header(student),
    )
    assert start_res.status_code == 201
    start_data = start_res.json()
    attempt_id = start_data["attempt_id"]
    assert start_data["attempt_number"] == 1
    assert start_data["remaining_seconds"] == 15 * 60

    # 2. Save intermediate answers:
    # Q1: Select "A" (CORRECT => +4)
    save_q1 = await client.post(
        f"/api/v1/assessment/tests/attempts/{attempt_id}/save-answer",
        json={"question_id": str(q1.id), "selected_option": "A"},
        headers=auth_header(student),
    )
    assert save_q1.status_code == 200

    # Q2: Select "A" (INCORRECT => -0.50)
    save_q2 = await client.post(
        f"/api/v1/assessment/tests/attempts/{attempt_id}/save-answer",
        json={"question_id": str(q2.id), "selected_option": "A"},
        headers=auth_header(student),
    )
    assert save_q2.status_code == 200

    # 3. Submit attempt -> Server-Side Scoring
    # Expected score: 4.00 - 0.50 = 3.50 out of 6.00 (58.33%) => PASS
    submit_res = await client.post(
        f"/api/v1/assessment/tests/attempts/{attempt_id}/submit",
        headers=auth_header(student),
    )
    assert submit_res.status_code == 200
    result = submit_res.json()
    assert result["score"] == "3.50"
    assert result["total_marks"] == 6
    assert result["correct_count"] == 1
    assert result["incorrect_count"] == 1
    assert result["unattempted_count"] == 0
    assert result["passed"] is True
    assert result["is_completed"] is True


@pytest.mark.asyncio
async def test_attempt_limit_enforced_under_max_attempts(
    client: AsyncClient, db_session: AsyncSession, assessment_fixture: dict
):
    student = assessment_fixture["student"]
    chapter = assessment_fixture["chapter"]

    test = Test(
        chapter_id=chapter.id,
        title="Single Attempt Test",
        duration_minutes=10,
        total_marks=2,
        deadline=utc_now() + timedelta(days=1),
        max_attempts=1,  # Only 1 attempt allowed!
        is_published=True,
    )
    db_session.add(test)
    await db_session.flush()

    q = Question(
        test_id=test.id,
        question_text="Q",
        options=[{"key": "A", "text": "Opt A"}],
        correct_option="A",
        marks=2,
    )
    db_session.add(q)
    await db_session.commit()

    # Attempt 1: Start and submit
    att1_res = await client.post(
        f"/api/v1/assessment/tests/{test.id}/attempts/start",
        headers=auth_header(student),
    )
    assert att1_res.status_code == 201
    att1_id = att1_res.json()["attempt_id"]

    await client.post(
        f"/api/v1/assessment/tests/attempts/{att1_id}/submit",
        headers=auth_header(student),
    )

    # Attempt 2: Must be rejected with 400 (Maximum attempt limit reached)
    att2_res = await client.post(
        f"/api/v1/assessment/tests/{test.id}/attempts/start",
        headers=auth_header(student),
    )
    assert att2_res.status_code == 400
    assert "Maximum attempt limit of 1 reached" in (att2_res.json().get("error") or att2_res.json().get("detail", ""))


@pytest.mark.asyncio
async def test_cross_student_attempt_anti_idor(
    client: AsyncClient, db_session: AsyncSession, assessment_fixture: dict
):
    student = assessment_fixture["student"]
    other_student = assessment_fixture["other_student"]
    chapter = assessment_fixture["chapter"]

    test = Test(
        chapter_id=chapter.id,
        title="Anti IDOR Test",
        duration_minutes=10,
        total_marks=2,
        deadline=utc_now() + timedelta(days=1),
        is_published=True,
    )
    db_session.add(test)
    await db_session.flush()

    q = Question(
        test_id=test.id,
        question_text="Q",
        options=[{"key": "A", "text": "Opt A"}],
        correct_option="A",
        marks=2,
    )
    db_session.add(q)
    await db_session.commit()

    # Student starts attempt
    att_res = await client.post(
        f"/api/v1/assessment/tests/{test.id}/attempts/start",
        headers=auth_header(student),
    )
    attempt_id = att_res.json()["attempt_id"]

    # Other student attempts to save answer or submit student's attempt -> 403 Forbidden
    hack_save = await client.post(
        f"/api/v1/assessment/tests/attempts/{attempt_id}/save-answer",
        json={"question_id": str(q.id), "selected_option": "A"},
        headers=auth_header(other_student),
    )
    assert hack_save.status_code == 403

    hack_submit = await client.post(
        f"/api/v1/assessment/tests/attempts/{attempt_id}/submit",
        headers=auth_header(other_student),
    )
    assert hack_submit.status_code == 403


@pytest.mark.asyncio
async def test_delayed_result_release_redacts_marks_and_answers(
    client: AsyncClient, db_session: AsyncSession, assessment_fixture: dict
):
    student = assessment_fixture["student"]
    chapter = assessment_fixture["chapter"]

    # Test with results_released_at set in the FUTURE
    test = Test(
        chapter_id=chapter.id,
        title="Delayed Release Test",
        duration_minutes=15,
        total_marks=10,
        deadline=utc_now() + timedelta(days=1),
        is_published=True,
        results_released_at=utc_now() + timedelta(days=2),
        solutions_released_at=utc_now() + timedelta(days=3),
    )
    db_session.add(test)
    await db_session.flush()

    q = Question(
        test_id=test.id,
        question_text="Q1",
        options=[{"key": "A", "text": "Correct A"}],
        correct_option="A",
        marks=10,
    )
    db_session.add(q)
    await db_session.commit()

    # Student starts and answers
    start_res = await client.post(
        f"/api/v1/assessment/tests/{test.id}/attempts/start",
        headers=auth_header(student),
    )
    attempt_id = start_res.json()["attempt_id"]

    await client.post(
        f"/api/v1/assessment/tests/attempts/{attempt_id}/save-answer",
        json={"question_id": str(q.id), "selected_option": "A"},
        headers=auth_header(student),
    )

    # Submit attempt -> score and answers must be redacted because results are not released yet
    sub_res = await client.post(
        f"/api/v1/assessment/tests/attempts/{attempt_id}/submit",
        headers=auth_header(student),
    )
    assert sub_res.status_code == 200
    data = sub_res.json()
    assert data["results_released"] is False
    assert Decimal(str(data["score"])) == Decimal("0.00")
    assert Decimal(str(data["percentage"])) == Decimal("0.00")
    assert data["passed"] is False
    assert data["answers"] is None
    assert data["results_released_at"] is not None

    # Student views attempt history -> must also be redacted
    my_att_res = await client.get(
        f"/api/v1/assessment/tests/{test.id}/attempts/my",
        headers=auth_header(student),
    )
    assert my_att_res.status_code == 200
    my_data = my_att_res.json()[0]
    assert my_data["results_released"] is False
    assert Decimal(str(my_data["score"])) == Decimal("0.00")
    assert my_data["passed"] is False


@pytest.mark.asyncio
async def test_submission_queue_aggregate_counts_invariant_to_filters(
    client: AsyncClient, db_session: AsyncSession, assessment_fixture: dict
):
    teacher = assessment_fixture["teacher"]
    student = assessment_fixture["student"]
    lecture = assessment_fixture["lecture"]

    assignment = Assignment(
        lecture_id=lecture.id,
        title="Queue Filter Test Assignment",
        instructions="Testing count invariance",
        max_marks=50,
        deadline=utc_now() + timedelta(days=2),
        is_published=True,
    )
    db_session.add(assignment)
    await db_session.commit()

    # Student submits assignment
    await client.post(
        f"/api/v1/assessment/assignments/{assignment.id}/submissions",
        json={"student_content": "Queue count test submission"},
        headers=auth_header(student),
    )

    # Teacher gets queue without filter
    q_all = await client.get(
        f"/api/v1/assessment/assignments/{assignment.id}/submissions",
        headers=auth_header(teacher),
    )
    assert q_all.status_code == 200
    all_data = q_all.json()
    assert all_data["submitted_count"] >= 1
    assert all_data["pending_count"] >= 1
    assert all_data["missing_count"] == max(0, all_data["total_enrolled"] - all_data["submitted_count"])

    # Teacher gets queue filtered by status=evaluated (where 0 rows match)
    q_eval = await client.get(
        f"/api/v1/assessment/assignments/{assignment.id}/submissions?status=evaluated",
        headers=auth_header(teacher),
    )
    assert q_eval.status_code == 200
    eval_data = q_eval.json()
    assert len(eval_data["submissions"]) == 0
    # True aggregate header counts must NOT distort to 0 when status_filter is applied
    assert eval_data["submitted_count"] == all_data["submitted_count"]
    assert eval_data["pending_count"] == all_data["pending_count"]
    assert eval_data["missing_count"] == all_data["missing_count"]


@pytest.mark.asyncio
async def test_resubmission_allowed_when_teacher_requests_resubmission(
    client: AsyncClient, db_session: AsyncSession, assessment_fixture: dict
):
    teacher = assessment_fixture["teacher"]
    student = assessment_fixture["student"]
    lecture = assessment_fixture["lecture"]

    assignment = Assignment(
        lecture_id=lecture.id,
        title="Resubmission Workflow Test",
        instructions="Submit homework",
        max_marks=100,
        deadline=utc_now() + timedelta(days=2),
        is_published=True,
    )
    db_session.add(assignment)
    await db_session.commit()

    # Student submits
    sub_res = await client.post(
        f"/api/v1/assessment/assignments/{assignment.id}/submissions",
        json={"student_content": "Attempt 1 content"},
        headers=auth_header(student),
    )
    sub_id = sub_res.json()["id"]

    # Teacher grades it
    await client.post(
        f"/api/v1/assessment/submissions/{sub_id}/grade",
        json={"obtained_marks": "40.00", "teacher_feedback": "Needs revision", "is_released": True},
        headers=auth_header(teacher),
    )

    # Student tries to submit again -> blocked with 400 because it's evaluated
    resub_blocked = await client.post(
        f"/api/v1/assessment/assignments/{assignment.id}/submissions",
        json={"student_content": "Illegal attempt 2"},
        headers=auth_header(student),
    )
    assert resub_blocked.status_code == 400

    # Teacher requests resubmission
    req_res = await client.post(
        f"/api/v1/assessment/submissions/{sub_id}/request-resubmission",
        headers=auth_header(teacher),
    )
    assert req_res.status_code == 200

    # Student submits again -> now permitted, creating attempt #2
    resub_success = await client.post(
        f"/api/v1/assessment/assignments/{assignment.id}/submissions",
        json={"student_content": "Revised attempt 2 content"},
        headers=auth_header(student),
    )
    assert resub_success.status_code == 201
    assert resub_success.json()["attempt_number"] == 2
    assert resub_success.json()["is_latest"] is True


