# Task: TASK-008 Daily Assignment & MCQ Assessment Engine

- **Assigned Agent**: `@Assessment_Agent` (Primary) & `@Education_CTO_Agent` (Lead)
- **Collaborators**: `@Backend_Agent`, `@Database_Agent`, `@Frontend_Agent`, `@Security_Agent`, `@Analytics_Agent`, `@QA_Agent`
- **Domain**: Assessment & Evaluation
- **Status**: Done
- **Target Release**: MVP Phase 1
- **Created Date**: 2026-10-24
- **Completed Date**: 2026-10-24

---

## 1. Objective & Context

Implement the daily assignment, student submission, teacher grading, timed MCQ testing, server-side scoring, and result-release workflows in `EdtechWeb/`.

Follow the core product principle:

**TEACH → ASSIGN → SUBMIT → EVALUATE → TRACK → IMPROVE**

The platform serves approximately 150 students and 1 primary teacher. All grading, clock derivations, correctness flags, and attempt restrictions are authoritative on the server. The client device clock and client-submitted scores are never trusted.

---

## 2. Prerequisites & Dependencies

- Depends on: `[TASK-004]` (PostgreSQL Schema & Models), `[TASK-005]` (FastAPI & Auth), `[TASK-006]` (React PWA Scaffolding), `[TASK-007]` (Media & Attachment Engine)
- Blocks: `[TASK-009]` (Student Health & Diagnostic Engine), `[TASK-010]` (End-to-End QA Test Strategy)

---

## 3. Scope of Work & Completed Deliverables

- [x] **Phase 1: Preflight & Schema Evolution**
  - Audited existing models in `backend/app/models/assessment.py`: `Assignment`, `Submission`, `SubmissionAttachment`, `Test`, `Question`, `TestAttempt`, `TestAnswer`.
  - Added workflow columns:
    - `Assignment.is_published`: Boolean draft/published status flag.
    - `Submission.student_content`: Text response for direct student written solutions.
    - `Submission.is_released`: Boolean flag hiding grades/feedback from students until explicitly released.
    - `Submission.released_at`: Timestamp tracking grade release date.
    - `Test.results_released_at`: Optional timestamp for delayed automated result publication.
  - Generated and applied Alembic migration `d730514f1c62_add_assessment_workflow_fields.py` cleanly across `edtech_dev` and `edtech_test` databases.
- [x] **Phase 2: Pydantic Validation Schemas**
  - Created `backend/app/schemas/assessment.py` containing request and response models:
    - Assignments: `AssignmentCreate`, `AssignmentUpdate`, `AssignmentResponse`, `AssignmentSubmissionQueueResponse`.
    - Submissions: `SubmissionCreateRequest`, `SubmissionGradeRequest`, `SubmissionResponse`, `SubmissionAttachmentResponse`.
    - Tests: `TestCreate`, `TestUpdate`, `TestResponse`, `TestDetailResponse`.
    - Questions: `QuestionCreate`, `QuestionResponse` (with conditional redaction of `correct_option` and `solution_explanation`).
    - Attempt Lifecycle: `AttemptStartResponse`, `SaveAnswerRequest`, `AttemptResultResponse`, `AnswerDetailItem`.
  - Exported schemas cleanly in `backend/app/schemas/__init__.py`.
