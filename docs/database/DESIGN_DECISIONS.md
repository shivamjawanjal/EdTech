# Database & Domain Design Decisions Log

- **Lead Orchestrator**: `@Education_CTO_Agent`
- **Contributing Agents**: `@Database_Agent`, `@Product_Agent`, `@Security_Agent`, `@Assessment_Agent`, `@Analytics_Agent`
- **Status**: Audit & Decision Matrix (Phase 1 MVP)

---

## 1. Decision Resolution Framework

Per project governance, **we do not invent teacher preferences**. Architectural choices requiring educator confirmation are explicitly tagged **`OPEN`**, supplied with a recommended default based on best practices for 150-student STEM coaching, and analyzed for technical/pedagogical trade-offs.

---

## 2. Design Decisions Matrix

### Decision 1: Student Creation and Enrolment Workflow
- **Status**: `OPEN` (Requires Teacher Confirmation)
- **Options Considered**:
  - *Option A (Recommended Default)*: **Teacher-managed batch enrolment**. The teacher uploads a simple CSV or fills a quick form (Full Name, Phone number, Grade). The system creates active student accounts with temporary passwords and flags `must_change_password = TRUE`.
  - *Option B*: **Student self-registration with an invite code / approval queue**. Students sign up via a link, enter a 6-character batch code, and wait for the teacher to click "Approve".
- **Trade-off Analysis**: Option A prevents unauthorized spam signups and maintains absolute teacher control over the 90–150 student cohort. Option B slightly reduces teacher entry time but requires building an approval management UI.
- **Database Contract Impact**: Supported by `users.must_change_password`, `users.is_active`, and `enrollments.status`.

### Decision 2: Multi-Course Enrolment Architecture
- **Status**: `OPEN` (Requires Teacher Confirmation)
- **Options Considered**:
  - *Option A (Recommended Default)*: **Batch-mapped multi-course enrolment**. A student belongs to an academic Batch (e.g. "Class 10 Foundation 2026"), and the teacher assigns one or more Courses to that Batch via `course_batches`. A student can also belong to multiple batches if taking separate programs (e.g. "Foundation Math" + "Weekend Reasoning Crash Course").
  - *Option B*: **Direct 1:1 Student-to-Course binding**.
- **Trade-off Analysis**: Option A mirrors real coaching institutes where 40 students in "Batch A" automatically get access to both Mathematics and Science courses without the teacher enrolling them 80 times individually.
- **Database Contract Impact**: Implemented via `batches`, `courses`, `course_batches`, and `enrollments`.

### Decision 3: Course Access Expiry & Date Boundaries
- **Status**: `OPEN` (Requires Teacher Confirmation)
- **Options Considered**:
  - *Option A (Recommended Default)*: **Cohort academic year lifecycle**. Courses remain open as long as the student's enrolment status is `active`. When an academic year finishes (e.g. March 31, 2027), the teacher toggles the batch or course to archived status.
  - *Option B*: **Hard per-course calendar expiration timestamps** (`access_expires_at`).
- **Trade-off Analysis**: Hard date lockouts often lock out students prematurely during exam delays. Manual status toggling provides flexibility.
- **Database Contract Impact**: Supported via `batches.is_active` and `enrollments.status IN ('active', 'suspended', 'completed')`.

### Decision 4: Assignment Submission Formats & File Limits
- **Status**: `OPEN` (Requires Teacher Confirmation)
- **Options Considered**:
  - *Option A (Recommended Default)*: **High-res camera photos (JPEG, PNG, WebP) and PDFs, max 15MB total, up to 5 pages per submission**.
  - *Option B*: **Unrestricted file formats (Word, ZIP, HEIC)**.
- **Trade-off Analysis**: Option A ensures the split-screen rapid grading console renders images instantly in standard web canvas viewers without expensive server-side document conversion pipelines.
- **Database Contract Impact**: Enforced via check constraint `chk_attachment_mime` and `chk_attachment_size` on `submission_attachments`.

