import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db, require_teacher, require_student
from app.core.config import get_settings
from app.models.base import utc_now
from app.models.identity import User
from app.models.curriculum import Lecture, Chapter, Subject
from app.models.enrolment import Course, CourseBatch, Enrollment
from app.models.assessment import (
    Assignment,
    Submission,
    SubmissionAttachment,
    Test,
    Question,
    TestAttempt,
    TestAnswer,
)
from app.schemas.assessment import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    AssignmentSubmissionQueueResponse,
    SubmissionCreateRequest,
    SubmissionGradeRequest,
    SubmissionResponse,
    SubmissionAttachmentResponse,
    TestCreate,
    TestUpdate,
    TestResponse,
    TestDetailResponse,
    QuestionCreate,
    QuestionResponse,
    AttemptStartResponse,
    SaveAnswerRequest,
    AttemptResultResponse,
    AnswerDetailItem,
)
from app.schemas.common import MessageResponse

settings = get_settings()
router = APIRouter(prefix="/assessment", tags=["assessment"])


# -----------------------------------------------------------------------------
# Internal Authorization & Hierarchy Helpers
# -----------------------------------------------------------------------------


async def get_lecture_course(
    lecture_id: uuid.UUID, db: AsyncSession
) -> tuple[Lecture, Course]:
    stmt = (
        select(Lecture)
        .where(Lecture.id == lecture_id)
        .options(
            selectinload(Lecture.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course)
        )
    )
    res = await db.execute(stmt)
    lecture = res.scalars().first()
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lecture with ID '{lecture_id}' not found",
        )
    return lecture, lecture.chapter.subject.course


async def get_chapter_course(
    chapter_id: uuid.UUID, db: AsyncSession
) -> tuple[Chapter, Course]:
    stmt = (
        select(Chapter)
        .where(Chapter.id == chapter_id)
        .options(
            selectinload(Chapter.subject)
            .selectinload(Subject.course)
        )
    )
    res = await db.execute(stmt)
    chapter = res.scalars().first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with ID '{chapter_id}' not found",
        )
    return chapter, chapter.subject.course


def verify_teacher_ownership(teacher: User, course: Course) -> None:
    if course.instructor_id is not None and course.instructor_id != teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to manage assessments for another teacher's course",
        )


async def is_student_enrolled_in_course(
    student_id: uuid.UUID, course_id: uuid.UUID, db: AsyncSession
) -> bool:
    stmt = (
        select(Enrollment)
        .join(CourseBatch, CourseBatch.batch_id == Enrollment.batch_id)
        .where(
            Enrollment.student_id == student_id,
            Enrollment.status == "active",
            CourseBatch.course_id == course_id,
        )
    )
    res = await db.execute(stmt)
    return res.scalars().first() is not None


# -----------------------------------------------------------------------------
# Assignment Endpoints
# -----------------------------------------------------------------------------


