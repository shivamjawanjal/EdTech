import asyncio
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure backend directory is in path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models import (
    User,
    StudentProfile,
    Batch,
    Course,
    CourseBatch,
    Enrollment,
    Subject,
    Chapter,
    Lecture,
    LectureNote,
    Assignment,
    Submission,
    SubmissionAttachment,
    Test,
    Question,
    TestAttempt,
    TestAnswer,
    DoubtThread,
    DoubtMessage,
    LiveSession,
    LiveAttendanceRecord,
    Announcement,
    Notification,
    StudentHealthSummary,
    StudentActivity,
    AuditEvent,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def seed_database(session: AsyncSession) -> None:
    now = utc_now()
    default_password_hash = hash_password("StudentPassword123!")
    teacher_password_hash = hash_password("TeacherPassword123!")

    # -------------------------------------------------------------
    # 1. Primary Teacher Account
    # -------------------------------------------------------------
    teacher_query = await session.execute(
        select(User).where(User.phone == "+919999900000")
    )
    teacher = teacher_query.scalar_one_or_none()
    if not teacher:
        teacher = User(
            phone="+919999900000",
            email="teacher@edtechweb.local",
            hashed_password=teacher_password_hash,
            full_name="Prof. Rajesh Sharma",
            role="teacher",
            is_active=True,
            must_change_password=False,
        )
        session.add(teacher)
        await session.flush()
        print("[OK] Created primary teacher: Prof. Rajesh Sharma")
    else:
        print("[INFO] Teacher already exists, skipping creation.")

    # -------------------------------------------------------------
    # 2. Academic Batches (3 Batches of 50 students each)
    # -------------------------------------------------------------
    batch_defs = [
        {"name": "Class 10 - STEM Foundation Morning 2026", "academic_year": "2026-2027"},
        {"name": "Class 10 - STEM Foundation Evening 2026", "academic_year": "2026-2027"},
        {"name": "Class 9 - Foundation Olympiad 2026", "academic_year": "2026-2027"},
    ]
    batches = {}
    for b_data in batch_defs:
        b_query = await session.execute(select(Batch).where(Batch.name == b_data["name"]))
        existing_b = b_query.scalar_one_or_none()
        if not existing_b:
            existing_b = Batch(
                name=b_data["name"],
                description=f"Cohort for {b_data['name']}",
                academic_year=b_data["academic_year"],
                is_active=True,
            )
            session.add(existing_b)
            await session.flush()
        batches[b_data["name"]] = existing_b
    print(f"[OK] Batches verified: {len(batches)} cohorts.")

    # -------------------------------------------------------------
    # 3. Courses & Multi-Batch Association
    # -------------------------------------------------------------
    course_query = await session.execute(
        select(Course).where(Course.slug == "class-10-stem-reasoning-2026")
    )
    course = course_query.scalar_one_or_none()
    if not course:
        course = Course(
            title="Class 10 STEM & Reasoning Comprehensive 2026",
            slug="class-10-stem-reasoning-2026",
            description="Complete conceptual mastery in Mathematics, Science and Logical Reasoning.",
            is_published=True,
        )
        session.add(course)
        await session.flush()

        # Link course to Batch 1 and Batch 2
        session.add(CourseBatch(course_id=course.id, batch_id=batches["Class 10 - STEM Foundation Morning 2026"].id))
        session.add(CourseBatch(course_id=course.id, batch_id=batches["Class 10 - STEM Foundation Evening 2026"].id))
        await session.flush()
        print("[OK] Created Course and linked to Morning and Evening Batches.")
    else:
        print("[INFO] Course already exists.")

    # -------------------------------------------------------------
    # 4. Curriculum: Subjects, Chapters, Lectures & Notes
    # -------------------------------------------------------------
    subjects_data = [
        {"name": "Mathematics", "code": "MATH", "order": 1},
        {"name": "Science", "code": "SCI", "order": 2},
        {"name": "Reasoning", "code": "REAS", "order": 3},
    ]
    created_subjects = {}
    for s_data in subjects_data:
        s_query = await session.execute(
            select(Subject).where(Subject.course_id == course.id, Subject.name == s_data["name"])
        )
        subject = s_query.scalar_one_or_none()
        if not subject:
            subject = Subject(
                course_id=course.id,
                name=s_data["name"],
                code=s_data["code"],
                order_index=s_data["order"],
            )
            session.add(subject)
            await session.flush()
        created_subjects[s_data["name"]] = subject

    math_subject = created_subjects["Mathematics"]

    # Chapters under Mathematics
    chapters_data = [
        {"title": "Chapter 1: Real Numbers", "order": 1},
        {"title": "Chapter 2: Polynomials", "order": 2},
        {"title": "Chapter 3: Quadratic Equations", "order": 3},
    ]
    created_chapters = {}
    for ch_data in chapters_data:
        ch_query = await session.execute(
            select(Chapter).where(Chapter.subject_id == math_subject.id, Chapter.title == ch_data["title"])
        )
        chapter = ch_query.scalar_one_or_none()
        if not chapter:
            chapter = Chapter(
                subject_id=math_subject.id,
                title=ch_data["title"],
                description=f"Foundations of {ch_data['title']}",
                order_index=ch_data["order"],
                is_published=True,
            )
            session.add(chapter)
            await session.flush()
        created_chapters[ch_data["title"]] = chapter

    ch3 = created_chapters["Chapter 3: Quadratic Equations"]

    # Lectures under Chapter 3
    lectures_data = [
        {"title": "Lecture 01: Concept of Quadratic Roots", "duration": 1800, "order": 1},
        {"title": "Lecture 02: Factorization & Completing Square", "duration": 2100, "order": 2},
        {"title": "Lecture 03: The Quadratic Formula & Discriminant", "duration": 2400, "order": 3},
    ]
    created_lectures = []
    for l_data in lectures_data:
        l_query = await session.execute(
            select(Lecture).where(Lecture.chapter_id == ch3.id, Lecture.title == l_data["title"])
        )
        lecture = l_query.scalar_one_or_none()
        if not lecture:
            lecture = Lecture(
                chapter_id=ch3.id,
                title=l_data["title"],
                description=f"Detailed lecture on {l_data['title']}",
                duration_seconds=l_data["duration"],
                video_s3_key=f"courses/{course.id}/lectures/{l_data['order']}/video.mp4",
                order_index=l_data["order"],
                is_published=True,
                published_at=now - timedelta(days=7 - l_data["order"]),
            )
            session.add(lecture)
            await session.flush()

            # Attach Lecture Notes PDF
            session.add(
                LectureNote(
                    lecture_id=lecture.id,
                    title=f"{l_data['title']} - Summary Sheet.pdf",
                    pdf_s3_key=f"courses/{course.id}/notes/{l_data['order']}_notes.pdf",
                    file_size_bytes=2450000,
                    allow_download=True,
                    order_index=1,
                )
            )
            await session.flush()
        created_lectures.append(lecture)

    target_lecture = created_lectures[0]

    # Daily Assignment attached to Lecture 01
    assign_query = await session.execute(
        select(Assignment).where(Assignment.lecture_id == target_lecture.id)
    )
    assignment = assign_query.scalar_one_or_none()
    if not assignment:
        assignment = Assignment(
            lecture_id=target_lecture.id,
            title="Daily Assignment 01: Quadratic Roots Practice",
            instructions="Solve problems 1 through 8 from worksheet. Upload clear photos of your notebook solutions.",
            question_sheet_s3_key=f"assignments/{target_lecture.id}/worksheet.pdf",
            max_marks=10,
            deadline=now - timedelta(days=1),
            allow_late_submission=True,
            late_deadline=now + timedelta(days=2),
        )
        session.add(assignment)
        await session.flush()
        print("[OK] Created Assignment attached to Lecture 01.")

    # Chapter Test under Chapter 3
    test_query = await session.execute(
        select(Test).where(Test.chapter_id == ch3.id)
    )
    test = test_query.scalar_one_or_none()
    if not test:
        test = Test(
            chapter_id=ch3.id,
            title="Chapter 3 Milestone Test: Quadratic Equations",
            description="20-minute timed objective assessment.",
            duration_minutes=20,
            total_marks=5,
            pass_percentage=40,
            deadline=now + timedelta(days=3),
            max_attempts=1,
            is_published=True,
        )
        session.add(test)
        await session.flush()

        # Add 5 questions
        q_texts = [
            ("Roots of equation x^2 - 5x + 6 = 0 are:", ["2, 3", "1, 6", "-2, -3", "2, -3"], "A"),
            ("Discriminant of 2x^2 - 4x + 3 = 0 is:", ["-8", "8", "-4", "16"], "A"),
            ("If roots of ax^2 + bx + c = 0 are equal, then:", ["b^2 = 4ac", "b^2 < 4ac", "b^2 > 4ac", "b = 0"], "A"),
            ("A quadratic equation has at most:", ["2 roots", "1 root", "3 roots", "Infinite roots"], "A"),
            ("Sum of roots of 3x^2 + 9x - 12 = 0 is:", ["-3", "3", "-4", "4"], "A"),
        ]
        for idx, (q_t, opts, c_opt) in enumerate(q_texts, start=1):
            session.add(
                Question(
                    test_id=test.id,
                    question_text=q_t,
                    options=[{"key": chr(65 + i), "text": opt} for i, opt in enumerate(opts)],
                    correct_option=c_opt,
                    marks=1,
                    negative_marks=Decimal("0.00"),
                    solution_explanation=f"Explanation for question {idx}.",
                    order_index=idx,
                )
            )
        await session.flush()
        print("[OK] Created Chapter Milestone Test with 5 MCQ questions.")

    # -------------------------------------------------------------
    # 5. 150 Synthetic Students across 3 Health Tiers
    # -------------------------------------------------------------
    # Tier 1: On Track (Students 1 to 100)
    # Tier 2: Needs Attention (Students 101 to 130)
    # Tier 3: At Risk (Students 131 to 150)
    print("[*] Checking / creating 150 synthetic student accounts...")
    student_records = []
    morning_batch = batches["Class 10 - STEM Foundation Morning 2026"]
    evening_batch = batches["Class 10 - STEM Foundation Evening 2026"]
    olympiad_batch = batches["Class 9 - Foundation Olympiad 2026"]

    for i in range(1, 151):
        phone_num = f"+9198{i:08d}"
        s_query = await session.execute(select(User).where(User.phone == phone_num))
        student = s_query.scalar_one_or_none()

        if not student:
            # Determine batch: 1-50 morning, 51-100 evening, 101-150 olympiad
            if i <= 50:
                target_batch = morning_batch
                grade = "Class 10"
            elif i <= 100:
                target_batch = evening_batch
                grade = "Class 10"
            else:
                target_batch = olympiad_batch
                grade = "Class 9"

            student = User(
                phone=phone_num,
                email=f"student{i:03d}@edtechweb.local",
                hashed_password=default_password_hash,
                full_name=f"Student {i:03d} {('Kumar' if i % 2 == 0 else 'Patel')}",
                role="student",
                is_active=True,
                must_change_password=False,
            )
            session.add(student)
            await session.flush()

            # Profile
            session.add(
                StudentProfile(
                    user_id=student.id,
                    roll_number=f"ROLL-2026-{i:03d}",
                    parent_name=f"Parent of Student {i:03d}",
                    parent_phone=f"+9197{i:08d}",
                    school_name="Kendriya Vidyalaya No. 1",
                    grade_level=grade,
                    target_exam="CBSE Board + Olympiad",
                )
            )

            # Enrolment
            session.add(
                Enrollment(
                    student_id=student.id,
                    batch_id=target_batch.id,
                    status="active",
                )
            )

            # Health classification, assignments, tests, and activity simulation
            if i <= 100:
                # ------------------- ON TRACK -------------------
                health_status = "ON_TRACK"
                sub_rate = Decimal("100.00")
                watch_rate = Decimal("95.00")
                test_avg = Decimal("85.00")
                days_inactive = 0
                c_missing = 0
                reason = "High assignment submission rate (100%); test score 85%."

                # Submitted homework on-time
                sub = Submission(
                    assignment_id=assignment.id,
                    student_id=student.id,
                    attempt_number=1,
                    is_latest=True,
                    status="evaluated",
                    submitted_at=now - timedelta(days=2),
                    is_evaluated=True,
                    obtained_marks=Decimal("9.00"),
                    teacher_feedback="Excellent work on quadratic roots calculation.",
                    evaluated_at=now - timedelta(days=1),
                    evaluated_by=teacher.id,
                )
                session.add(sub)
                await session.flush()

                session.add(
                    SubmissionAttachment(
                        submission_id=sub.id,
                        s3_key=f"submissions/{assignment.id}/{student.id}/page1.jpg",
                        file_name="homework_page1.jpg",
                        file_size_bytes=1200000,
                        mime_type="image/jpeg",
                        page_order=1,
                    )
                )

                # Recent activity
                session.add(
                    StudentActivity(
                        student_id=student.id,
                        activity_type="WATCH_LECTURE",
                        entity_id=target_lecture.id,
                        created_at=now - timedelta(hours=3),
                    )
                )

            elif i <= 130:
                # ----------------- NEEDS ATTENTION -----------------
                health_status = "NEEDS_ATTENTION"
                sub_rate = Decimal("70.00")
                watch_rate = Decimal("65.00")
                test_avg = Decimal("52.00")
                days_inactive = 3
                c_missing = 1
                reason = "Test average dropped to 52%; 1 assignment missed."

                if i == 105:
                    # Demonstrate resubmission attempt versioning for student 105
                    sub1 = Submission(
                        assignment_id=assignment.id,
                        student_id=student.id,
                        attempt_number=1,
                        is_latest=False,
                        status="resubmission_requested",
                        submitted_at=now - timedelta(days=3),
                        is_evaluated=False,
                        teacher_feedback="Page 2 was blurry. Please re-upload.",
                        evaluated_at=now - timedelta(days=2),
                        evaluated_by=teacher.id,
                    )
                    session.add(sub1)
                    await session.flush()

                    sub2 = Submission(
                        assignment_id=assignment.id,
                        student_id=student.id,
                        attempt_number=2,
                        is_latest=True,
                        status="submitted",
                        submitted_at=now - timedelta(hours=12),
                        is_evaluated=False,
                    )
                    session.add(sub2)
                    await session.flush()
                else:
                    # Submitted late or waiting for review
                    sub = Submission(
                        assignment_id=assignment.id,
                        student_id=student.id,
                        attempt_number=1,
                        is_latest=True,
                        status="submitted",
                        submitted_at=now - timedelta(hours=10),
                        is_evaluated=False,
                    )
                    session.add(sub)
                    await session.flush()

                session.add(
                    StudentActivity(
                        student_id=student.id,
                        activity_type="LOGIN",
                        created_at=now - timedelta(days=3),
                    )
                )

            else:
                # ------------------- AT RISK -------------------
                health_status = "AT_RISK"
                sub_rate = Decimal("20.00")
                watch_rate = Decimal("25.00")
                test_avg = Decimal("30.00")
                days_inactive = 6
                c_missing = 3
                reason = "Flagged At Risk: 3 consecutive missing assignments; Inactive for 6 days."

                # No submission for assignment (missing work scenario)
                session.add(
                    StudentActivity(
                        student_id=student.id,
                        activity_type="LOGIN",
                        created_at=now - timedelta(days=6),
                    )
                )

            # Student Health Summary Snapshot
            session.add(
                StudentHealthSummary(
                    student_id=student.id,
                    health_status=health_status,
                    assignment_submission_rate=sub_rate,
                    video_watch_rate=watch_rate,
                    test_score_average=test_avg,
                    consecutive_missing_assignments=c_missing,
                    days_inactive=days_inactive,
                    explainability_reason=reason,
                    last_calculated_at=now,
                )
            )

            # Notification with read and unread states
            session.add(
                Notification(
                    user_id=student.id,
                    title="New Assignment Posted",
                    body="Daily Assignment 01 is due tomorrow at 8:00 PM.",
                    notification_type="ASSIGNMENT_DUE",
                    is_read=(i <= 100),  # On-track read it; at-risk unread
                    read_at=(now - timedelta(days=1)) if i <= 100 else None,
                )
            )

        student_records.append(student)

    await session.flush()
    print("[OK] 150 synthetic students verified with On Track (100), Needs Attention (30), and At Risk (20).")

    # -------------------------------------------------------------
    # 6. Live Class & Attendance Evidence
    # -------------------------------------------------------------
    live_query = await session.execute(
        select(LiveSession).where(LiveSession.batch_id == morning_batch.id)
    )
    live_session = live_query.scalar_one_or_none()
    if not live_session:
        live_session = LiveSession(
            batch_id=morning_batch.id,
            subject_id=math_subject.id,
            title="Live Problem Solving: Quadratic Equations & Roots",
            scheduled_start_time=now + timedelta(days=1, hours=2),
            scheduled_end_time=now + timedelta(days=1, hours=3),
            meet_url="https://meet.google.com/abc-defg-hij",
            status="scheduled",
        )
        session.add(live_session)
        await session.flush()

        # Add attendance evidence for student 1
        s1 = student_records[0]
        session.add(
            LiveAttendanceRecord(
                session_id=live_session.id,
                student_id=s1.id,
                click_through_at=now - timedelta(hours=1),
                client_ip="127.0.0.1",
                user_agent="Mozilla/5.0 (Linux; Android 14; Mobile)",
                verified_participation=True,
                verified_by=teacher.id,
                verification_notes="Participated actively and answered question 3.",
            )
        )
        await session.flush()
        print("[OK] Created Scheduled Live Class and sample attendance record.")

    # -------------------------------------------------------------
    # 7. Doubt Threads & Inbound Messages
    # -------------------------------------------------------------
    doubt_query = await session.execute(
        select(DoubtThread).where(DoubtThread.student_id == student_records[0].id)
    )
    doubt = doubt_query.scalar_one_or_none()
    if not doubt:
        doubt = DoubtThread(
            student_id=student_records[0].id,
            lecture_id=target_lecture.id,
            lecture_timestamp_seconds=345,
            title="Clarification on sign of roots in discriminant",
            status="resolved",
            resolved_at=now - timedelta(hours=6),
        )
        session.add(doubt)
        await session.flush()

        session.add(
            DoubtMessage(
                thread_id=doubt.id,
                sender_id=student_records[0].id,
                message_text="Sir, at 05:45 why did we invert the negative sign inside the square root?",
            )
        )
        session.add(
            DoubtMessage(
                thread_id=doubt.id,
                sender_id=teacher.id,
                message_text="Because (-b)^2 is positive, but -4ac has another minus sign making it positive.",
            )
        )
        await session.flush()
        print("[OK] Created Doubt Thread with student-teacher Q&A.")

    # -------------------------------------------------------------
    # 8. Announcements & Security Audit Trail
    # -------------------------------------------------------------
    announcement_query = await session.execute(select(Announcement))
    if not announcement_query.scalar_one_or_none():
        session.add(
            Announcement(
                batch_id=None,  # All batches
                title="Sunday Milestone Test Schedule",
                message_body="All batches please note the Quadratic Equations test will open this Sunday at 10:00 AM.",
                priority="urgent",
                created_by=teacher.id,
            )
        )
        await session.flush()
        print("[OK] Created Broadcast Announcement.")

    audit_query = await session.execute(select(AuditEvent))
    if not audit_query.scalar_one_or_none():
        session.add(
            AuditEvent(
                actor_id=teacher.id,
                action="STUDENT_ENROLLED_BATCH",
                target_entity_type="enrollment",
                target_entity_id=student_records[0].id,
                previous_state=None,
                new_state={"batch": morning_batch.name, "role": "student"},
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            )
        )
        await session.flush()
        print("[OK] Created Security Audit Log event.")

    await session.commit()
    print("\n[SUCCESS] Synthetic development database seeding completed successfully!")


async def main():
    print("=" * 60)
    print("EdtechWeb Synthetic Development Database Seeder")
    print("=" * 60)
    async with async_session_factory() as session:
        await seed_database(session)


if __name__ == "__main__":
    asyncio.run(main())
