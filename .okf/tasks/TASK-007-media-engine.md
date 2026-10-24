# Task: TASK-007 Secure Object Storage and Media Delivery Engine

- **Assigned Agent**: `@Media_Agent` (Primary) & `@Education_CTO_Agent` (Lead)
- **Collaborators**: `@Backend_Agent`, `@Security_Agent`, `@Database_Agent`, `@Frontend_Agent`, `@QA_Agent`
- **Domain**: Media & Object Storage
- **Status**: Done
- **Target Release**: MVP Phase 1
- **Created Date**: 2026-10-24
- **Completed Date**: 2026-10-24

---

## 1. Objective & Context

Implement secure, provider-configurable object-storage integration for lecture videos, lecture notes, and student assignment attachments using the existing FastAPI backend, PostgreSQL models, and React frontend.

The platform serves approximately 150 students and 1 primary teacher. Binary media transfers never pass through FastAPI memory or PostgreSQL tables. Transfers occur directly between the client browser and private cloud object storage via short-lived pre-signed URLs.

---

## 2. Prerequisites & Dependencies

- Depends on: `[TASK-004]` (PostgreSQL Schema & Models), `[TASK-005]` (FastAPI & Auth), `[TASK-006]` (React PWA Scaffolding)
- Blocks: `[TASK-008]` (Assessment & MCQ Assessment Logic)

---

## 3. Scope of Work & Completed Deliverables

- [x] **Phase 1: Inspection & Task Registry Audit**
  - Inspected repository models (`Lecture`, `LectureNote`, `Assignment`, `Submission`, `SubmissionAttachment`).
  - Audited route conventions, HttpOnly cookie authentication, and CSRF protection behavior.
  - Confirmed `TASK-007` is registered as backlog and available in `.okf/tasks/TASK_INDEX.md`.
  - Identified requirement for explicit upload lifecycle state tracking (`PENDING`, `VALIDATING`, `READY`, `REJECTED`).
- [x] **Phase 2: Object-Storage Abstraction**
  - Built `BaseStorageService` in `backend/app/services/storage_service.py`.
  - Implemented `S3StorageService` supporting AWS S3 and Cloudflare R2 (via `boto3`).
  - Implemented `MockStorageService` for offline development and deterministic CI testing without credentials.
  - Added `boto3>=1.34.0` to `backend/requirements.txt`.
- [x] **Phase 3: Database Integration & Migration**
  - Created `MediaUpload` model in `backend/app/models/media.py` tracking direct upload sessions, statuses (`PENDING`, `VALIDATING`, `READY`, `REJECTED`), server-generated keys, declared/actual sizes, and magic byte validation state.
  - Generated and applied Alembic migration `db90fd9f0b84_create_media_uploads_table.py` across `edtech_dev` and `edtech_test` databases.
- [x] **Phase 4: Content Validation & File Signature Engine**
  - Built `backend/app/services/content_validator.py` with magic byte detection for MP4, WebM, PDF, JPEG, PNG, and WebP.
  - Enforced cross-validation between declared MIME types, file extensions, and detected binary signatures.
  - Enforced strict size limits (1.5GB video, 50MB notes, 15MB student attachments).
- [x] **Phase 5: Authorization & Media API Endpoints**
  - Implemented `POST /api/v1/media/uploads`: Validates teacher/student scope, generates random object key, persists PENDING upload, and issues signed upload ticket.
  - Implemented `POST /api/v1/media/uploads/{id}/complete`: Confirms stored object existence, validates magic bytes and actual size, marks READY, and updates curriculum/assessment tables.
  - Implemented `GET /api/v1/media/assets/{id}/play`: Verifies course-batch enrollment for students and issues 30-minute signed streaming URL.
  - Implemented `GET /api/v1/media/assets/{id}/download`: Enforces Anti-IDOR (students only download their own submission attachments and enrolled notes) and issues 15-minute signed download URL.
- [x] **Phase 6: Frontend Integration**
  - Built `frontend/src/api/mediaService.ts` for upload initiation, direct browser-to-storage transfer with real-time percentage progress, and completion verification.
  - Built dedicated `StudentLectureView.tsx` (`/student/lectures/:lectureId`) with HTML5 video player, 30-minute expiration countdown timer, renewal retry, unavailable media state, and notes download button.
  - Connected `StudentHome.tsx` to link to `/student/lectures/:lectureId` and added `StudentAttachmentUploader.tsx` modal for homework photos.
  - Added `TeacherMediaManager.tsx` modal in `TeacherDashboard.tsx` for video and notes uploading.
- [x] **Phase 7: Testing & Verification**
  - Automated backend tests in `backend/tests/test_media_api.py`: **19 passed in 9.91s**.
  - Full backend test suite: **57 passed in 20.71s**.
  - Frontend test suite with Vitest: **20 passed in 1.84s** (including `StudentLectureView.test.tsx`).
  - Production TypeScript build (`tsc -b && vite build`): **0 errors, 0 warnings**.
- [x] **Phase 8: Configuration & Documentation**
  - Updated `backend/.env.example` with media storage variables, TTLs, and size limits.
  - Created `docs/engineering/MEDIA_ENGINE_SETUP.md` detailing architecture, security rules, R2/S3 setups, validation limits, and cost projections ($0.60/mo with R2 zero-egress).

---

## 4. Key Security & Architectural Invariants

1. **Anti-IDOR Enforcement**:
   - Students cannot initiate uploads targeting another student's submission.
   - Students cannot download attachments belonging to other students (`403 Forbidden`).
   - Students cannot play lecture videos or download notes for courses they are not actively enrolled in (`403 Forbidden`).
2. **Zero Large Binary Proxying**:
   - Browser transfers directly to S3/R2 endpoints.
   - FastAPI server never buffers multi-gigabyte video files in memory.
3. **Magic Byte Verification Before Publication**:
   - Files are rejected if the header signature does not match declared MIME type or file extension.
   - Target database records (`Lecture.video_s3_key`, `LectureNote`, `SubmissionAttachment`) are only populated upon verified `READY` transition.

---

## 5. Test Summary

- Backend: 57 tests passing (`test_auth_api`, `test_database_infra`, `test_media_api`, `test_migrations`, `test_models`, `test_security_deps`, `test_seed`).
- Frontend: 20 tests passing (`apiClient`, `DesignTokensAndBadges`, `ProtectedRoute`, `StudentLectureView`, `LoginPage`).