@router.post(
    "/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and optionally publish a new daily assignment (Teacher)",
)
async def create_assignment(
    payload: AssignmentCreate,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    lecture, course = await get_lecture_course(payload.lecture_id, db)
    verify_teacher_ownership(current_user, course)

    if payload.allow_late_submission and payload.late_deadline:
        if payload.late_deadline < payload.deadline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Late submission deadline cannot be earlier than the standard deadline",
            )

    assignment = Assignment(
        lecture_id=payload.lecture_id,
        title=payload.title,
        instructions=payload.instructions,
        max_marks=payload.max_marks,
        deadline=payload.deadline,
        allow_late_submission=payload.allow_late_submission,
        late_deadline=payload.late_deadline,
        is_published=payload.is_published,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    return AssignmentResponse(
        id=assignment.id,
        lecture_id=assignment.lecture_id,
        title=assignment.title,
        instructions=assignment.instructions,
        max_marks=assignment.max_marks,
        deadline=assignment.deadline,
        allow_late_submission=assignment.allow_late_submission,
        late_deadline=assignment.late_deadline,
        is_published=assignment.is_published,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        course_id=course.id,
        course_title=course.title,
        lecture_title=lecture.title,
    )


@router.get(
    "/assignments",
    response_model=List[AssignmentResponse],
    summary="List assignments for teacher or enrolled student",
)
async def list_assignments(
    lecture_id: Optional[uuid.UUID] = Query(default=None),
    course_id: Optional[uuid.UUID] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == "teacher":
        query = (
            select(Assignment)
            .join(Lecture, Lecture.id == Assignment.lecture_id)
            .join(Chapter, Chapter.id == Lecture.chapter_id)
            .join(Subject, Subject.id == Chapter.subject_id)
            .join(Course, Course.id == Subject.course_id)
            .options(
                selectinload(Assignment.lecture)
                .selectinload(Lecture.chapter)
                .selectinload(Chapter.subject)
                .selectinload(Subject.course)
            )
            .order_by(Assignment.created_at.desc())
        )
        if lecture_id:
            query = query.where(Assignment.lecture_id == lecture_id)
        if course_id:
            query = query.where(Course.id == course_id)

        res = await db.execute(query)
        assignments = res.scalars().all()

        results = []
        for a in assignments:
            c = a.lecture.chapter.subject.course
            # Get submission counts
            sub_count_res = await db.execute(
                select(
                    func.count(Submission.id),
                    func.count(Submission.id).filter(Submission.is_evaluated == True),
                    func.count(Submission.id).filter(
                        Submission.is_latest == True, Submission.is_evaluated == False
                    ),
                ).where(Submission.assignment_id == a.id, Submission.is_latest == True)
            )
            total_subs, eval_subs, pending_subs = sub_count_res.one()

            results.append(
                AssignmentResponse(
                    id=a.id,
                    lecture_id=a.lecture_id,
                    title=a.title,
                    instructions=a.instructions,
                    max_marks=a.max_marks,
                    deadline=a.deadline,
                    allow_late_submission=a.allow_late_submission,
                    late_deadline=a.late_deadline,
                    is_published=a.is_published,
                    created_at=a.created_at,
                    updated_at=a.updated_at,
                    course_id=c.id,
                    course_title=c.title,
                    lecture_title=a.lecture.title,
                    submission_count=total_subs or 0,
                    evaluated_count=eval_subs or 0,
                    pending_count=pending_subs or 0,
                )
            )
        return results

    else:
        # Student: only active enrolled courses and published assignments
        enrolled_courses_stmt = (
            select(CourseBatch.course_id)
            .join(Enrollment, Enrollment.batch_id == CourseBatch.batch_id)
            .where(
                Enrollment.student_id == current_user.id,
                Enrollment.status == "active",
            )
        )
        enrolled_res = await db.execute(enrolled_courses_stmt)
        enrolled_course_ids = [r[0] for r in enrolled_res.all()]

        if not enrolled_course_ids:
            return []

        query = (
            select(Assignment)
            .join(Lecture, Lecture.id == Assignment.lecture_id)
            .join(Chapter, Chapter.id == Lecture.chapter_id)
            .join(Subject, Subject.id == Chapter.subject_id)
            .join(Course, Course.id == Subject.course_id)
            .where(
                Assignment.is_published == True,
                Course.id.in_(enrolled_course_ids),
            )
            .options(
                selectinload(Assignment.lecture)
                .selectinload(Lecture.chapter)
                .selectinload(Chapter.subject)
                .selectinload(Subject.course)
            )
            .order_by(Assignment.deadline.asc())
        )
        if lecture_id:
            query = query.where(Assignment.lecture_id == lecture_id)
        if course_id:
            query = query.where(Course.id == course_id)

        res = await db.execute(query)
        assignments = res.scalars().all()

        results = []
        for a in assignments:
            c = a.lecture.chapter.subject.course
            # Fetch student's latest submission for this assignment
            sub_stmt = (
                select(Submission)
                .where(
                    Submission.assignment_id == a.id,
                    Submission.student_id == current_user.id,
                    Submission.is_latest == True,
                )
                .options(selectinload(Submission.attachments))
            )
            sub_res = await db.execute(sub_stmt)
            sub = sub_res.scalars().first()

            sub_resp = None
            if sub:
                # Redact marks and feedback if not released
                marks = sub.obtained_marks if sub.is_released else None
                feedback = sub.teacher_feedback if sub.is_released else None

                sub_resp = SubmissionResponse(
                    id=sub.id,
                    assignment_id=sub.assignment_id,
                    student_id=sub.student_id,
                    attempt_number=sub.attempt_number,
                    is_latest=sub.is_latest,
                    status=sub.status,
                    student_content=sub.student_content,
                    submitted_at=sub.submitted_at,
                    is_evaluated=sub.is_evaluated,
                    obtained_marks=marks,
                    teacher_feedback=feedback,
                    evaluated_at=sub.evaluated_at if sub.is_released else None,
                    is_released=sub.is_released,
                    released_at=sub.released_at,
                    attachments=[
                        SubmissionAttachmentResponse(
                            id=att.id,
                            s3_key=att.s3_key,
                            file_name=att.file_name,
                            file_size_bytes=att.file_size_bytes,
                            mime_type=att.mime_type,
                            page_order=att.page_order,
                            created_at=att.created_at,
                        )
                        for att in sub.attachments
                    ],
                )

            results.append(
                AssignmentResponse(
                    id=a.id,
                    lecture_id=a.lecture_id,
                    title=a.title,
                    instructions=a.instructions,
                    max_marks=a.max_marks,
                    deadline=a.deadline,
                    allow_late_submission=a.allow_late_submission,
                    late_deadline=a.late_deadline,
                    is_published=a.is_published,
                    created_at=a.created_at,
                    updated_at=a.updated_at,
                    course_id=c.id,
                    course_title=c.title,
                    lecture_title=a.lecture.title,
                    my_submission=sub_resp,
                )
            )
        return results


@router.get(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse,
    summary="Get assignment details",
)
async def get_assignment(
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Assignment)
        .where(Assignment.id == assignment_id)
        .options(
            selectinload(Assignment.lecture)
            .selectinload(Lecture.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course)
        )
    )
    res = await db.execute(stmt)
    assignment = res.scalars().first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    course = assignment.lecture.chapter.subject.course

    if current_user.role == "student":
        if not assignment.is_published:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or not published",
            )
        enrolled = await is_student_enrolled_in_course(current_user.id, course.id, db)
        if not enrolled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not enrolled in the course for this assignment",
            )

        # Get latest submission
        sub_stmt = (
            select(Submission)
            .where(
                Submission.assignment_id == assignment.id,
                Submission.student_id == current_user.id,
                Submission.is_latest == True,
            )
            .options(selectinload(Submission.attachments))
        )
        sub_res = await db.execute(sub_stmt)
        sub = sub_res.scalars().first()
        sub_resp = None
        if sub:
            marks = sub.obtained_marks if sub.is_released else None
            feedback = sub.teacher_feedback if sub.is_released else None
            sub_resp = SubmissionResponse(
                id=sub.id,
                assignment_id=sub.assignment_id,
                student_id=sub.student_id,
                attempt_number=sub.attempt_number,
                is_latest=sub.is_latest,
                status=sub.status,
                student_content=sub.student_content,
                submitted_at=sub.submitted_at,
                is_evaluated=sub.is_evaluated,
                obtained_marks=marks,
                teacher_feedback=feedback,
                evaluated_at=sub.evaluated_at if sub.is_released else None,
                is_released=sub.is_released,
                released_at=sub.released_at,
                attachments=[
                    SubmissionAttachmentResponse(
                        id=att.id,
                        s3_key=att.s3_key,
                        file_name=att.file_name,
                        file_size_bytes=att.file_size_bytes,
                        mime_type=att.mime_type,
                        page_order=att.page_order,
                        created_at=att.created_at,
                    )
                    for att in sub.attachments
                ],
            )

        return AssignmentResponse(
            id=assignment.id,
            lecture_id=assignment.lecture_id,
            title=assignment.title,
            instructions=assignment.instructions,
            max_marks=assignment.max_marks,
            deadline=assignment.deadline,
            allow_late_submission=assignment.allow_late_submission,
            late_deadline=assignment.late_deadline,
            is_published=assignment.is_published,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
            course_id=course.id,
            course_title=course.title,
            lecture_title=assignment.lecture.title,
            my_submission=sub_resp,
        )

    else:
        # Teacher: include stats
        sub_count_res = await db.execute(
            select(
                func.count(Submission.id),
                func.count(Submission.id).filter(Submission.is_evaluated == True),
                func.count(Submission.id).filter(
                    Submission.is_latest == True, Submission.is_evaluated == False
                ),
            ).where(Submission.assignment_id == assignment.id, Submission.is_latest == True)
        )
        total_subs, eval_subs, pending_subs = sub_count_res.one()

        return AssignmentResponse(
            id=assignment.id,
            lecture_id=assignment.lecture_id,
            title=assignment.title,
            instructions=assignment.instructions,
            max_marks=assignment.max_marks,
            deadline=assignment.deadline,
            allow_late_submission=assignment.allow_late_submission,
            late_deadline=assignment.late_deadline,
            is_published=assignment.is_published,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
            course_id=course.id,
            course_title=course.title,
            lecture_title=assignment.lecture.title,
            submission_count=total_subs or 0,
            evaluated_count=eval_subs or 0,
            pending_count=pending_subs or 0,
        )