### Decision 5: Test Timing, Retakes, and Scoring Rules
- **Status**: `OPEN` (Requires Teacher Confirmation)
- **Options Considered**:
  - *Option A (Recommended Default)*: **Strict single-attempt for official milestone tests; negative marking disabled by default (0.00); solutions hidden until test deadline passes**. Max attempts configurable per test (`max_attempts = 1`).
  - *Option B*: **Unlimited retakes with highest score retention**.
- **Trade-off Analysis**: For assessing genuine weak students, single-attempt milestone tests prevent answer-memorization gaming. Self-paced practice sets can be assigned with higher attempt limits.
- **Database Contract Impact**: Supported by `tests.max_attempts`, `tests.solutions_released_at`, and unique constraint `(test_id, student_id, attempt_number)` on `test_attempts`.

### Decision 6: Lecture Progress Tracking Semantics
- **Status**: `OPEN` (Requires Teacher Confirmation)
- **Options Considered**:
  - *Option A (Recommended Default)*: **Progress estimate based on cumulative heartbeat pings; milestone badge awarded at $\ge 85\%$ total duration**. Acknowledged in UI as *"Estimated Watch Progress"* rather than certified conceptual understanding.
  - *Option B*: **Forced interactive popup quizzes every 5 minutes during video playback**.
- **Trade-off Analysis**: Option B disrupts video flow on mobile devices. Option A provides accurate engagement tracking without pedagogical annoyance. Real understanding is verified via daily assignments.
- **Database Contract Impact**: Implemented via `video_progress.completion_percentage` and `video_progress.is_completed`.

### Decision 7: Video Storage Provider & Pre-Signed URL Access Policy
- **Status**: `OPEN` (Requires Teacher Confirmation)
- **Options Considered**:
  - *Option A (Recommended Default)*: **Cloudflare R2 object storage with 30-minute pre-signed streaming URLs**. $0 egress bandwidth costs.
  - *Option B*: **AWS S3 + CloudFront CDN with Signed Cookies**.
- **Trade-off Analysis**: Cloudflare R2 eliminates high data egress fees, keeping monthly hosting under $15 total for 150 students streaming 50+ hours of video.
- **Database Contract Impact**: Database stores only S3 keys (`video_s3_key: VARCHAR(500)`). Fully provider-agnostic.

### Decision 8: In-App Notification Read/Unread Semantics
- **Status**: `OPEN` (Requires Teacher Confirmation)
- **Options Considered**:
  - *Option A (Recommended Default)*: **Per-user notification inbox with explicit `is_read` boolean and 'Mark All as Read' action**. Pruned after 60 days.
  - *Option B*: **Global announcement broadcast log with client-side local storage pointers**.
- **Trade-off Analysis**: Option A ensures unread notification badges sync accurately across multiple devices (e.g. student switching from laptop to phone).
- **Database Contract Impact**: Implemented via `notifications` table with partial index on `(user_id, is_read, created_at DESC) WHERE is_read = FALSE`.

### Decision 9: At-Risk Health Thresholds & Explainability
- **Status**: `OPEN` (Requires Teacher Confirmation)
- **Options Considered**:
  - *Option A (Recommended Default)*: **Deterministic 14-day rolling thresholds**:
    - `At Risk`: Inactive > 4 days OR $\ge 3$ consecutive missing homeworks OR test average < 40%.
    - `Needs Attention`: Submission rate 60–79% OR 1–2 missed homeworks OR test average 40–59%.
    - `On Track`: All other active students.
    - Full explainability string stored and visible on teacher dashboard.
  - *Option B*: **Customizable per-chapter weights set by teacher**.
- **Trade-off Analysis**: Option A works immediately out of the box with zero configuration burden on the teacher.
- **Database Contract Impact**: Cached in `student_health_summaries` table with `explainability_reason: TEXT`.
