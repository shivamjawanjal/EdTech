import os
import uuid
from datetime import datetime, timedelta
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.models.base import utc_now
from app.models.identity import User, StudentProfile
from app.models.enrolment import Course, Batch, CourseBatch, Enrollment
from app.models.curriculum import Subject, Chapter, Lecture, LectureNote
from app.models.assessment import Assignment, Submission, SubmissionAttachment
from app.models.media import MediaUpload
from app.services.content_validator import detect_mime_from_magic_bytes, validate_stored_content
from app.services.storage_service import get_storage_service, MockStorageService

settings = get_settings()

# Synthetic magic byte samples for testing
SAMPLE_MP4_HEADER = b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41\x00\x00\x00\x08free" + (b"\x00" * 400)
SAMPLE_PDF_HEADER = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n" + (b"\x00" * 400)
SAMPLE_JPEG_HEADER = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00" + (b"\x00" * 400)
SAMPLE_PNG_HEADER = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + (b"\x00" * 400)
SAMPLE_WEBP_HEADER = b"RIFF\x24\x00\x00\x00WEBPVP8 " + (b"\x00" * 400)
SAMPLE_FAKE_TEXT = b"Hello world, this is a plain text file masquerading as a media file"


@pytest_asyncio.fixture(scope="function")
async def media_fixture(db_session: AsyncSession, test_teacher: User, test_student: User):
    """
    Sets up a full curriculum hierarchy:
    Course -> Subject -> Chapter -> Lecture
    Batch -> CourseBatch -> Enrollment (for test_student)
    Assignment -> Submission (for test_student)
    Plus a second student not enrolled in the course.
    """
    # 1. Course
    course = Course(
        title="Class 10 Advanced Mathematics",
        slug="class-10-maths-" + uuid.uuid4().hex[:6],
        description="Comprehensive Mathematics Curriculum",
        is_published=True,
    )
    db_session.add(course)
    await db_session.flush()

    # 2. Subject
    subject = Subject(
        course_id=course.id,
        name="Trigonometry & Geometry",
        code="MATH-101",
        order_index=1,
    )
    db_session.add(subject)
    await db_session.flush()

    # 3. Chapter
    chapter = Chapter(
        subject_id=subject.id,
        title="Heights and Distances",
        order_index=1,
        is_published=True,
    )
    db_session.add(chapter)
    await db_session.flush()

    # 4. Lecture
    lecture = Lecture(
        chapter_id=chapter.id,
        title="Angles of Elevation and Depression",
        duration_seconds=2400,
        video_s3_key="lectures/seed/video_sample.mp4",
        video_mime_type="video/mp4",
        order_index=1,
        is_published=True,
    )
    db_session.add(lecture)
    await db_session.flush()

    # 5. Lecture Note
    note = LectureNote(
        lecture_id=lecture.id,
        title="Trigonometry Summary Formula Sheet",
        pdf_s3_key="lectures/seed/formula_sheet.pdf",
        file_size_bytes=1048576,  # 1 MB
        allow_download=True,
        order_index=1,
    )
    db_session.add(note)
    await db_session.flush()

    # 6. Batch & Enrollment for test_student
    batch = Batch(
        name="Target 100 Batch " + uuid.uuid4().hex[:6],
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

    # 7. Assignment & Submission for test_student
    assignment = Assignment(
        lecture_id=lecture.id,
        title="Heights and Distances Practice Set",
        instructions="Solve questions 1-5 and upload photo",
        max_marks=10,
        deadline=utc_now() + timedelta(days=7),
    )
    db_session.add(assignment)
    await db_session.flush()

    submission = Submission(
        assignment_id=assignment.id,
        student_id=test_student.id,
        attempt_number=1,
        status="submitted",
    )
    db_session.add(submission)
    await db_session.flush()

    attachment = SubmissionAttachment(
        submission_id=submission.id,
        s3_key="submissions/seed/attachment_1.jpg",
        file_name="homework_page_1.jpg",
        file_size_bytes=524288,
        mime_type="image/jpeg",
        page_order=1,
    )
    db_session.add(attachment)
    await db_session.flush()

    # 8. Second Student (NOT enrolled in this course)
    student2 = User(
        phone="+919800000002",
        email="student002@edtech.local",
        hashed_password=hash_password("StudentPassword123!"),
        full_name="Student 002 (Unenrolled)",
        role="student",
        is_active=True,
    )
    db_session.add(student2)
    await db_session.flush()

    submission2 = Submission(
        assignment_id=assignment.id,
        student_id=student2.id,
        attempt_number=1,
        status="submitted",
    )
    db_session.add(submission2)
    await db_session.flush()

    attachment2 = SubmissionAttachment(
        submission_id=submission2.id,
        s3_key="submissions/seed/attachment_2.jpg",
        file_name="student2_homework.jpg",
        file_size_bytes=614400,
        mime_type="image/jpeg",
        page_order=1,
    )
    db_session.add(attachment2)
    await db_session.flush()

    return {
        "course": course,
        "lecture": lecture,
        "note": note,
        "batch": batch,
        "assignment": assignment,
        "submission": submission,
        "attachment": attachment,
        "student2": student2,
        "submission2": submission2,
        "attachment2": attachment2,
    }


def auth_headers(user: User) -> dict:
    """Generate Authorization Bearer token headers for test requests."""
    token = create_access_token(subject=str(user.id), role=user.role)
    return {"Authorization": f"Bearer {token}"}


def get_err(resp) -> str:
    """Extract error detail from FastAPI JSON response."""
    data = resp.json()
    return str(data.get("error") or data.get("detail") or "")


# ==============================================================================
# 1. Content Validator & Magic Bytes Unit Tests
# ==============================================================================
def test_detect_mime_from_magic_bytes():
    """Verify accurate file signature detection for MP4, PDF, JPEG, PNG, and WebP."""
    assert detect_mime_from_magic_bytes(SAMPLE_MP4_HEADER) == "video/mp4"
    assert detect_mime_from_magic_bytes(SAMPLE_PDF_HEADER) == "application/pdf"
    assert detect_mime_from_magic_bytes(SAMPLE_JPEG_HEADER) == "image/jpeg"
    assert detect_mime_from_magic_bytes(SAMPLE_PNG_HEADER) == "image/png"
    assert detect_mime_from_magic_bytes(SAMPLE_WEBP_HEADER) == "image/webp"
    assert detect_mime_from_magic_bytes(SAMPLE_FAKE_TEXT) is None
    assert detect_mime_from_magic_bytes(b"") is None


def test_validate_stored_content_rejection():
    """Verify mismatched content types and extensions are strictly rejected."""
    # Text file disguised as MP4
    is_valid, detected, err = validate_stored_content(
        purpose="lecture_video",
        file_name="malicious.mp4",
        declared_mime="video/mp4",
        actual_size=1024,
        header_bytes=SAMPLE_FAKE_TEXT,
    )
    assert not is_valid
    assert "Unrecognized or corrupted" in err

    # PDF file disguised as image
    is_valid, detected, err = validate_stored_content(
        purpose="submission_attachment",
        file_name="homework.jpg",
        declared_mime="image/jpeg",
        actual_size=1024,
        header_bytes=SAMPLE_PDF_HEADER,
    )
    assert not is_valid
    assert detected == "application/pdf"
    assert "mismatch" in err.lower()


# ==============================================================================
# 2. Upload Initiation API Tests
# ==============================================================================
@pytest.mark.asyncio
async def test_teacher_can_initiate_lecture_video_upload(
    client: AsyncClient, test_teacher: User, media_fixture: dict
):
    """Teacher initiates pre-signed upload ticket for lecture video."""
    lecture = media_fixture["lecture"]
    headers = auth_headers(test_teacher)

    payload = {
        "purpose": "lecture_video",
        "target_id": str(lecture.id),
        "file_name": "chapter1_angles.mp4",
        "declared_size_bytes": 500000000,  # 500 MB
        "declared_mime_type": "video/mp4",
    }

    resp = await client.post("/api/v1/media/uploads", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()

    assert "upload_id" in data
    assert "upload_url" in data
    assert data["bucket_name"] == settings.S3_BUCKET_NAME
    assert data["expires_in_seconds"] == settings.SIGNED_URL_UPLOAD_TTL_SECONDS
    # Server-generated key format
    assert data["object_key"].startswith(f"lectures/{lecture.id}/video/")
    assert data["object_key"].endswith(".mp4")


@pytest.mark.asyncio
async def test_student_cannot_initiate_lecture_upload(
    client: AsyncClient, test_student: User, media_fixture: dict
):
    """Student attempting to upload lecture media receives 403 Forbidden."""
    lecture = media_fixture["lecture"]
    headers = auth_headers(test_student)

    payload = {
        "purpose": "lecture_video",
        "target_id": str(lecture.id),
        "file_name": "hacked_video.mp4",
        "declared_size_bytes": 10000000,
        "declared_mime_type": "video/mp4",
    }

    resp = await client.post("/api/v1/media/uploads", json=payload, headers=headers)
    assert resp.status_code == 403
    assert "Teacher privileges required" in get_err(resp)


@pytest.mark.asyncio
async def test_student_can_initiate_own_submission_attachment_upload(
    client: AsyncClient, test_student: User, media_fixture: dict
):
    """Student initiates upload for their own valid submission."""
    submission = media_fixture["submission"]
    headers = auth_headers(test_student)

    payload = {
        "purpose": "submission_attachment",
        "target_id": str(submission.id),
        "file_name": "page_2_solution.jpg",
        "declared_size_bytes": 2048000,  # 2 MB
        "declared_mime_type": "image/jpeg",
        "extra_metadata": {"page_order": 2},
    }

    resp = await client.post("/api/v1/media/uploads", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["object_key"].startswith(f"submissions/{submission.id}/")


@pytest.mark.asyncio
async def test_student_cannot_upload_to_another_student_submission(
    client: AsyncClient, media_fixture: dict
):
    """Student attempting to upload to another student's submission receives 403 Forbidden."""
    student2 = media_fixture["student2"]
    student1_submission = media_fixture["submission"]
    headers = auth_headers(student2)

    payload = {
        "purpose": "submission_attachment",
        "target_id": str(student1_submission.id),
        "file_name": "tampered_page.jpg",
        "declared_size_bytes": 1024000,
        "declared_mime_type": "image/jpeg",
    }

    resp = await client.post("/api/v1/media/uploads", json=payload, headers=headers)
    assert resp.status_code == 403
    assert "another student's submission" in get_err(resp)


@pytest.mark.asyncio
async def test_oversized_file_rejected_at_initiation(
    client: AsyncClient, test_student: User, media_fixture: dict
):
    """Declared file size exceeding max limit (15MB for attachments) is rejected with 422."""
    submission = media_fixture["submission"]
    headers = auth_headers(test_student)

    payload = {
        "purpose": "submission_attachment",
        "target_id": str(submission.id),
        "file_name": "huge_attachment.pdf",
        "declared_size_bytes": 20 * 1024 * 1024,  # 20 MB (> 15 MB limit)
        "declared_mime_type": "application/pdf",
    }

    resp = await client.post("/api/v1/media/uploads", json=payload, headers=headers)
    assert resp.status_code == 422
    assert "exceeds maximum allowed size" in get_err(resp)


# ==============================================================================
# 3. Upload Completion and Validation API Tests
# ==============================================================================
@pytest.mark.asyncio
async def test_complete_upload_success_transitions_to_ready(
    client: AsyncClient, test_teacher: User, media_fixture: dict
):
    """
    Teacher uploads lecture note PDF into mock storage and completes upload.
    Verifies state transitions PENDING -> READY and LectureNote record is created.
    """
    lecture = media_fixture["lecture"]
    headers = auth_headers(test_teacher)
    storage = get_storage_service()
    assert isinstance(storage, MockStorageService)

    # 1. Initiate upload
    init_resp = await client.post(
        "/api/v1/media/uploads",
        json={
            "purpose": "lecture_note",
            "target_id": str(lecture.id),
            "file_name": "chapter1_cheatsheet.pdf",
            "declared_size_bytes": len(SAMPLE_PDF_HEADER),
            "declared_mime_type": "application/pdf",
            "extra_metadata": {"title": "Chapter 1 Cheatsheet"},
        },
        headers=headers,
    )
    assert init_resp.status_code == 201
    upload_data = init_resp.json()
    upload_id = upload_data["upload_id"]
    object_key = upload_data["object_key"]

    # 2. Simulate direct transfer into mock storage
    storage.store_mock_object(object_key, SAMPLE_PDF_HEADER, "application/pdf")

    # 3. Call completion endpoint
    comp_resp = await client.post(f"/api/v1/media/uploads/{upload_id}/complete", headers=headers)
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()

    assert comp_data["status"] == "READY"
    assert comp_data["detected_mime_type"] == "application/pdf"
    assert comp_data["actual_size_bytes"] == len(SAMPLE_PDF_HEADER)


@pytest.mark.asyncio
async def test_complete_upload_fails_on_magic_byte_mismatch(
    client: AsyncClient, test_teacher: User, media_fixture: dict
):
    """
    Upload claims to be MP4 video, but payload is plain text.
    Completion verification must reject the upload and set status to REJECTED.
    """
    lecture = media_fixture["lecture"]
    headers = auth_headers(test_teacher)
    storage = get_storage_service()
    assert isinstance(storage, MockStorageService)

    init_resp = await client.post(
        "/api/v1/media/uploads",
        json={
            "purpose": "lecture_video",
            "target_id": str(lecture.id),
            "file_name": "spoofed_video.mp4",
            "declared_size_bytes": len(SAMPLE_FAKE_TEXT),
            "declared_mime_type": "video/mp4",
        },
        headers=headers,
    )
    assert init_resp.status_code == 201
    upload_id = init_resp.json()["upload_id"]
    object_key = init_resp.json()["object_key"]

    # Store fake text under MP4 key
    storage.store_mock_object(object_key, SAMPLE_FAKE_TEXT, "video/mp4")

    # Completion should fail
    comp_resp = await client.post(f"/api/v1/media/uploads/{upload_id}/complete", headers=headers)
    assert comp_resp.status_code == 400
    assert "Media validation failed" in get_err(comp_resp)


@pytest.mark.asyncio
async def test_complete_nonexistent_upload_returns_404(
    client: AsyncClient, test_teacher: User
):
    """Attempting to complete a non-existent upload ID returns 404."""
    headers = auth_headers(test_teacher)
    random_id = str(uuid.uuid4())
    resp = await client.post(f"/api/v1/media/uploads/{random_id}/complete", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_student_cannot_complete_another_users_upload(
    client: AsyncClient, test_teacher: User, media_fixture: dict
):
    """Student attempting to complete teacher's upload ticket receives 403 Forbidden."""
    lecture = media_fixture["lecture"]
    student2 = media_fixture["student2"]
    teacher_headers = auth_headers(test_teacher)
    student2_headers = auth_headers(student2)

    init_resp = await client.post(
        "/api/v1/media/uploads",
        json={
            "purpose": "lecture_video",
            "target_id": str(lecture.id),
            "file_name": "teacher_lecture.mp4",
            "declared_size_bytes": 1000000,
            "declared_mime_type": "video/mp4",
        },
        headers=teacher_headers,
    )
    upload_id = init_resp.json()["upload_id"]

    # Student 2 tries to complete teacher's upload
    resp = await client.post(f"/api/v1/media/uploads/{upload_id}/complete", headers=student2_headers)
    assert resp.status_code == 403
    assert "not authorized to complete" in get_err(resp)


@pytest.mark.asyncio
async def test_teacher_cannot_upload_to_another_teachers_course(
    client: AsyncClient, test_teacher: User, db_session: AsyncSession, media_fixture: dict
):
    """Teacher cannot attach media to a course assigned to a different instructor."""
    course = media_fixture["course"]
    lecture = media_fixture["lecture"]

    # Assign course to another teacher
    other_teacher = User(
        phone="+919800000099",
        email="other_teacher@edtech.local",
        hashed_password=hash_password("TeacherPassword123!"),
        full_name="Prof. Other Instructor",
        role="teacher",
        is_active=True,
    )
    db_session.add(other_teacher)
    await db_session.flush()

    course.instructor_id = other_teacher.id
    await db_session.flush()

    # test_teacher attempts to upload to other_teacher's course
    headers = auth_headers(test_teacher)
    resp = await client.post(
        "/api/v1/media/uploads",
        json={
            "purpose": "lecture_video",
            "target_id": str(lecture.id),
            "file_name": "unauthorized_video.mp4",
            "declared_size_bytes": 1000000,
            "declared_mime_type": "video/mp4",
        },
        headers=headers,
    )
    assert resp.status_code == 403
    assert "another teacher's course" in get_err(resp)


@pytest.mark.asyncio
async def test_student_cannot_upload_to_evaluated_submission(
    client: AsyncClient, test_student: User, db_session: AsyncSession, media_fixture: dict
):
    """Student cannot attach files to a submission that has already been evaluated."""
    submission = media_fixture["submission"]
    submission.status = "evaluated"
    await db_session.flush()

    headers = auth_headers(test_student)
    resp = await client.post(
        "/api/v1/media/uploads",
        json={
            "purpose": "submission_attachment",
            "target_id": str(submission.id),
            "file_name": "late_attempt.jpg",
            "declared_size_bytes": 1000000,
            "declared_mime_type": "image/jpeg",
        },
        headers=headers,
    )
    assert resp.status_code == 400
    assert "already evaluated submission" in get_err(resp)


@pytest.mark.asyncio
async def test_duplicate_or_sequential_upload_completion_rejection(
    client: AsyncClient, test_teacher: User, media_fixture: dict
):
    """Calling complete twice on the same upload ticket rejects the second attempt with 400."""
    lecture = media_fixture["lecture"]
    headers = auth_headers(test_teacher)
    storage = get_storage_service()

    init_resp = await client.post(
        "/api/v1/media/uploads",
        json={
            "purpose": "lecture_note",
            "target_id": str(lecture.id),
            "file_name": "test_note_duplicate.pdf",
            "declared_size_bytes": len(SAMPLE_PDF_HEADER),
            "declared_mime_type": "application/pdf",
        },
        headers=headers,
    )
    upload_id = init_resp.json()["upload_id"]
    object_key = init_resp.json()["object_key"]
    storage.store_mock_object(object_key, SAMPLE_PDF_HEADER, "application/pdf")

    # First completion succeeds
    resp1 = await client.post(f"/api/v1/media/uploads/{upload_id}/complete", headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "READY"

    # Second completion fails
    resp2 = await client.post(f"/api/v1/media/uploads/{upload_id}/complete", headers=headers)
    assert resp2.status_code == 400
    assert "already been processed with status 'READY'" in get_err(resp2)


# ==============================================================================
# 4. Playback and Download Authorization Tests (Anti-IDOR)
# ==============================================================================
@pytest.mark.asyncio
async def test_enrolled_student_can_get_playback_url(
    client: AsyncClient, test_student: User, media_fixture: dict
):
    """Enrolled student can retrieve 30-minute signed playback URL."""
    lecture = media_fixture["lecture"]
    headers = auth_headers(test_student)

    resp = await client.get(f"/api/v1/media/assets/{lecture.id}/play", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "playback_url" in data
    assert data["expires_in_seconds"] == settings.SIGNED_URL_VIDEO_TTL_SECONDS
    assert data["title"] == lecture.title
    assert data["mime_type"] == "video/mp4"


@pytest.mark.asyncio
async def test_unenrolled_student_cannot_get_playback_url(
    client: AsyncClient, media_fixture: dict
):
    """Unenrolled student attempting to play lecture video receives 403 Forbidden."""
    lecture = media_fixture["lecture"]
    student2 = media_fixture["student2"]
    headers = auth_headers(student2)

    resp = await client.get(f"/api/v1/media/assets/{lecture.id}/play", headers=headers)
    assert resp.status_code == 403
    assert "not enrolled in the course" in get_err(resp)


@pytest.mark.asyncio
async def test_teacher_can_always_play_lecture(
    client: AsyncClient, test_teacher: User, media_fixture: dict
):
    """Teacher has administrative access to preview any lecture video."""
    lecture = media_fixture["lecture"]
    headers = auth_headers(test_teacher)

    resp = await client.get(f"/api/v1/media/assets/{lecture.id}/play", headers=headers)
    assert resp.status_code == 200
    assert "playback_url" in resp.json()


@pytest.mark.asyncio
async def test_student_can_download_enrolled_note(
    client: AsyncClient, test_student: User, media_fixture: dict
):
    """Enrolled student can retrieve 15-minute signed download URL for lecture notes."""
    note = media_fixture["note"]
    headers = auth_headers(test_student)

    resp = await client.get(
        f"/api/v1/media/assets/{note.id}/download?asset_type=lecture_note",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "download_url" in data
    assert data["expires_in_seconds"] == settings.SIGNED_URL_DOWNLOAD_TTL_SECONDS
    assert "filename=" in data["download_url"]


@pytest.mark.asyncio
async def test_student_cannot_download_another_student_attachment(
    client: AsyncClient, test_student: User, media_fixture: dict
):
    """Anti-IDOR: Student 1 attempting to download Student 2's attachment receives 403 Forbidden."""
    att2 = media_fixture["attachment2"]
    headers = auth_headers(test_student)

    resp = await client.get(
        f"/api/v1/media/assets/{att2.id}/download?asset_type=submission_attachment",
        headers=headers,
    )
    assert resp.status_code == 403
    assert "cannot access attachments belonging to other students" in get_err(resp)


@pytest.mark.asyncio
async def test_student_can_download_own_attachment(
    client: AsyncClient, test_student: User, media_fixture: dict
):
    """Student can retrieve signed download URL for their own submitted attachment."""
    att1 = media_fixture["attachment"]
    headers = auth_headers(test_student)

    resp = await client.get(
        f"/api/v1/media/assets/{att1.id}/download?asset_type=submission_attachment",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "download_url" in data
    assert data["file_name"] == att1.file_name


@pytest.mark.asyncio
async def test_teacher_can_download_any_student_attachment(
    client: AsyncClient, test_teacher: User, media_fixture: dict
):
    """Teacher can download any student's assignment attachment for grading evaluation."""
    att1 = media_fixture["attachment"]
    headers = auth_headers(test_teacher)

    resp = await client.get(
        f"/api/v1/media/assets/{att1.id}/download?asset_type=submission_attachment",
        headers=headers,
    )
    assert resp.status_code == 200
    assert "download_url" in resp.json()


# ==============================================================================
# 5. Local Mock Direct PUT Handler Test
# ==============================================================================
@pytest.mark.asyncio
async def test_mock_storage_put_handler(client: AsyncClient):
    """Verify local mock storage PUT handler successfully stores bytes."""
    test_key = "test_folder/sample.bin"
    test_bytes = b"Sample mock payload binary bytes"

    resp = await client.put(
        f"/api/v1/media/mock-storage/{test_key}",
        content=test_bytes,
        headers={"Content-Type": "application/octet-stream"},
    )
    assert resp.status_code == 200
    assert resp.json()["bytes"] == len(test_bytes)

    storage = get_storage_service()
    assert isinstance(storage, MockStorageService)
    meta = storage.get_object_metadata(test_key)
    assert meta is not None
    assert meta.content_length == len(test_bytes)