@router.patch(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse,
    summary="Update assignment settings or publish status (Teacher)",
)
async def update_assignment(
    assignment_id: uuid.UUID,
    payload: AssignmentUpdate,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Assignment)
        .where(Assignment.id == assignment_id)
        .options(
            selectinload(Assignment.lecture)
            .selectinload(Lecture.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course)
        )
    )
    res = await db.execute(stmt)
    assignment = res.scalars().first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    course = assignment.lecture.chapter.subject.course
    verify_teacher_ownership(current_user, course)

    if payload.title is not None:
        assignment.title = payload.title
    if payload.instructions is not None:
        assignment.instructions = payload.instructions
    if payload.max_marks is not None:
        assignment.max_marks = payload.max_marks
    if payload.deadline is not None:
        assignment.deadline = payload.deadline
    if payload.allow_late_submission is not None:
        assignment.allow_late_submission = payload.allow_late_submission
    if payload.late_deadline is not None:
        assignment.late_deadline = payload.late_deadline
    if payload.is_published is not None:
        assignment.is_published = payload.is_published

    if assignment.allow_late_submission and assignment.late_deadline:
        if assignment.late_deadline < assignment.deadline:
            raise HTTPException(
                status_code=400,
                detail="Late submission deadline cannot be earlier than standard deadline",
            )

    await db.commit()
    await db.refresh(assignment)

    return AssignmentResponse(
        id=assignment.id,
        lecture_id=assignment.lecture_id,
        title=assignment.title,
        instructions=assignment.instructions,
        max_marks=assignment.max_marks,
        deadline=assignment.deadline,
        allow_late_submission=assignment.allow_late_submission,
        late_deadline=assignment.late_deadline,
        is_published=assignment.is_published,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        course_id=course.id,
        course_title=course.title,
        lecture_title=assignment.lecture.title,
    )


# -----------------------------------------------------------------------------
# Student Submissions & Teacher Grading
# -----------------------------------------------------------------------------


@router.post(
    "/assignments/{assignment_id}/submissions",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit or resubmit an assignment (Student)",
)
async def submit_assignment(
    assignment_id: uuid.UUID,
    payload: SubmissionCreateRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Assignment)
        .where(Assignment.id == assignment_id)
        .options(
            selectinload(Assignment.lecture)
            .selectinload(Lecture.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course)
        )
    )
    res = await db.execute(stmt)
    assignment = res.scalars().first()
    if not assignment or not assignment.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or not published",
        )

    course = assignment.lecture.chapter.subject.course
    enrolled = await is_student_enrolled_in_course(current_user.id, course.id, db)
    if not enrolled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not actively enrolled in the course for this assignment",
        )

    # Server-Authoritative Deadline Check
    now = utc_now()
    if now <= assignment.deadline:
        sub_status = "submitted"
    else:
        if not assignment.allow_late_submission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment deadline has passed. Late submissions are not permitted.",
            )
        if assignment.late_deadline and now > assignment.late_deadline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment is closed. The late submission deadline has passed.",
            )
        sub_status = "late"

    # Advisory lock to serialize competing submission requests even when 0 rows exist yet
    await db.execute(
        select(
            func.pg_advisory_xact_lock(
                func.hashtext(f"assignment_sub:{assignment.id}:{current_user.id}")
            )
        )
    )

    # Check for existing submissions
    existing_stmt = (
        select(Submission)
        .where(
            Submission.assignment_id == assignment.id,
            Submission.student_id == current_user.id,
            Submission.is_latest == True,
        )
        .with_for_update()
    )
    res = await db.execute(existing_stmt)
    latest_sub = res.scalars().first()

    attempt_number = 1
    if latest_sub:
        if latest_sub.status == "evaluated":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify or resubmit an already evaluated assignment unless resubmission is requested by teacher",
            )
        attempt_number = latest_sub.attempt_number + 1
        latest_sub.is_latest = False

    new_submission = Submission(
        assignment_id=assignment.id,
        student_id=current_user.id,
        attempt_number=attempt_number,
        is_latest=True,
        status=sub_status,
        student_content=payload.student_content,
        submitted_at=now,
        is_evaluated=False,
        is_released=False,
    )
    db.add(new_submission)
    await db.commit()
    await db.refresh(new_submission)

    return SubmissionResponse(
        id=new_submission.id,
        assignment_id=new_submission.assignment_id,
        student_id=new_submission.student_id,
        attempt_number=new_submission.attempt_number,
        is_latest=new_submission.is_latest,
        status=new_submission.status,
        student_content=new_submission.student_content,
        submitted_at=new_submission.submitted_at,
        is_evaluated=False,
        is_released=False,
        attachments=[],
    )


@router.get(
    "/assignments/{assignment_id}/submissions",
    response_model=AssignmentSubmissionQueueResponse,
    summary="Get assignment submission queue with filters (Teacher)",
)
async def get_submission_queue(
    assignment_id: uuid.UUID,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Assignment)
        .where(Assignment.id == assignment_id)
        .options(
            selectinload(Assignment.lecture)
            .selectinload(Lecture.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course)
        )
    )
    res = await db.execute(stmt)
    assignment = res.scalars().first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    course = assignment.lecture.chapter.subject.course
    verify_teacher_ownership(current_user, course)

    # Total enrolled students in the course
    enrolled_count_stmt = (
        select(func.count(func.distinct(Enrollment.student_id)))
        .join(CourseBatch, CourseBatch.batch_id == Enrollment.batch_id)
        .where(
            CourseBatch.course_id == course.id,
            Enrollment.status == "active",
        )
    )
    enrolled_res = await db.execute(enrolled_count_stmt)
    total_enrolled = enrolled_res.scalar_one() or 0

    # Submissions query
    subs_stmt = (
        select(Submission)
        .where(
            Submission.assignment_id == assignment.id,
            Submission.is_latest == True,
        )
        .options(
            selectinload(Submission.attachments),
            selectinload(Submission.student).selectinload(User.profile),
        )
        .order_by(Submission.submitted_at.desc())
    )
    if status_filter:
        if status_filter == "pending":
            subs_stmt = subs_stmt.where(Submission.is_evaluated == False)
        elif status_filter == "evaluated":
            subs_stmt = subs_stmt.where(Submission.is_evaluated == True)
        elif status_filter in ("submitted", "late", "resubmission_requested"):
            subs_stmt = subs_stmt.where(Submission.status == status_filter)

    subs_res = await db.execute(subs_stmt)
    submissions = subs_res.scalars().all()

    # Calculate true aggregate counts across all latest submissions regardless of status_filter
    agg_stmt = select(
        func.count(Submission.id),
        func.count(Submission.id).filter(Submission.is_evaluated == True),
        func.count(Submission.id).filter(Submission.is_evaluated == False),
        func.count(Submission.id).filter(Submission.status == "late"),
    ).where(
        Submission.assignment_id == assignment.id,
        Submission.is_latest == True,
    )
    agg_res = await db.execute(agg_stmt)
    total_latest_subs, agg_evaluated, agg_pending, agg_late = agg_res.one()

    submitted_count = total_latest_subs or 0
    evaluated_count = agg_evaluated or 0
    pending_count = agg_pending or 0
    late_count = agg_late or 0
    missing_count = max(0, total_enrolled - submitted_count)

    sub_responses = []
    for s in submissions:
        student_name = (
            s.student.full_name
            if s.student and s.student.full_name
            else (s.student.email if s.student else "Student")
        )
        sub_responses.append(
            SubmissionResponse(
                id=s.id,
                assignment_id=s.assignment_id,
                student_id=s.student_id,
                attempt_number=s.attempt_number,
                is_latest=s.is_latest,
                status=s.status,
                student_content=s.student_content,
                submitted_at=s.submitted_at,
                is_evaluated=s.is_evaluated,
                obtained_marks=s.obtained_marks,
                teacher_feedback=s.teacher_feedback,
                evaluated_at=s.evaluated_at,
                is_released=s.is_released,
                released_at=s.released_at,
                student_name=student_name,
                student_email=s.student.email if s.student else None,
                attachments=[
                    SubmissionAttachmentResponse(
                        id=att.id,
                        s3_key=att.s3_key,
                        file_name=att.file_name,
                        file_size_bytes=att.file_size_bytes,
                        mime_type=att.mime_type,
                        page_order=att.page_order,
                        created_at=att.created_at,
                    )
                    for att in s.attachments
                ],
            )
        )

    assignment_resp = AssignmentResponse(
        id=assignment.id,
        lecture_id=assignment.lecture_id,
        title=assignment.title,
        instructions=assignment.instructions,
        max_marks=assignment.max_marks,
        deadline=assignment.deadline,
        allow_late_submission=assignment.allow_late_submission,
        late_deadline=assignment.late_deadline,
        is_published=assignment.is_published,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        course_id=course.id,
        course_title=course.title,
        lecture_title=assignment.lecture.title,
        submission_count=submitted_count,
        evaluated_count=evaluated_count,
        pending_count=pending_count,
        missing_count=missing_count,
    )

    return AssignmentSubmissionQueueResponse(
        assignment=assignment_resp,
        total_enrolled=total_enrolled,
        submitted_count=submitted_count,
        evaluated_count=evaluated_count,
        pending_count=pending_count,
        late_count=late_count,
        missing_count=missing_count,
        submissions=sub_responses,
    )