- [x] **Phase 3: Domain API Implementation (`backend/app/api/v1/assessment.py`)**
  - **Assignment Workflow:**
    - `POST /api/v1/assessment/assignments`: Teacher creates and publishes daily assignments linked to lectures and courses.
    - `GET /api/v1/assessment/assignments`: Role-aware listing. Teachers view all course assignments with submission counters (`total`, `evaluated`, `pending`); students view published assignments in enrolled courses with their own submission status and score.
    - `GET /api/v1/assessment/assignments/{id}`: Detailed assignment instructions and deadline enforcement.
    - `PATCH /api/v1/assessment/assignments/{id}`: Teacher updates deadlines, late policy, or publication status.
    - `POST /api/v1/assessment/assignments/{id}/submissions`: Enrolled student submits text response; determines `'submitted'` vs. `'late'` based on server time; rejects submissions to closed assignments.
    - `GET /api/v1/assessment/assignments/{id}/submissions`: Teacher reviews submission queue with filters (`all`, `pending`, `evaluated`, `late`), student details, attachments, and missing work counts.
    - `GET /api/v1/assessment/assignments/{id}/submissions/my`: Student views own attempt history with redacted marks until released.
    - `POST /api/v1/assessment/submissions/{id}/grade`: Teacher assigns marks and written feedback; validates marks do not exceed `assignment.max_marks`; locks row transactionally.
    - `POST /api/v1/assessment/assignments/{id}/release-grades`: Teacher batch-releases all evaluated grades to students.
  - **Timed MCQ Assessment Workflow:**
    - `POST /api/v1/assessment/tests`: Teacher creates timed test (duration 1-180m, pass %, deadline, max attempts).
    - `GET /api/v1/assessment/tests`: Role-aware listing with attempt counters, best scores, and active attempt indicators.
    - `GET /api/v1/assessment/tests/{id}`: Details and questions. Strictly redacts `correct_option` and `solution_explanation` for students prior to `solutions_released_at`.
    - `PATCH /api/v1/assessment/tests/{id}`: Teacher updates settings or publishes test.
    - `POST /api/v1/assessment/tests/{id}/questions`: Teacher adds question with options A-D, marks, negative marks, and explanations; automatically sums test total marks.
    - `POST /api/v1/assessment/tests/{id}/attempts/start`: Student starts timed attempt. Server-authoritative start time, duration calculation, and 30-second network latency grace period. Safely resumes ongoing uncompleted attempts; enforces `max_attempts`.
    - `POST /api/v1/assessment/tests/attempts/{id}/save-answer`: Student saves intermediate answer; rejects requests past expiry + grace period.
    - `POST /api/v1/assessment/tests/attempts/{id}/submit`: Server-side scoring engine (zero client trust). Calculates positive marks, deducts negative marks, handles unattempted questions, applies floor at 0.00, sets completed status, and returns instant results.
    - `GET /api/v1/assessment/tests/{id}/attempts`: Teacher reviews all student attempt results.
    - `GET /api/v1/assessment/tests/{id}/attempts/my`: Student reviews past attempt history and released solutions.
- [x] **Phase 4: Security & Concurrency Verification**
  - Created automated backend test suite in `backend/tests/test_assessment_api.py` covering:
    - Teacher ownership checks & cross-teacher course isolation (403).
    - Unenrolled student access denial (403).
    - Student IDOR protection for attempts and submissions.
    - Deadline enforcement (on-time, late, and closed).
    - Maximum marks constraint violation rejection (400).
    - Strict redaction of correct options and explanations until release time.
    - Server-authoritative timed scoring and negative marking math.
    - Attempt limit enforcement under repeated/concurrent requests.
  - Full backend test suite: **72 passed, 7 skipped (live S3), 0 failed in 54.24s**.
- [x] **Phase 5: Frontend Integration**
  - Created TypeScript definitions in `frontend/src/types/assessment.ts`.
  - Built API service client in `frontend/src/api/assessmentService.ts`.
  - Built `TeacherAssessmentConsole.tsx` component supporting:
    - Daily Assignments & Grading queue with status filters (`pending`, `evaluated`, `late`, `missing`).
    - Grading modal with marks validation, feedback, and immediate release toggle.
    - Batch release button for evaluated submissions.
    - Timed MCQ test management, question addition with options A-D, and student scores table.
  - Built `StudentQuizView.tsx` (`/student/tests/:testId`) supporting:
    - Pre-assessment instructions and integrity rules card.
    - Server-authoritative countdown timer with urgent visual state.
    - Question navigation ribbon and responsive option selection.
    - Answer clearing and unanswered warning modal.
    - Instant result screen with passed/failed badges, score breakdown, and step-by-step solutions (when released).
  - Built `StudentAssignmentSubmitModal.tsx` for submitting written solutions, uploading attachments, and checking released marks/feedback.
  - Integrated `StudentHome.tsx` and `TeacherDashboard.tsx` with live API endpoints and navigation.
  - Added frontend test suite in `frontend/src/test/AssessmentEngine.test.tsx`: **3 passed**.
  - Verified full frontend test suite: **23 passed in 2.38s**.
  - Verified production build: `npm run build` (`tsc -b && vite build`) passed with zero errors.

---

## 4. Verification & Evidence

| Verification Target | Command Executed | Result |
| :--- | :--- | :--- |
| Database Migration | `alembic upgrade head` | Applied `d730514f1c62_add_assessment_workflow_fields` to `edtech_dev` and `edtech_test` |
| Assessment API Tests | `pytest backend/tests/test_assessment_api.py -v` | **12 passed in 16.66s** (100% pass) |
| Full Backend Regression | `pytest backend/ -v` | **72 passed, 7 skipped in 54.24s** (0 failed) |
| Frontend Unit Tests | `npm test -- --run` | **23 passed in 2.38s** (6 test files) |
| Frontend Production Build | `npm run build` | **`tsc -b && vite build` succeeded in 855ms** |

---

## 5. Security & Invariant Checklist

