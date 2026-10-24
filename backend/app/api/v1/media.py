import os
import uuid
from datetime import timedelta
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db, require_teacher
from app.core.config import get_settings
from app.models.base import utc_now
from app.models.identity import User
from app.models.curriculum import Lecture, LectureNote, Chapter, Subject
from app.models.enrolment import Course, CourseBatch, Enrollment
from app.models.assessment import Submission, SubmissionAttachment
from app.models.media import MediaUpload
from app.schemas.media import (
    MediaUploadInitRequest,
    MediaUploadInitResponse,
    MediaUploadCompleteResponse,
    MediaPlaybackResponse,
    MediaDownloadResponse,
)
from app.services.content_validator import validate_file_metadata, validate_stored_content
from app.services.storage_service import get_storage_service, MockStorageService

settings = get_settings()
router = APIRouter(prefix="/media", tags=["media"])


@router.post(
    "/uploads",
    response_model=MediaUploadInitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize direct-to-storage media upload ticket",
)
async def initialize_upload(
    payload: MediaUploadInitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authorize and generate a short-lived pre-signed URL for direct client-to-storage transfer.
    Server generates safe object keys and creates a PENDING media upload record.
    """
    storage = get_storage_service()

    # 1. Role and Target Authorization
    if payload.purpose in ("lecture_video", "lecture_note"):
        if current_user.role != "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access restricted: Teacher privileges required to upload lecture media",
            )
        # Verify target lecture exists and check course instructor ownership
        lecture_stmt = (
            select(Lecture)
            .where(Lecture.id == payload.target_id)
            .options(
                selectinload(Lecture.chapter)
                .selectinload(Chapter.subject)
                .selectinload(Subject.course)
            )
        )
        res = await db.execute(lecture_stmt)
        lecture = res.scalars().first()
        if not lecture:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target lecture with ID '{payload.target_id}' not found",
            )

        course = lecture.chapter.subject.course
        if course.instructor_id is not None and course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to attach media to another teacher's course",
            )

    elif payload.purpose == "submission_attachment":
        # Verify target submission exists and belongs to current student (or teacher)
        sub_stmt = select(Submission).where(Submission.id == payload.target_id)
        res = await db.execute(sub_stmt)
        submission = res.scalars().first()
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target submission with ID '{payload.target_id}' not found",
            )

        if current_user.role == "student" and submission.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot upload attachments to another student's submission",
            )

        if submission.status == "evaluated":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot attach files to an already evaluated submission",
            )

    # 2. Metadata, extension, and size limits validation
    is_valid, err_msg = validate_file_metadata(
        purpose=payload.purpose,
        file_name=payload.file_name,
        declared_mime=payload.declared_mime_type,
        declared_size=payload.declared_size_bytes,
    )
    if not is_valid:
        raise HTTPException(
            status_code=422,
            detail=err_msg,
        )

    # 3. Server-Generated Safe Object Key
    _, ext = os.path.splitext(payload.file_name.lower())
    random_token = uuid.uuid4().hex
    if payload.purpose == "lecture_video":
        object_key = f"lectures/{payload.target_id}/video/{random_token}{ext}"
    elif payload.purpose == "lecture_note":
        object_key = f"lectures/{payload.target_id}/notes/{random_token}{ext}"
    else:
        object_key = f"submissions/{payload.target_id}/{random_token}{ext}"

    expires_in = settings.SIGNED_URL_UPLOAD_TTL_SECONDS
    ticket = storage.generate_upload_url(
        object_key=object_key,
        content_type=payload.declared_mime_type,
        max_size_bytes=payload.declared_size_bytes,
        expires_in=expires_in,
    )

    # 4. Persist PENDING upload record
    expires_at = utc_now() + timedelta(seconds=expires_in)
    upload_record = MediaUpload(
        user_id=current_user.id,
        purpose=payload.purpose,
        target_id=payload.target_id,
        bucket_name=settings.S3_BUCKET_NAME,
        object_key=object_key,
        file_name=payload.file_name,
        declared_mime_type=payload.declared_mime_type,
        declared_size_bytes=payload.declared_size_bytes,
        status="PENDING",
        upload_url_expires_at=expires_at,
        extra_metadata=payload.extra_metadata or {},
    )
    db.add(upload_record)
    await db.commit()
    await db.refresh(upload_record)

    return MediaUploadInitResponse(
        upload_id=upload_record.id,
        upload_url=ticket.upload_url,
        object_key=object_key,
        bucket_name=settings.S3_BUCKET_NAME,
        expires_in_seconds=expires_in,
        headers=ticket.headers,
    )


@router.post(
    "/uploads/{upload_id}/complete",
    response_model=MediaUploadCompleteResponse,
    summary="Complete and validate uploaded media object",
)
async def complete_upload(
    upload_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate uploaded media content headers and size before publication.
    Enforces row-level locking (with_for_update) to prevent concurrent completion race conditions,
    verifies magic bytes, and transitions status PENDING -> READY (or REJECTED).
    """
    storage = get_storage_service()

    # 1. Fetch upload record with row-level lock
    stmt = select(MediaUpload).where(MediaUpload.id == upload_id).with_for_update()
    res = await db.execute(stmt)
    upload = res.scalars().first()
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media upload ticket '{upload_id}' not found",
        )

    # 2. Ownership verification
    if upload.user_id != current_user.id and current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to complete this upload",
        )

    # 3. Status verification
    if upload.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload ticket has already been processed with status '{upload.status}'",
        )

    # 4. Expiry check
    if utc_now() > upload.upload_url_expires_at:
        upload.status = "REJECTED"
        upload.rejection_reason = "Upload ticket expired before completion"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload ticket has expired. Please initiate a new upload request.",
        )

    # 5. Verify object existence in object storage
    meta = storage.get_object_metadata(upload.object_key)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stored object not found. Ensure direct storage PUT transfer completed successfully.",
        )

    # 6. Read initial byte slice for magic byte inspection
    header_bytes = storage.get_object_header_bytes(upload.object_key, byte_count=512)
    if not header_bytes:
        upload.status = "REJECTED"
        upload.rejection_reason = "Empty object or unable to read file header"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stored object is empty or could not be inspected",
        )

    # 7. Validate content signatures
    is_valid, detected_mime, err_msg = validate_stored_content(
        purpose=upload.purpose,
        file_name=upload.file_name,
        declared_mime=upload.declared_mime_type,
        actual_size=meta.content_length,
        header_bytes=header_bytes,
    )

    if not is_valid:
        upload.status = "REJECTED"
        upload.actual_size_bytes = meta.content_length
        upload.detected_mime_type = detected_mime
        upload.rejection_reason = err_msg
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Media validation failed: {err_msg}",
        )

    # 8. Mark READY and link to target entity
    upload.status = "READY"
    upload.actual_size_bytes = meta.content_length
    upload.detected_mime_type = detected_mime
    upload.validated_at = utc_now()

    if upload.purpose == "lecture_video":
        lec_res = await db.execute(select(Lecture).where(Lecture.id == upload.target_id))
        lecture = lec_res.scalars().first()
        if lecture:
            lecture.video_s3_key = upload.object_key
            lecture.video_mime_type = detected_mime

    elif upload.purpose == "lecture_note":
        extra = upload.extra_metadata or {}
        note_title = extra.get("title") or upload.file_name
        order_index = int(extra.get("order_index", 0))
        new_note = LectureNote(
            lecture_id=upload.target_id,
            title=note_title,
            pdf_s3_key=upload.object_key,
            file_size_bytes=meta.content_length,
            allow_download=True,
            order_index=order_index,
        )
        db.add(new_note)

    elif upload.purpose == "submission_attachment":
        extra = upload.extra_metadata or {}
        page_order = int(extra.get("page_order", 1))
        new_att = SubmissionAttachment(
            submission_id=upload.target_id,
            s3_key=upload.object_key,
            file_name=upload.file_name,
            file_size_bytes=meta.content_length,
            mime_type=detected_mime,
            page_order=page_order,
        )
        db.add(new_att)

    await db.commit()
    await db.refresh(upload)

    return MediaUploadCompleteResponse(
        upload_id=upload.id,
        status=upload.status,
        purpose=upload.purpose,
        target_id=upload.target_id,
        object_key=upload.object_key,
        actual_size_bytes=upload.actual_size_bytes,
        detected_mime_type=upload.detected_mime_type,
        validated_at=upload.validated_at,
    )