@router.get(
    "/assignments/{assignment_id}/submissions/my",
    response_model=List[SubmissionResponse],
    summary="Get student's own submission history for an assignment",
)
async def get_my_submissions(
    assignment_id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Submission)
        .where(
            Submission.assignment_id == assignment_id,
            Submission.student_id == current_user.id,
        )
        .options(selectinload(Submission.attachments))
        .order_by(Submission.attempt_number.desc())
    )
    res = await db.execute(stmt)
    submissions = res.scalars().all()

    results = []
    for s in submissions:
        marks = s.obtained_marks if s.is_released else None
        feedback = s.teacher_feedback if s.is_released else None

        results.append(
            SubmissionResponse(
                id=s.id,
                assignment_id=s.assignment_id,
                student_id=s.student_id,
                attempt_number=s.attempt_number,
                is_latest=s.is_latest,
                status=s.status,
                student_content=s.student_content,
                submitted_at=s.submitted_at,
                is_evaluated=s.is_evaluated,
                obtained_marks=marks,
                teacher_feedback=feedback,
                evaluated_at=s.evaluated_at if s.is_released else None,
                is_released=s.is_released,
                released_at=s.released_at,
                attachments=[
                    SubmissionAttachmentResponse(
                        id=att.id,
                        s3_key=att.s3_key,
                        file_name=att.file_name,
                        file_size_bytes=att.file_size_bytes,
                        mime_type=att.mime_type,
                        page_order=att.page_order,
                        created_at=att.created_at,
                    )
                    for att in s.attachments
                ],
            )
        )
    return results


@router.post(
    "/submissions/{submission_id}/grade",
    response_model=SubmissionResponse,
    summary="Grade an assignment submission (Teacher)",
)
async def grade_submission(
    submission_id: uuid.UUID,
    payload: SubmissionGradeRequest,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Submission)
        .where(Submission.id == submission_id)
        .options(
            selectinload(Submission.assignment)
            .selectinload(Assignment.lecture)
            .selectinload(Lecture.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course),
            selectinload(Submission.attachments),
            selectinload(Submission.student).selectinload(User.profile),
        )
        .with_for_update()
    )
    res = await db.execute(stmt)
    submission = res.scalars().first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    course = submission.assignment.lecture.chapter.subject.course
    verify_teacher_ownership(current_user, course)

    if payload.obtained_marks > Decimal(submission.assignment.max_marks):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Obtained marks ({payload.obtained_marks}) cannot exceed assignment maximum marks ({submission.assignment.max_marks})",
        )

    now = utc_now()
    submission.obtained_marks = payload.obtained_marks
    submission.teacher_feedback = payload.teacher_feedback
    submission.is_evaluated = True
    submission.status = "evaluated"
    submission.evaluated_at = now
    submission.evaluated_by = current_user.id
    submission.is_released = payload.is_released
    if payload.is_released:
        submission.released_at = now

    await db.commit()
    await db.refresh(submission)

    student_name = (
        submission.student.full_name
        if submission.student and submission.student.full_name
        else (submission.student.email if submission.student else "Student")
    )

    return SubmissionResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        attempt_number=submission.attempt_number,
        is_latest=submission.is_latest,
        status=submission.status,
        student_content=submission.student_content,
        submitted_at=submission.submitted_at,
        is_evaluated=submission.is_evaluated,
        obtained_marks=submission.obtained_marks,
        teacher_feedback=submission.teacher_feedback,
        evaluated_at=submission.evaluated_at,
        is_released=submission.is_released,
        released_at=submission.released_at,
        student_name=student_name,
        attachments=[
            SubmissionAttachmentResponse(
                id=att.id,
                s3_key=att.s3_key,
                file_name=att.file_name,
                file_size_bytes=att.file_size_bytes,
                mime_type=att.mime_type,
                page_order=att.page_order,
                created_at=att.created_at,
            )
            for att in submission.attachments
        ],
    )


@router.post(
    "/assignments/{assignment_id}/release-grades",
    response_model=MessageResponse,
    summary="Batch release evaluated assignment grades to students (Teacher)",
)
async def release_assignment_grades(
    assignment_id: uuid.UUID,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Assignment)
        .where(Assignment.id == assignment_id)
        .options(
            selectinload(Assignment.lecture)
            .selectinload(Lecture.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course)
        )
    )
    res = await db.execute(stmt)
    assignment = res.scalars().first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    course = assignment.lecture.chapter.subject.course
    verify_teacher_ownership(current_user, course)

    now = utc_now()
    upd_stmt = (
        update(Submission)
        .where(
            Submission.assignment_id == assignment.id,
            Submission.is_evaluated == True,
            Submission.is_released == False,
        )
        .values(is_released=True, released_at=now)
    )
    result = await db.execute(upd_stmt)
    await db.commit()

    return MessageResponse(
        message=f"Grades successfully released for {result.rowcount} evaluated submission(s)",
        detail=str(result.rowcount),
    )