- [x] **Zero Client Trust**: All marks, scores, percentages, elapsed durations, and pass/fail states are evaluated exclusively on the server.
- [x] **Anti-IDOR Authorization**: Students can never access or modify other students' submissions or test attempts.
- [x] **Enrollment Enforcement**: Only actively enrolled students can access assignments or tests associated with their courses.
- [x] **Teacher Scoping**: Teachers cannot manage assignments, tests, or submissions belonging to courses taught by other instructors.
- [x] **Solution Leakage Prevention**: `correct_option` and `solution_explanation` are stripped from student responses until `solutions_released_at`.
- [x] **Grading Privacy**: Marks and teacher feedback are hidden (`null`) from students until `is_released=True`.
- [x] **Concurrency & Attempt Limits**: Attempt counts are validated under transactional advisory locks (`pg_advisory_xact_lock`) even when zero attempt rows exist.

---

## 6. Audit Findings & Resolution Summary

### 1. Potential Result-Release Inconsistency
- **Finding**: Individual submission grading updates release flags, while a separate batch-release endpoint exists. Grading without immediate release must never expose marks or feedback.
- **Resolution**:
  - `grade_submission` accepts `is_released: bool` (defaulting to unreleased if preferred for batch release).
  - All student queries (`list_assignments`, `get_assignment`, and `get_my_submissions`) strictly redact marks, feedback, and evaluated timestamp whenever `is_released == False`.
  - Batch release endpoint `/api/v1/assessment/assignments/{assignment_id}/release-grades` atomically flips all evaluated submissions to `is_released = True`.

### 2. Attempt-Limit Concurrency
- **Finding**: Transactional locks on nonexistent attempt rows return 0 rows in PostgreSQL MVCC, failing to serialize concurrent requests racing to create attempt #1.
- **Resolution**:
  - Implemented PostgreSQL transactional advisory locks (`pg_advisory_xact_lock(hashtext(f"test_attempt:{test.id}:{student.id}"))` in `start_test_attempt` and `hashtext(f"assignment_sub:{assignment.id}:{student.id}"))` in `submit_assignment`).
  - Serializes all concurrent attempt initialization requests for that user and entity before any query executes, guaranteeing attempt limits are never bypassed.

### 3. Late-Submission Policy
- **Finding**: Ensure `deadline`, `late_deadline`, and resubmission of evaluated submissions are consistent across APIs and UI, and analytics does not classify accepted late work as missing.
- **Resolution**:
  - Standard submissions before `deadline` are marked `"submitted"`. Submissions between `deadline` and `late_deadline` (when enabled) are accepted and marked `"late"`.
  - Accepted late work has `is_latest == True`, correctly included in `submitted_count`, and therefore subtracted from `missing_count = max(0, total_enrolled - submitted_count)`.
  - Evaluated submissions are immutable unless the teacher issues a resubmission request (`/api/v1/assessment/submissions/{id}/request-resubmission`). In the student UI, `StudentAssignmentSubmitModal.tsx` enables editing and submission when `status == 'resubmission_requested'`.

### 4. Assessment Reporting Accuracy
- **Finding**: Check that pending, evaluated, late, and missing counts are calculated from the correct latest submission and active enrollment—not inflated by older attempts or distorted by filters.
- **Resolution**:
  - In `get_submission_queue`, aggregate metrics (`submitted_count`, `evaluated_count`, `pending_count`, `late_count`, `missing_count`) are calculated via an independent database query across all latest submissions (`is_latest == True`), ensuring header metrics remain accurate and invariant under UI status filters (`?status=pending`, etc.).

### 5. Question Privacy & Scoring
- **Finding**: Pre-release answer redaction must be enforced in every student endpoint, including attempt responses and result breakdowns, and scoring must use the question configuration applicable to that attempt.
- **Resolution**:
  - In `GET /tests/{id}`, student question responses redact `correct_option` and `solution_explanation` until `solutions_released_at`.
  - In `POST /tests/attempts/{id}/submit` and `GET /tests/{id}/attempts/my`, if `results_released_at` is in the future, overall score, percentage, and passed status are redacted (`0.00`, `False`, `answers=None`).
  - In `StudentQuizView.tsx`, unreleased test results display a "Assessment Completed - Results Pending Release" status card rather than misleading 0 marks.
  - Server-authoritative scoring computes marks and negative marks from the individual test questions linked to that attempt.

---

## 7. Explicit Documented Limitations (Preserved)

1. **Live S3/R2 Storage Integration Tests**: Remain skipped in offline development environments when live Cloudflare R2 / AWS S3 credentials are not configured in `.env`.
2. **Question Randomization**: Question randomization / shuffling per student attempt is not implemented in MVP scope (questions are ordered by `order_index`).
3. **Teacher UI Question Types**: The teacher UI console exposes single-choice A-D multiple choice questions; numerical and multi-select question types are not exposed in the teacher console.