@router.get(
    "/assets/{asset_id}/play",
    response_model=MediaPlaybackResponse,
    summary="Get short-lived signed video playback URL",
)
async def get_playback_url(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Issue short-lived signed URL (30 min TTL) for lecture video playback.
    Enforces student batch enrollment authorization and verified ready media state.
    """
    storage = get_storage_service()

    # 1. Fetch lecture and related curriculum hierarchy
    stmt = (
        select(Lecture)
        .where(Lecture.id == asset_id)
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
            detail="Lecture not found",
        )

    if not lecture.is_published and current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found or not published",
        )

    if not lecture.video_s3_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture video has not been uploaded yet",
        )

    # 2. Anti-IDOR Authorization Check for Students
    if current_user.role == "student":
        course = lecture.chapter.subject.course
        enrollment_stmt = (
            select(Enrollment)
            .join(CourseBatch, CourseBatch.batch_id == Enrollment.batch_id)
            .where(
                Enrollment.student_id == current_user.id,
                Enrollment.status == "active",
                CourseBatch.course_id == course.id,
            )
        )
        enr_res = await db.execute(enrollment_stmt)
        if not enr_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not enrolled in the course for this lecture",
            )

    # 3. Generate signed playback URL (30 minutes TTL)
    ttl = settings.SIGNED_URL_VIDEO_TTL_SECONDS
    signed_url = storage.generate_download_url(
        object_key=lecture.video_s3_key,
        disposition="inline",
        expires_in=ttl,
    )

    return MediaPlaybackResponse(
        playback_url=signed_url,
        expires_in_seconds=ttl,
        mime_type=lecture.video_mime_type,
        title=lecture.title,
        duration_seconds=lecture.duration_seconds,
    )


@router.get(
    "/assets/{asset_id}/download",
    response_model=MediaDownloadResponse,
    summary="Get short-lived signed download URL for notes or attachments",
)
async def get_download_url(
    asset_id: uuid.UUID,
    asset_type: Literal["lecture_note", "submission_attachment"] = Query(..., description="Asset type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Issue short-lived signed download URL (15 min TTL) for lecture notes or student attachments.
    Enforces strict access control and anti-IDOR checks.
    """
    storage = get_storage_service()
    ttl = settings.SIGNED_URL_DOWNLOAD_TTL_SECONDS

    if asset_type == "lecture_note":
        stmt = (
            select(LectureNote)
            .where(LectureNote.id == asset_id)
            .options(
                selectinload(LectureNote.lecture)
                .selectinload(Lecture.chapter)
                .selectinload(Chapter.subject)
                .selectinload(Subject.course)
            )
        )
        res = await db.execute(stmt)
        note = res.scalars().first()
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lecture note not found",
            )

        if not note.allow_download and current_user.role != "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Download is not permitted for this lecture note",
            )

        # Student enrollment authorization check
        if current_user.role == "student":
            course = note.lecture.chapter.subject.course
            enrollment_stmt = (
                select(Enrollment)
                .join(CourseBatch, CourseBatch.batch_id == Enrollment.batch_id)
                .where(
                    Enrollment.student_id == current_user.id,
                    Enrollment.status == "active",
                    CourseBatch.course_id == course.id,
                )
            )
            enr_res = await db.execute(enrollment_stmt)
            if not enr_res.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You are not enrolled in the course for this note",
                )

        signed_url = storage.generate_download_url(
            object_key=note.pdf_s3_key,
            filename=f"{note.title}.pdf",
            disposition="attachment",
            expires_in=ttl,
        )
        return MediaDownloadResponse(
            download_url=signed_url,
            expires_in_seconds=ttl,
            file_name=f"{note.title}.pdf",
            file_size_bytes=note.file_size_bytes,
        )

    elif asset_type == "submission_attachment":
        stmt = (
            select(SubmissionAttachment)
            .where(SubmissionAttachment.id == asset_id)
            .options(selectinload(SubmissionAttachment.submission))
        )
        res = await db.execute(stmt)
        attachment = res.scalars().first()
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission attachment not found",
            )

        # Anti-IDOR: Students can only download their own submission attachments
        if current_user.role == "student" and attachment.submission.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot access attachments belonging to other students",
            )

        signed_url = storage.generate_download_url(
            object_key=attachment.s3_key,
            filename=attachment.file_name,
            disposition="attachment",
            expires_in=ttl,
        )
        return MediaDownloadResponse(
            download_url=signed_url,
            expires_in_seconds=ttl,
            file_name=attachment.file_name,
            file_size_bytes=attachment.file_size_bytes,
        )


# Dedicated Local Mock Storage Route (for local testing without AWS credentials)
@router.put(
    "/mock-storage/{object_key:path}",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def mock_storage_upload_handler(
    object_key: str,
    request: Request,
):
    """Local simulation endpoint for direct PUT upload when STORAGE_PROVIDER == 'mock'."""
    if settings.STORAGE_PROVIDER != "mock":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock storage disabled")

    storage = get_storage_service()
    if isinstance(storage, MockStorageService):
        body = await request.body()
        content_type = request.headers.get("content-type", "application/octet-stream")
        storage.store_mock_object(object_key, body, content_type)
        return {"message": "Mock upload stored successfully", "bytes": len(body), "key": object_key}

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Mock adapter error")