@router.post(
    "/submissions/{submission_id}/request-resubmission",
    response_model=SubmissionResponse,
    summary="Request student to resubmit assignment (Teacher)",
)
async def request_resubmission(
    submission_id: uuid.UUID,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Submission)
        .where(Submission.id == submission_id)
        .options(
            selectinload(Submission.assignment)
            .selectinload(Assignment.lecture)
            .selectinload(Lecture.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course),
            selectinload(Submission.attachments),
            selectinload(Submission.student),
        )
        .with_for_update()
    )
    res = await db.execute(stmt)
    submission = res.scalars().first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    course = submission.assignment.lecture.chapter.subject.course
    verify_teacher_ownership(current_user, course)

    submission.status = "resubmission_requested"
    await db.commit()
    await db.refresh(submission)

    student_name = (
        submission.student.full_name
        if submission.student and submission.student.full_name
        else (submission.student.email if submission.student else "Student")
    )

    return SubmissionResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        attempt_number=submission.attempt_number,
        is_latest=submission.is_latest,
        status=submission.status,
        student_content=submission.student_content,
        submitted_at=submission.submitted_at,
        is_evaluated=submission.is_evaluated,
        obtained_marks=submission.obtained_marks,
        teacher_feedback=submission.teacher_feedback,
        evaluated_at=submission.evaluated_at,
        is_released=submission.is_released,
        released_at=submission.released_at,
        student_name=student_name,
        attachments=[
            SubmissionAttachmentResponse(
                id=att.id,
                s3_key=att.s3_key,
                file_name=att.file_name,
                file_size_bytes=att.file_size_bytes,
                mime_type=att.mime_type,
                page_order=att.page_order,
                created_at=att.created_at,
            )
            for att in submission.attachments
        ],
    )


# -----------------------------------------------------------------------------
# Timed MCQ Assessments & Questions
# -----------------------------------------------------------------------------


@router.post(
    "/tests",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new timed MCQ test (Teacher)",
)
async def create_test(
    payload: TestCreate,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    chapter, course = await get_chapter_course(payload.chapter_id, db)
    verify_teacher_ownership(current_user, course)

    test = Test(
        chapter_id=payload.chapter_id,
        title=payload.title,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        total_marks=0,  # Computed from questions
        pass_percentage=payload.pass_percentage,
        deadline=payload.deadline,
        max_attempts=payload.max_attempts,
        is_published=payload.is_published,
        solutions_released_at=payload.solutions_released_at,
        results_released_at=payload.results_released_at,
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    return TestResponse(
        id=test.id,
        chapter_id=test.chapter_id,
        title=test.title,
        description=test.description,
        duration_minutes=test.duration_minutes,
        total_marks=test.total_marks,
        pass_percentage=test.pass_percentage,
        deadline=test.deadline,
        max_attempts=test.max_attempts,
        is_published=test.is_published,
        solutions_released_at=test.solutions_released_at,
        results_released_at=test.results_released_at,
        created_at=test.created_at,
        updated_at=test.updated_at,
        chapter_title=chapter.title,
        course_id=course.id,
        course_title=course.title,
        question_count=0,
    )


@router.get(
    "/tests",
    response_model=List[TestResponse],
    summary="List tests for teacher or enrolled student",
)
async def list_tests(
    chapter_id: Optional[uuid.UUID] = Query(default=None),
    course_id: Optional[uuid.UUID] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == "teacher":
        query = (
            select(Test)
            .join(Chapter, Chapter.id == Test.chapter_id)
            .join(Subject, Subject.id == Chapter.subject_id)
            .join(Course, Course.id == Subject.course_id)
            .options(
                selectinload(Test.chapter)
                .selectinload(Chapter.subject)
                .selectinload(Subject.course),
                selectinload(Test.questions),
            )
            .order_by(Test.created_at.desc())
        )
        if chapter_id:
            query = query.where(Test.chapter_id == chapter_id)
        if course_id:
            query = query.where(Course.id == course_id)

        res = await db.execute(query)
        tests = res.scalars().all()

        results = []
        for t in tests:
            c = t.chapter.subject.course
            results.append(
                TestResponse(
                    id=t.id,
                    chapter_id=t.chapter_id,
                    title=t.title,
                    description=t.description,
                    duration_minutes=t.duration_minutes,
                    total_marks=t.total_marks,
                    pass_percentage=t.pass_percentage,
                    deadline=t.deadline,
                    max_attempts=t.max_attempts,
                    is_published=t.is_published,
                    solutions_released_at=t.solutions_released_at,
                    results_released_at=t.results_released_at,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                    chapter_title=t.chapter.title,
                    course_id=c.id,
                    course_title=c.title,
                    question_count=len(t.questions),
                )
            )
        return results

    else:
        # Student: only published tests in active enrolled courses
        enrolled_courses_stmt = (
            select(CourseBatch.course_id)
            .join(Enrollment, Enrollment.batch_id == CourseBatch.batch_id)
            .where(
                Enrollment.student_id == current_user.id,
                Enrollment.status == "active",
            )
        )
        enrolled_res = await db.execute(enrolled_courses_stmt)
        enrolled_course_ids = [r[0] for r in enrolled_res.all()]

        if not enrolled_course_ids:
            return []

        query = (
            select(Test)
            .join(Chapter, Chapter.id == Test.chapter_id)
            .join(Subject, Subject.id == Chapter.subject_id)
            .join(Course, Course.id == Subject.course_id)
            .where(
                Test.is_published == True,
                Course.id.in_(enrolled_course_ids),
            )
            .options(
                selectinload(Test.chapter)
                .selectinload(Chapter.subject)
                .selectinload(Subject.course),
                selectinload(Test.questions),
            )
            .order_by(Test.deadline.asc())
        )
        if chapter_id:
            query = query.where(Test.chapter_id == chapter_id)
        if course_id:
            query = query.where(Course.id == course_id)

        res = await db.execute(query)
        tests = res.scalars().all()

        results = []
        for t in tests:
            c = t.chapter.subject.course

            # Check student's attempts
            att_stmt = (
                select(
                    func.count(TestAttempt.id),
                    func.max(TestAttempt.score),
                ).where(
                    TestAttempt.test_id == t.id,
                    TestAttempt.student_id == current_user.id,
                    TestAttempt.is_completed == True,
                )
            )
            att_res = await db.execute(att_stmt)
            attempt_count, best_score = att_res.one()

            # Check ongoing active attempt
            active_stmt = (
                select(TestAttempt.id)
                .where(
                    TestAttempt.test_id == t.id,
                    TestAttempt.student_id == current_user.id,
                    TestAttempt.is_completed == False,
                )
            )
            act_res = await db.execute(active_stmt)
            active_id = act_res.scalar_one_or_none()

            results.append(
                TestResponse(
                    id=t.id,
                    chapter_id=t.chapter_id,
                    title=t.title,
                    description=t.description,
                    duration_minutes=t.duration_minutes,
                    total_marks=t.total_marks,
                    pass_percentage=t.pass_percentage,
                    deadline=t.deadline,
                    max_attempts=t.max_attempts,
                    is_published=t.is_published,
                    solutions_released_at=t.solutions_released_at,
                    results_released_at=t.results_released_at,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                    chapter_title=t.chapter.title,
                    course_id=c.id,
                    course_title=c.title,
                    question_count=len(t.questions),
                    my_attempts_count=attempt_count or 0,
                    my_best_score=best_score,
                    active_attempt_id=active_id,
                )
            )
        return results


@router.get(
    "/tests/{test_id}",
    response_model=TestDetailResponse,
    summary="Get test details and questions with solution redaction",
)
async def get_test(
    test_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Test)
        .where(Test.id == test_id)
        .options(
            selectinload(Test.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course),
            selectinload(Test.questions),
        )
    )
    res = await db.execute(stmt)
    test = res.scalars().first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    course = test.chapter.subject.course

    # Check student enrollment & solutions release
    solutions_revealed = False
    now = utc_now()

    if current_user.role == "student":
        if not test.is_published:
            raise HTTPException(status_code=404, detail="Test not found or not published")
        enrolled = await is_student_enrolled_in_course(current_user.id, course.id, db)
        if not enrolled:
            raise HTTPException(
                status_code=403,
                detail="Access denied: You are not enrolled in the course for this test",
            )
        if test.solutions_released_at and now >= test.solutions_released_at:
            solutions_revealed = True
    else:
        solutions_revealed = True

    question_responses = []
    for q in test.questions:
        correct = q.correct_option if solutions_revealed else None
        explanation = q.solution_explanation if solutions_revealed else None

        question_responses.append(
            QuestionResponse(
                id=q.id,
                test_id=q.test_id,
                question_text=q.question_text,
                question_image_s3_key=q.question_image_s3_key,
                options=q.options,
                correct_option=correct,
                marks=q.marks,
                negative_marks=q.negative_marks,
                solution_explanation=explanation,
                order_index=q.order_index,
            )
        )

    return TestDetailResponse(
        id=test.id,
        chapter_id=test.chapter_id,
        title=test.title,
        description=test.description,
        duration_minutes=test.duration_minutes,
        total_marks=test.total_marks,
        pass_percentage=test.pass_percentage,
        deadline=test.deadline,
        max_attempts=test.max_attempts,
        is_published=test.is_published,
        solutions_released_at=test.solutions_released_at,
        results_released_at=test.results_released_at,
        created_at=test.created_at,
        updated_at=test.updated_at,
        chapter_title=test.chapter.title,
        course_id=course.id,
        course_title=course.title,
        question_count=len(test.questions),
        questions=question_responses,
    )


@router.patch(
    "/tests/{test_id}",
    response_model=TestResponse,
    summary="Update test details or publication status (Teacher)",
)
async def update_test(
    test_id: uuid.UUID,
    payload: TestUpdate,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Test)
        .where(Test.id == test_id)
        .options(
            selectinload(Test.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course),
            selectinload(Test.questions),
        )
    )
    res = await db.execute(stmt)
    test = res.scalars().first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    course = test.chapter.subject.course
    verify_teacher_ownership(current_user, course)

    if payload.title is not None:
        test.title = payload.title
    if payload.description is not None:
        test.description = payload.description
    if payload.duration_minutes is not None:
        test.duration_minutes = payload.duration_minutes
    if payload.pass_percentage is not None:
        test.pass_percentage = payload.pass_percentage
    if payload.deadline is not None:
        test.deadline = payload.deadline
    if payload.max_attempts is not None:
        test.max_attempts = payload.max_attempts
    if payload.is_published is not None:
        test.is_published = payload.is_published
    if payload.solutions_released_at is not None:
        test.solutions_released_at = payload.solutions_released_at
    if payload.results_released_at is not None:
        test.results_released_at = payload.results_released_at

    await db.commit()
    await db.refresh(test)

    return TestResponse(
        id=test.id,
        chapter_id=test.chapter_id,
        title=test.title,
        description=test.description,
        duration_minutes=test.duration_minutes,
        total_marks=test.total_marks,
        pass_percentage=test.pass_percentage,
        deadline=test.deadline,
        max_attempts=test.max_attempts,
        is_published=test.is_published,
        solutions_released_at=test.solutions_released_at,
        results_released_at=test.results_released_at,
        created_at=test.created_at,
        updated_at=test.updated_at,
        chapter_title=test.chapter.title,
        course_id=course.id,
        course_title=course.title,
        question_count=len(test.questions),
    )


@router.post(
    "/tests/{test_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a question to a test (Teacher)",
)
async def add_question(
    test_id: uuid.UUID,
    payload: QuestionCreate,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Test)
        .where(Test.id == test_id)
        .options(
            selectinload(Test.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course),
            selectinload(Test.questions),
        )
    )
    res = await db.execute(stmt)
    test = res.scalars().first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    course = test.chapter.subject.course
    verify_teacher_ownership(current_user, course)

    question = Question(
        test_id=test.id,
        question_text=payload.question_text,
        options=payload.options,
        correct_option=payload.correct_option,
        marks=payload.marks,
        negative_marks=payload.negative_marks,
        solution_explanation=payload.solution_explanation,
        order_index=payload.order_index,
    )
    db.add(question)

    # Recalculate test total marks
    test.total_marks += payload.marks

    await db.commit()
    await db.refresh(question)

    return QuestionResponse(
        id=question.id,
        test_id=question.test_id,
        question_text=question.question_text,
        question_image_s3_key=question.question_image_s3_key,
        options=question.options,
        correct_option=question.correct_option,
        marks=question.marks,
        negative_marks=question.negative_marks,
        solution_explanation=question.solution_explanation,
        order_index=question.order_index,
    )


# -----------------------------------------------------------------------------
# Timed Attempt Lifecycle & Server-Authoritative Scoring
# -----------------------------------------------------------------------------


@router.post(
    "/tests/{test_id}/attempts/start",
    response_model=AttemptStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start or resume a timed assessment attempt (Student)",
)
async def start_test_attempt(
    test_id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Test)
        .where(Test.id == test_id)
        .options(
            selectinload(Test.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course)
        )
    )
    res = await db.execute(stmt)
    test = res.scalars().first()
    if not test or not test.is_published:
        raise HTTPException(status_code=404, detail="Test not found or not published")

    course = test.chapter.subject.course
    enrolled = await is_student_enrolled_in_course(current_user.id, course.id, db)
    if not enrolled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not enrolled in the course for this test",
        )

    now = utc_now()
    if now > test.deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test deadline has passed. New attempts cannot be started.",
        )

    # Advisory lock to serialize competing attempt requests even when 0 rows exist yet
    await db.execute(
        select(
            func.pg_advisory_xact_lock(
                func.hashtext(f"test_attempt:{test.id}:{current_user.id}")
            )
        )
    )

    # Check for active / ongoing attempt within grace period
    active_stmt = (
        select(TestAttempt)
        .where(
            TestAttempt.test_id == test.id,
            TestAttempt.student_id == current_user.id,
            TestAttempt.is_completed == False,
        )
        .options(selectinload(TestAttempt.answers))
        .with_for_update()
    )
    active_res = await db.execute(active_stmt)
    active_attempt = active_res.scalars().first()

    if active_attempt:
        remaining_seconds = max(0, int((active_attempt.expires_at - now).total_seconds()))
        # Check grace period (30s)
        if remaining_seconds > 0 or now <= active_attempt.expires_at + timedelta(seconds=30):
            saved = {
                str(ans.question_id): ans.selected_option
                for ans in active_attempt.answers
                if ans.selected_option
            }
            return AttemptStartResponse(
                attempt_id=active_attempt.id,
                test_id=test.id,
                attempt_number=active_attempt.attempt_number,
                started_at=active_attempt.started_at,
                expires_at=active_attempt.expires_at,
                remaining_seconds=remaining_seconds,
                is_resumed=True,
                saved_answers=saved,
            )
        else:
            # Expired without submission
            active_attempt.is_completed = True
            await db.commit()

    # Verify attempt limit under transactional lock
    attempts_count_res = await db.execute(
        select(func.count(TestAttempt.id)).where(
            TestAttempt.test_id == test.id,
            TestAttempt.student_id == current_user.id,
        )
    )
    past_attempts = attempts_count_res.scalar_one() or 0
    if past_attempts >= test.max_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum attempt limit of {test.max_attempts} reached for this test",
        )

    # Create server-authoritative attempt
    started_at = now
    expires_at = started_at + timedelta(minutes=test.duration_minutes)
    attempt_number = past_attempts + 1

    new_attempt = TestAttempt(
        test_id=test.id,
        student_id=current_user.id,
        attempt_number=attempt_number,
        started_at=started_at,
        expires_at=expires_at,
        is_completed=False,
        score=Decimal("0.00"),
        total_questions_count=0,
        correct_answers_count=0,
        incorrect_answers_count=0,
        unattempted_count=0,
    )
    db.add(new_attempt)
    await db.commit()
    await db.refresh(new_attempt)

    return AttemptStartResponse(
        attempt_id=new_attempt.id,
        test_id=test.id,
        attempt_number=new_attempt.attempt_number,
        started_at=new_attempt.started_at,
        expires_at=new_attempt.expires_at,
        remaining_seconds=test.duration_minutes * 60,
        is_resumed=False,
        saved_answers={},
    )


@router.post(
    "/tests/attempts/{attempt_id}/save-answer",
    response_model=MessageResponse,
    summary="Save an intermediate MCQ answer (Student)",
)
async def save_answer(
    attempt_id: uuid.UUID,
    payload: SaveAnswerRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(TestAttempt)
        .where(TestAttempt.id == attempt_id)
        .options(selectinload(TestAttempt.test))
    )
    res = await db.execute(stmt)
    attempt = res.scalars().first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot modify another student's test attempt",
        )

    if attempt.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This test attempt has already been submitted",
        )

    # Check server-authoritative expiry with 30s network grace period
    now = utc_now()
    if now > attempt.expires_at + timedelta(seconds=30):
        attempt.is_completed = True
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test attempt time has expired. Further answer modifications are rejected.",
        )

    # Validate question belongs to this test
    q_stmt = select(Question).where(
        Question.id == payload.question_id, Question.test_id == attempt.test_id
    )
    q_res = await db.execute(q_stmt)
    question = q_res.scalars().first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question ID for this test",
        )

    # Upsert answer
    ans_stmt = (
        select(TestAnswer)
        .where(
            TestAnswer.attempt_id == attempt.id,
            TestAnswer.question_id == payload.question_id,
        )
        .with_for_update()
    )
    ans_res = await db.execute(ans_stmt)
    existing_ans = ans_res.scalars().first()

    if existing_ans:
        existing_ans.selected_option = payload.selected_option
        existing_ans.answered_at = now
    else:
        new_ans = TestAnswer(
            attempt_id=attempt.id,
            question_id=payload.question_id,
            selected_option=payload.selected_option,
            is_correct=False,
            marks_awarded=Decimal("0.00"),
            answered_at=now,
        )
        db.add(new_ans)

    await db.commit()
    return MessageResponse(
        message="Answer saved successfully",
        detail=payload.selected_option or "Cleared",
    )


@router.post(
    "/tests/attempts/{attempt_id}/submit",
    response_model=AttemptResultResponse,
    summary="Submit and score timed assessment server-side (Student)",
)
async def submit_test_attempt(
    attempt_id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(TestAttempt)
        .where(TestAttempt.id == attempt_id)
        .options(
            selectinload(TestAttempt.test),
            selectinload(TestAttempt.answers),
        )
        .with_for_update()
    )
    res = await db.execute(stmt)
    attempt = res.scalars().first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot submit another student's test attempt",
        )

    test = attempt.test
    now = utc_now()
    results_released = (
        test.results_released_at is None or now >= test.results_released_at
    )
    solutions_released = (
        results_released
        and test.solutions_released_at is not None
        and now >= test.solutions_released_at
    )

    # Idempotent response if already submitted
    if attempt.is_completed:
        if not results_released:
            return AttemptResultResponse(
                attempt_id=attempt.id,
                test_id=test.id,
                attempt_number=attempt.attempt_number,
                is_completed=True,
                score=Decimal("0.00"),
                total_marks=test.total_marks,
                percentage=Decimal("0.00"),
                passed=False,
                total_questions=attempt.total_questions_count,
                correct_count=0,
                incorrect_count=0,
                unattempted_count=0,
                started_at=attempt.started_at,
                submitted_at=attempt.submitted_at,
                solutions_released=False,
                results_released=False,
                results_released_at=test.results_released_at,
                answers=None,
            )

        percentage = (
            Decimal("0.00")
            if test.total_marks == 0
            else (attempt.score / Decimal(test.total_marks)) * Decimal("100.00")
        )
        passed = (attempt.score >= Decimal(test.total_marks * test.pass_percentage / 100))

        # Build detailed answer breakdown if solutions are released
        answers_breakdown = None
        if solutions_released:
            q_res = await db.execute(
                select(Question)
                .where(Question.test_id == test.id)
                .order_by(Question.order_index)
            )
            questions = q_res.scalars().all()
            ans_map = {ans.question_id: ans for ans in attempt.answers}
            answers_breakdown = [
                AnswerDetailItem(
                    question_id=q.id,
                    selected_option=ans_map.get(q.id).selected_option
                    if ans_map.get(q.id)
                    else None,
                    correct_option=q.correct_option,
                    is_correct=ans_map.get(q.id).is_correct
                    if ans_map.get(q.id)
                    else False,
                    marks_awarded=ans_map.get(q.id).marks_awarded
                    if ans_map.get(q.id)
                    else Decimal("0.00"),
                    solution_explanation=q.solution_explanation,
                )
                for q in questions
            ]

        return AttemptResultResponse(
            attempt_id=attempt.id,
            test_id=test.id,
            attempt_number=attempt.attempt_number,
            is_completed=True,
            score=attempt.score,
            total_marks=test.total_marks,
            percentage=round(percentage, 2),
            passed=passed,
            total_questions=attempt.total_questions_count,
            correct_count=attempt.correct_answers_count,
            incorrect_count=attempt.incorrect_answers_count,
            unattempted_count=attempt.unattempted_count,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            solutions_released=solutions_released,
            results_released=True,
            results_released_at=test.results_released_at,
            answers=answers_breakdown,
        )

    # Server-Authoritative Scoring Engine (Zero Client Trust)
    q_stmt = (
        select(Question)
        .where(Question.test_id == test.id)
        .order_by(Question.order_index)
    )
    q_res = await db.execute(q_stmt)
    questions = q_res.scalars().all()

    existing_answers_map = {ans.question_id: ans for ans in attempt.answers}

    total_score = Decimal("0.00")
    correct_count = 0
    incorrect_count = 0
    unattempted_count = 0

    for q in questions:
        ans = existing_answers_map.get(q.id)
        if ans and ans.selected_option:
            if ans.selected_option == q.correct_option:
                ans.is_correct = True
                ans.marks_awarded = Decimal(q.marks)
                correct_count += 1
                total_score += Decimal(q.marks)
            else:
                ans.is_correct = False
                ans.marks_awarded = -Decimal(q.negative_marks)
                incorrect_count += 1
                total_score -= Decimal(q.negative_marks)
        else:
            unattempted_count += 1
            if not ans:
                new_ans = TestAnswer(
                    attempt_id=attempt.id,
                    question_id=q.id,
                    selected_option=None,
                    is_correct=False,
                    marks_awarded=Decimal("0.00"),
                    answered_at=now,
                )
                db.add(new_ans)

    # Floor score at 0
    final_score = max(Decimal("0.00"), total_score)
    passed = final_score >= Decimal(test.total_marks * test.pass_percentage / 100)
    percentage = (
        Decimal("0.00")
        if test.total_marks == 0
        else (final_score / Decimal(test.total_marks)) * Decimal("100.00")
    )

    attempt.score = final_score
    attempt.is_completed = True
    attempt.submitted_at = now
    attempt.total_questions_count = len(questions)
    attempt.correct_answers_count = correct_count
    attempt.incorrect_answers_count = incorrect_count
    attempt.unattempted_count = unattempted_count

    await db.commit()
    await db.refresh(attempt)

    if not results_released:
        return AttemptResultResponse(
            attempt_id=attempt.id,
            test_id=test.id,
            attempt_number=attempt.attempt_number,
            is_completed=True,
            score=Decimal("0.00"),
            total_marks=test.total_marks,
            percentage=Decimal("0.00"),
            passed=False,
            total_questions=len(questions),
            correct_count=0,
            incorrect_count=0,
            unattempted_count=0,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            solutions_released=False,
            results_released=False,
            results_released_at=test.results_released_at,
            answers=None,
        )

    return AttemptResultResponse(
        attempt_id=attempt.id,
        test_id=test.id,
        attempt_number=attempt.attempt_number,
        is_completed=True,
        score=final_score,
        total_marks=test.total_marks,
        percentage=round(percentage, 2),
        passed=passed,
        total_questions=len(questions),
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        unattempted_count=unattempted_count,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        solutions_released=solutions_released,
        results_released=True,
        results_released_at=test.results_released_at,
        answers=None,
    )


@router.get(
    "/tests/{test_id}/attempts",
    response_model=List[AttemptResultResponse],
    summary="Get all student attempts for a test (Teacher)",
)
async def get_test_attempts(
    test_id: uuid.UUID,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Test)
        .where(Test.id == test_id)
        .options(
            selectinload(Test.chapter)
            .selectinload(Chapter.subject)
            .selectinload(Subject.course)
        )
    )
    res = await db.execute(stmt)
    test = res.scalars().first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    course = test.chapter.subject.course
    verify_teacher_ownership(current_user, course)

    attempts_stmt = (
        select(TestAttempt)
        .where(TestAttempt.test_id == test.id, TestAttempt.is_completed == True)
        .order_by(TestAttempt.score.desc())
    )
    att_res = await db.execute(attempts_stmt)
    attempts = att_res.scalars().all()

    results = []
    for att in attempts:
        percentage = (
            Decimal("0.00")
            if test.total_marks == 0
            else (att.score / Decimal(test.total_marks)) * Decimal("100.00")
        )
        passed = att.score >= Decimal(test.total_marks * test.pass_percentage / 100)

        results.append(
            AttemptResultResponse(
                attempt_id=att.id,
                test_id=test.id,
                attempt_number=att.attempt_number,
                is_completed=True,
                score=att.score,
                total_marks=test.total_marks,
                percentage=round(percentage, 2),
                passed=passed,
                total_questions=att.total_questions_count,
                correct_count=att.correct_answers_count,
                incorrect_count=att.incorrect_answers_count,
                unattempted_count=att.unattempted_count,
                started_at=att.started_at,
                submitted_at=att.submitted_at,
                solutions_released=True,
            )
        )
    return results


@router.get(
    "/tests/{test_id}/attempts/my",
    response_model=List[AttemptResultResponse],
    summary="Get student's own attempts for a test",
)
async def get_my_test_attempts(
    test_id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Test).where(Test.id == test_id)
    res = await db.execute(stmt)
    test = res.scalars().first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    now = utc_now()
    results_released = (
        test.results_released_at is None or now >= test.results_released_at
    )
    solutions_released = (
        results_released
        and test.solutions_released_at is not None
        and now >= test.solutions_released_at
    )

    attempts_stmt = (
        select(TestAttempt)
        .where(
            TestAttempt.test_id == test.id,
            TestAttempt.student_id == current_user.id,
            TestAttempt.is_completed == True,
        )
        .order_by(TestAttempt.attempt_number.desc())
    )
    att_res = await db.execute(attempts_stmt)
    attempts = att_res.scalars().all()

    results = []
    for att in attempts:
        if not results_released:
            results.append(
                AttemptResultResponse(
                    attempt_id=att.id,
                    test_id=test.id,
                    attempt_number=att.attempt_number,
                    is_completed=True,
                    score=Decimal("0.00"),
                    total_marks=test.total_marks,
                    percentage=Decimal("0.00"),
                    passed=False,
                    total_questions=att.total_questions_count,
                    correct_count=0,
                    incorrect_count=0,
                    unattempted_count=0,
                    started_at=att.started_at,
                    submitted_at=att.submitted_at,
                    solutions_released=False,
                    results_released=False,
                    results_released_at=test.results_released_at,
                    answers=None,
                )
            )
        else:
            percentage = (
                Decimal("0.00")
                if test.total_marks == 0
                else (att.score / Decimal(test.total_marks)) * Decimal("100.00")
            )
            passed = att.score >= Decimal(test.total_marks * test.pass_percentage / 100)

            results.append(
                AttemptResultResponse(
                    attempt_id=att.id,
                    test_id=test.id,
                    attempt_number=att.attempt_number,
                    is_completed=True,
                    score=att.score,
                    total_marks=test.total_marks,
                    percentage=round(percentage, 2),
                    passed=passed,
                    total_questions=att.total_questions_count,
                    correct_count=att.correct_answers_count,
                    incorrect_count=att.incorrect_answers_count,
                    unattempted_count=att.unattempted_count,
                    started_at=att.started_at,
                    submitted_at=att.submitted_at,
                    solutions_released=solutions_released,
                    results_released=True,
                    results_released_at=test.results_released_at,
                    answers=None,
                )
            )
    return results
