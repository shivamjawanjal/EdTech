# Database Schema Specification: Relational Contract

- **Target Engine**: PostgreSQL 15+ (Compatible with standard Cloud / Local PostgreSQL)
- **Primary Architect**: `@Database_Agent`
- **Supervising Authority**: `@Education_CTO_Agent`
- **Contributing Collaborators**: `@Backend_Agent`, `@Security_Agent`, `@Assessment_Agent`, `@Analytics_Agent`
- **Status**: Ratified Implementation Contract (Phase 1 MVP)

---

## 1. Global Conventions & Design Invariants

1. **Primary Keys**: Every table uses a `UUID` primary key with default generator `gen_random_uuid()`. Primary keys are named `id`.
2. **Timestamps**:
   - All timestamps are stored as `TIMESTAMPTZ` (UTC with timezone).
   - Every operational table contains `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` and `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`.
   - Display timezone conversion (defaulting to Indian Standard Time `Asia/Kolkata` for the target educator) is executed strictly at the application/presentation layer.
3. **Foreign Key Deletion Semantics**:
   - Hard structural children (e.g. Subjects in a Course, Chapters in a Subject, Lectures in a Chapter) use `ON DELETE CASCADE`.
   - Student work artifacts (Submissions, Test Attempts, Doubts) use `ON DELETE RESTRICT` or soft-delete flags to prevent accidental erasure of historical academic records if a student is deactivated.
4. **Binary & Media Isolation**:
   - Zero binary files are stored in PostgreSQL. Media columns store strictly immutable S3/R2 storage keys (`VARCHAR(500)`).
5. **JSONB Usage**:
   - JSONB is used strictly for polymorphic, schema-flexible payload structures (e.g. MCQ options list, submission attachment metadata, audit delta payloads).
   - Searchable or relational identifiers must NOT be buried in unindexed JSONB keys.
6. **Concurrency & Locking**:
   - Optimistic concurrency control using `updated_at` checks or conditional `UPDATE` statements for evaluation scores and attempt submissions.

---

## 2. Comprehensive Domain Schema Catalog

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DOMAIN-TO-TABLE MAPPING                         │
├──────────────────────────┬─────────────────────────────────────────────┤
│ 1. Identity & Auth       │ users, student_profiles, refresh_tokens     │
│ 2. Enrolment & Cohorts   │ batches, courses, course_batches,           │
│                          │ enrollments                                 │
│ 3. Curriculum Hierarchy  │ subjects, chapters, lectures                │
│ 4. Media & Notes         │ lecture_notes                               │
│ 5. Telemetry & Heartbeat │ video_progress, video_watch_sessions        │
│ 6. Daily Assignments     │ assignments, submissions,                   │
│                          │ submission_attachments                      │
│ 7. Objective Tests       │ tests, questions, test_attempts,            │
│                          │ test_answers                                │
│ 8. Doubts & Q&A          │ doubt_threads, doubt_messages               │
│ 9. Live Classes          │ live_sessions, live_attendance_records      │
│ 10. Announcements & Alerts│ announcements, notifications                │
│ 11. Student Health Analytics│ student_health_summaries, student_activities│
│ 12. Security Audit       │ audit_events                                │
└──────────────────────────┴─────────────────────────────────────────────┘
```

---

### Domain 1: Identity, Authentication & Student Profiles

#### 1.1 `users`
- **Purpose**: Core authentication identity and credential store.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `phone`: `VARCHAR(20)` (`NOT NULL`, Unique, E.164 formatted, e.g. `+919876543210`)
  - `email`: `VARCHAR(255)` (`NULL`, Unique)
  - `hashed_password`: `VARCHAR(255)` (`NOT NULL`)
  - `full_name`: `VARCHAR(150)` (`NOT NULL`)
  - `role`: `VARCHAR(20)` (`NOT NULL`, Check: `role IN ('teacher', 'student')`)
  - `is_active`: `BOOLEAN` (`NOT NULL`, Default `TRUE`)
  - `must_change_password`: `BOOLEAN` (`NOT NULL`, Default `FALSE`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Unique index on `phone`
  - Unique index on `email` WHERE `email IS NOT NULL`
  - Index on `(role, is_active)`

#### 1.2 `student_profiles`
- **Purpose**: Academic, parental, and administrative metadata for enrolled learners.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `user_id`: `UUID` (`NOT NULL`, Unique, FK `users.id` `ON DELETE CASCADE`)
  - `roll_number`: `VARCHAR(50)` (`NULL`, Unique within cohort)
  - `parent_name`: `VARCHAR(150)` (`NULL`)
  - `parent_phone`: `VARCHAR(20)` (`NULL`)
  - `school_name`: `VARCHAR(200)` (`NULL`)
  - `grade_level`: `VARCHAR(50)` (`NULL`, e.g. "Class 10")
  - `target_exam`: `VARCHAR(100)` (`NULL`, e.g. "Board + Olympiad Foundation")
  - `teacher_notes`: `TEXT` (`NULL`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Unique index on `user_id`
  - Index on `parent_phone`

#### 1.3 `refresh_tokens`
- **Purpose**: Secure server-side tracking of active refresh tokens and device sessions.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `user_id`: `UUID` (`NOT NULL`, FK `users.id` `ON DELETE CASCADE`)
  - `token_hash`: `VARCHAR(255)` (`NOT NULL`, Unique, SHA-256 hash of token secret)
  - `user_agent`: `VARCHAR(500)` (`NULL`)
  - `ip_address`: `INET` (`NULL`)
  - `expires_at`: `TIMESTAMPTZ` (`NOT NULL`)
  - `is_revoked`: `BOOLEAN` (`NOT NULL`, Default `FALSE`)
  - `revoked_at`: `TIMESTAMPTZ` (`NULL`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Unique index on `token_hash`
  - Composite index on `(user_id, is_revoked, expires_at)`

---

### Domain 2: Enrolment & Cohort Access Control

#### 2.1 `batches`
- **Purpose**: Logical academic cohorts (e.g. "Class 10 STEM Morning 2026").
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `name`: `VARCHAR(100)` (`NOT NULL`, Unique)
  - `description`: `TEXT` (`NULL`)
  - `academic_year`: `VARCHAR(20)` (`NOT NULL`, e.g. "2026-2027")
  - `is_active`: `BOOLEAN` (`NOT NULL`, Default `TRUE`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)

#### 2.2 `courses`
- **Purpose**: Top-level curriculum containers (e.g. "STEM & Reasoning Comprehensive Foundation").
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `title`: `VARCHAR(200)` (`NOT NULL`)
  - `slug`: `VARCHAR(200)` (`NOT NULL`, Unique)
  - `description`: `TEXT` (`NULL`)
  - `is_published`: `BOOLEAN` (`NOT NULL`, Default `FALSE`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)

#### 2.3 `course_batches`
- **Purpose**: Many-to-many mapping allowing courses to be assigned to one or more batches.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `course_id`: `UUID` (`NOT NULL`, FK `courses.id` `ON DELETE CASCADE`)
  - `batch_id`: `UUID` (`NOT NULL`, FK `batches.id` `ON DELETE CASCADE`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Uniqueness & Constraints**:
  - Unique constraint on `(course_id, batch_id)`

#### 2.4 `enrollments`
- **Purpose**: Maps students to academic batches with explicit access lifecycle status.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `student_id`: `UUID` (`NOT NULL`, FK `users.id` `ON DELETE CASCADE`)
  - `batch_id`: `UUID` (`NOT NULL`, FK `batches.id` `ON DELETE CASCADE`)
  - `enrolled_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `status`: `VARCHAR(20)` (`NOT NULL`, Default `'active'`, Check: `status IN ('active', 'suspended', 'completed')`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Uniqueness & Constraints**:
  - Unique constraint on `(student_id, batch_id)`

---

### Domain 3: Curriculum Hierarchy

#### 3.1 `subjects`
- **Purpose**: Categorical subjects under a course (`Mathematics`, `Science`, `Reasoning`).
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `course_id`: `UUID` (`NOT NULL`, FK `courses.id` `ON DELETE CASCADE`)
  - `name`: `VARCHAR(100)` (`NOT NULL`)
  - `code`: `VARCHAR(20)` (`NOT NULL`, e.g. "MATH", "SCI", "REAS")
  - `icon_slug`: `VARCHAR(50)` (`NULL`)
  - `order_index`: `INT` (`NOT NULL`, Default `0`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes & Uniqueness**:
  - Unique constraint on `(course_id, name)`
  - Index on `(course_id, order_index)`

#### 3.2 `chapters`
- **Purpose**: Pedagogical units/topics within a subject (e.g. "Quadratic Equations").
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `subject_id`: `UUID` (`NOT NULL`, FK `subjects.id` `ON DELETE CASCADE`)
  - `title`: `VARCHAR(200)` (`NOT NULL`)
  - `description`: `TEXT` (`NULL`)
  - `order_index`: `INT` (`NOT NULL`, Default `0`)
  - `is_published`: `BOOLEAN` (`NOT NULL`, Default `TRUE`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(subject_id, order_index)`

#### 3.3 `lectures`
- **Purpose**: Individual lessons containing video lectures and associated materials.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `chapter_id`: `UUID` (`NOT NULL`, FK `chapters.id` `ON DELETE CASCADE`)
  - `title`: `VARCHAR(250)` (`NOT NULL`)
  - `description`: `TEXT` (`NULL`)
  - `duration_seconds`: `INT` (`NOT NULL`, Default `0`, Check: `duration_seconds >= 0`)
  - `video_s3_key`: `VARCHAR(500)` (`NULL`)
  - `video_mime_type`: `VARCHAR(50)` (`NULL`, Default `'video/mp4'`)
  - `order_index`: `INT` (`NOT NULL`, Default `0`)
  - `is_published`: `BOOLEAN` (`NOT NULL`, Default `TRUE`)
  - `published_at`: `TIMESTAMPTZ` (`NULL`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(chapter_id, order_index)`
  - Index on `(published_at DESC)`

---

### Domain 4: Media Assets & Lecture Notes

#### 4.1 `lecture_notes`
- **Purpose**: Curated PDF formula sheets, summaries, or exercise files attached to a lecture.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `lecture_id`: `UUID` (`NOT NULL`, FK `lectures.id` `ON DELETE CASCADE`)
  - `title`: `VARCHAR(200)` (`NOT NULL`)
  - `pdf_s3_key`: `VARCHAR(500)` (`NOT NULL`)
  - `file_size_bytes`: `BIGINT` (`NOT NULL`, Check: `file_size_bytes > 0`)
  - `allow_download`: `BOOLEAN` (`NOT NULL`, Default `TRUE`)
  - `order_index`: `INT` (`NOT NULL`, Default `0`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(lecture_id, order_index)`

---

### Domain 5: Telemetry, Heartbeats & Watch Progress

#### 5.1 `video_progress`
- **Purpose**: Cumulative watch progress per student per lecture.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `student_id`: `UUID` (`NOT NULL`, FK `users.id` `ON DELETE CASCADE`)
  - `lecture_id`: `UUID` (`NOT NULL`, FK `lectures.id` `ON DELETE CASCADE`)
  - `seconds_watched`: `INT` (`NOT NULL`, Default `0`, Check: `seconds_watched >= 0`)
  - `last_position_seconds`: `INT` (`NOT NULL`, Default `0`, Check: `last_position_seconds >= 0`)
  - `completion_percentage`: `SMALLINT` (`NOT NULL`, Default `0`, Check: `completion_percentage BETWEEN 0 AND 100`)
  - `is_completed`: `BOOLEAN` (`NOT NULL`, Default `FALSE`)
  - `first_watched_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `completed_at`: `TIMESTAMPTZ` (`NULL`)
  - `last_heartbeat_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Uniqueness & Constraints**:
  - Unique constraint on `(student_id, lecture_id)`
- **Indexes**:
  - Composite index on `(lecture_id, is_completed)`
  - Index on `(student_id, last_heartbeat_at DESC)`

#### 5.2 `video_watch_sessions`
- **Purpose**: Ephemeral session log capturing raw heartbeat playback intervals to audit watch integrity.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `student_id`: `UUID` (`NOT NULL`, FK `users.id` `ON DELETE CASCADE`)
  - `lecture_id`: `UUID` (`NOT NULL`, FK `lectures.id` `ON DELETE CASCADE`)
  - `session_start_position`: `INT` (`NOT NULL`)
  - `session_end_position`: `INT` (`NOT NULL`)
  - `session_duration_seconds`: `INT` (`NOT NULL`, Check: `session_duration_seconds > 0`)
  - `playback_rate`: `NUMERIC(3,2)` (`NOT NULL`, Default `1.00`)
  - `client_ip`: `INET` (`NULL`)
  - `recorded_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(student_id, lecture_id, recorded_at DESC)`
  - Index on `(recorded_at)` (for rolling retention cleanup)

---

### Domain 6: Daily Assignments, Submissions & Evaluation

#### 6.1 `assignments`
- **Purpose**: Daily homework tasks attached to lectures with submission deadlines.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `lecture_id`: `UUID` (`NOT NULL`, FK `lectures.id` `ON DELETE CASCADE`)
  - `title`: `VARCHAR(250)` (`NOT NULL`)
  - `instructions`: `TEXT` (`NOT NULL`)
  - `question_sheet_s3_key`: `VARCHAR(500)` (`NULL`)
  - `max_marks`: `SMALLINT` (`NOT NULL`, Default `10`, Check: `max_marks > 0`)
  - `deadline`: `TIMESTAMPTZ` (`NOT NULL`)
  - `allow_late_submission`: `BOOLEAN` (`NOT NULL`, Default `TRUE`)
  - `late_deadline`: `TIMESTAMPTZ` (`NULL`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(lecture_id)`
  - Index on `(deadline ASC)`

#### 6.2 `submissions`
- **Purpose**: Student submission header with attempt versioning and grading state.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `assignment_id`: `UUID` (`NOT NULL`, FK `assignments.id` `ON DELETE RESTRICT`)
  - `student_id`: `UUID` (`NOT NULL`, FK `users.id` `ON DELETE RESTRICT`)
  - `attempt_number`: `SMALLINT` (`NOT NULL`, Default `1`, Check: `attempt_number >= 1`)
  - `is_latest`: `BOOLEAN` (`NOT NULL`, Default `TRUE`)
  - `status`: `VARCHAR(30)` (`NOT NULL`, Default `'submitted'`, Check: `status IN ('submitted', 'late', 'resubmission_requested', 'evaluated')`)
  - `submitted_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `is_evaluated`: `BOOLEAN` (`NOT NULL`, Default `FALSE`)
  - `obtained_marks`: `NUMERIC(5,2)` (`NULL`, Check: `obtained_marks >= 0`)
  - `teacher_feedback`: `TEXT` (`NULL`)
  - `evaluated_at`: `TIMESTAMPTZ` (`NULL`)
  - `evaluated_by`: `UUID` (`NULL`, FK `users.id`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Uniqueness & Constraints**:
  - Unique constraint on `(assignment_id, student_id, attempt_number)`
- **Indexes**:
  - Composite index on `(assignment_id, is_latest, is_evaluated)`
  - Composite index on `(student_id, assignment_id, is_latest)`
  - Index on `(submitted_at DESC)`

#### 6.3 `submission_attachments`
- **Purpose**: Individual photo or PDF files uploaded by student for an assignment submission.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `submission_id`: `UUID` (`NOT NULL`, FK `submissions.id` `ON DELETE CASCADE`)
  - `s3_key`: `VARCHAR(500)` (`NOT NULL`)
  - `file_name`: `VARCHAR(255)` (`NOT NULL`)
  - `file_size_bytes`: `BIGINT` (`NOT NULL`, Check: `file_size_bytes > 0 AND file_size_bytes <= 15728640`) -- max 15MB
  - `mime_type`: `VARCHAR(50)` (`NOT NULL`, Check: `mime_type IN ('image/jpeg', 'image/png', 'image/webp', 'application/pdf')`)
  - `page_order`: `SMALLINT` (`NOT NULL`, Default `1`, Check: `page_order >= 1`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(submission_id, page_order)`

---

### Domain 7: Objective Tests, Attempts & Auto-Grading

#### 7.1 `tests`
- **Purpose**: Timed chapter milestone MCQ tests.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `chapter_id`: `UUID` (`NOT NULL`, FK `chapters.id` `ON DELETE RESTRICT`)
  - `title`: `VARCHAR(250)` (`NOT NULL`)
  - `description`: `TEXT` (`NULL`)
  - `duration_minutes`: `SMALLINT` (`NOT NULL`, Check: `duration_minutes > 0 AND duration_minutes <= 180`)
  - `total_marks`: `INT` (`NOT NULL`, Default `0`, Check: `total_marks >= 0`)
  - `pass_percentage`: `SMALLINT` (`NOT NULL`, Default `40`, Check: `pass_percentage BETWEEN 0 AND 100`)
  - `deadline`: `TIMESTAMPTZ` (`NOT NULL`)
  - `max_attempts`: `SMALLINT` (`NOT NULL`, Default `1`, Check: `max_attempts >= 1`)
  - `solutions_released_at`: `TIMESTAMPTZ` (`NULL`)
  - `is_published`: `BOOLEAN` (`NOT NULL`, Default `FALSE`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(chapter_id, deadline)`

#### 7.2 `questions`
- **Purpose**: Questions belonging to an objective test.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `test_id`: `UUID` (`NOT NULL`, FK `tests.id` `ON DELETE CASCADE`)
  - `question_text`: `TEXT` (`NOT NULL`)
  - `question_image_s3_key`: `VARCHAR(500)` (`NULL`)
  - `options`: `JSONB` (`NOT NULL`) -- format: `[{"key": "A", "text": "...", "image_key": null}, ...]`
  - `correct_option`: `VARCHAR(5)` (`NOT NULL`, Check: `correct_option IN ('A', 'B', 'C', 'D')`)
  - `marks`: `SMALLINT` (`NOT NULL`, Default `1`, Check: `marks > 0`)
  - `negative_marks`: `NUMERIC(4,2)` (`NOT NULL`, Default `0.00`, Check: `negative_marks >= 0`)
  - `solution_explanation`: `TEXT` (`NULL`)
  - `order_index`: `SMALLINT` (`NOT NULL`, Default `0`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(test_id, order_index)`

#### 7.3 `test_attempts`
- **Purpose**: Student's timed test sitting session and final evaluated outcome.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `test_id`: `UUID` (`NOT NULL`, FK `tests.id` `ON DELETE RESTRICT`)
  - `student_id`: `UUID` (`NOT NULL`, FK `users.id` `ON DELETE RESTRICT`)
  - `attempt_number`: `SMALLINT` (`NOT NULL`, Default `1`, Check: `attempt_number >= 1`)
  - `started_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `expires_at`: `TIMESTAMPTZ` (`NOT NULL`)
  - `submitted_at`: `TIMESTAMPTZ` (`NULL`)
  - `is_completed`: `BOOLEAN` (`NOT NULL`, Default `FALSE`)
  - `score`: `NUMERIC(6,2)` (`NOT NULL`, Default `0.00`)
  - `total_questions_count`: `SMALLINT` (`NOT NULL`, Default `0`)
  - `correct_answers_count`: `SMALLINT` (`NOT NULL`, Default `0`)
  - `incorrect_answers_count`: `SMALLINT` (`NOT NULL`, Default `0`)
  - `unattempted_count`: `SMALLINT` (`NOT NULL`, Default `0`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Uniqueness & Constraints**:
  - Unique constraint on `(test_id, student_id, attempt_number)`
- **Indexes**:
  - Composite index on `(test_id, is_completed, score DESC)`
  - Composite index on `(student_id, test_id)`

#### 7.4 `test_answers`
- **Purpose**: Normalized record of student choices per question in a test attempt.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `attempt_id`: `UUID` (`NOT NULL`, FK `test_attempts.id` `ON DELETE CASCADE`)
  - `question_id`: `UUID` (`NOT NULL`, FK `questions.id` `ON DELETE RESTRICT`)
  - `selected_option`: `VARCHAR(5)` (`NULL`, Check: `selected_option IN ('A', 'B', 'C', 'D')`)
  - `is_correct`: `BOOLEAN` (`NOT NULL`, Default `FALSE`)
  - `marks_awarded`: `NUMERIC(4,2)` (`NOT NULL`, Default `0.00`)
  - `answered_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Uniqueness & Constraints**:
  - Unique constraint on `(attempt_id, question_id)`
- **Indexes**:
  - Index on `(attempt_id)`
  - Index on `(question_id, is_correct)` (for topic deficiency analytics)

---

### Domain 8: Doubts & Q&A Management

#### 8.1 `doubt_threads`
- **Purpose**: Student questions linked to a specific lecture timestamp or assignment.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `student_id`: `UUID` (`NOT NULL`, FK `users.id` `ON DELETE CASCADE`)
  - `lecture_id`: `UUID` (`NULL`, FK `lectures.id` `ON DELETE SET NULL`)
  - `assignment_id`: `UUID` (`NULL`, FK `assignments.id` `ON DELETE SET NULL`)
  - `lecture_timestamp_seconds`: `INT` (`NULL`)
  - `title`: `VARCHAR(250)` (`NOT NULL`)
  - `status`: `VARCHAR(20)` (`NOT NULL`, Default `'open'`, Check: `status IN ('open', 'resolved', 'closed')`)
  - `resolved_at`: `TIMESTAMPTZ` (`NULL`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(student_id, status)`
  - Index on `(lecture_id, status)`
  - Index on `(status, created_at DESC)` (teacher doubt triage queue)

#### 8.2 `doubt_messages`
- **Purpose**: Chronological messages within a doubt thread.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `thread_id`: `UUID` (`NOT NULL`, FK `doubt_threads.id` `ON DELETE CASCADE`)
  - `sender_id`: `UUID` (`NOT NULL`, FK `users.id` `ON DELETE CASCADE`)
  - `message_text`: `TEXT` (`NOT NULL`)
  - `attachment_s3_key`: `VARCHAR(500)` (`NULL`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(thread_id, created_at ASC)`

---

### Domain 9: Live Classes & Attendance Verification

#### 9.1 `live_sessions`
- **Purpose**: Scheduled live classes (Google Meet) for interactive problem solving.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `batch_id`: `UUID` (`NOT NULL`, FK `batches.id` `ON DELETE CASCADE`)
  - `subject_id`: `UUID` (`NULL`, FK `subjects.id` `ON DELETE SET NULL`)
  - `title`: `VARCHAR(250)` (`NOT NULL`)
  - `scheduled_start_time`: `TIMESTAMPTZ` (`NOT NULL`)
  - `scheduled_end_time`: `TIMESTAMPTZ` (`NOT NULL`)
  - `meet_url`: `VARCHAR(500)` (`NOT NULL`)
  - `recording_lecture_id`: `UUID` (`NULL`, FK `lectures.id` `ON DELETE SET NULL`)
  - `status`: `VARCHAR(20)` (`NOT NULL`, Default `'scheduled'`, Check: `status IN ('scheduled', 'live', 'completed', 'cancelled')`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(batch_id, scheduled_start_time ASC)`
  - Index on `(status, scheduled_start_time ASC)`

#### 9.2 `live_attendance_records`
- **Purpose**: Student presence tracking, explicitly distinguishing click-through evidence from verified participation.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `session_id`: `UUID` (`NOT NULL`, FK `live_sessions.id` `ON DELETE CASCADE`)
  - `student_id`: `UUID` (`NOT NULL`, FK `users.id` `ON DELETE CASCADE`)
  - `click_through_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
  - `client_ip`: `INET` (`NULL`)
  - `user_agent`: `VARCHAR(500)` (`NULL`)
  - `verified_participation`: `BOOLEAN` (`NOT NULL`, Default `FALSE`)
  - `verified_by`: `UUID` (`NULL`, FK `users.id`)
  - `verification_notes`: `TEXT` (`NULL`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Uniqueness & Constraints**:
  - Unique constraint on `(session_id, student_id)`
- **Indexes**:
  - Index on `(session_id, verified_participation)`
  - Index on `(student_id, session_id)`

---

### Domain 10: Announcements & In-App Notifications

#### 10.1 `announcements`
- **Purpose**: Teacher broadcast announcements to batches or the whole institute.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `batch_id`: `UUID` (`NULL`, FK `batches.id` `ON DELETE CASCADE`) -- NULL means all batches
  - `title`: `VARCHAR(250)` (`NOT NULL`)
  - `message_body`: `TEXT` (`NOT NULL`)
  - `priority`: `VARCHAR(20)` (`NOT NULL`, Default `'normal'`, Check: `priority IN ('normal', 'urgent', 'pinned')`)
  - `created_by`: `UUID` (`NOT NULL`, FK `users.id`)
  - `expires_at`: `TIMESTAMPTZ` (`NULL`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(batch_id, created_at DESC)`

#### 10.2 `notifications`
- **Purpose**: Individual in-app notifications with read/unread tracking.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `user_id`: `UUID` (`NOT NULL`, FK `users.id` `ON DELETE CASCADE`)
  - `title`: `VARCHAR(200)` (`NOT NULL`)
  - `body`: `TEXT` (`NOT NULL`)
  - `notification_type`: `VARCHAR(50)` (`NOT NULL`) -- e.g. 'ASSIGNMENT_DUE', 'EVALUATION_PUBLISHED', 'TEST_ANNOUNCED', 'NEW_DOUBT_REPLY'
  - `target_url`: `VARCHAR(500)` (`NULL`)
  - `is_read`: `BOOLEAN` (`NOT NULL`, Default `FALSE`)
  - `read_at`: `TIMESTAMPTZ` (`NULL`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Composite index on `(user_id, is_read, created_at DESC)`

---

### Domain 11: Student Health Summaries & Audit Telemetry

#### 11.1 `student_health_summaries`
- **Purpose**: Cached, explainable student health states to prevent expensive on-the-fly dashboard aggregations.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `student_id`: `UUID` (`NOT NULL`, Unique, FK `users.id` `ON DELETE CASCADE`)
  - `health_status`: `VARCHAR(20)` (`NOT NULL`, Check: `health_status IN ('ON_TRACK', 'NEEDS_ATTENTION', 'AT_RISK')`)
  - `assignment_submission_rate`: `NUMERIC(5,2)` (`NOT NULL`, Default `100.00`)
  - `video_watch_rate`: `NUMERIC(5,2)` (`NOT NULL`, Default `100.00`)
  - `test_score_average`: `NUMERIC(5,2)` (`NOT NULL`, Default `75.00`)
  - `consecutive_missing_assignments`: `SMALLINT` (`NOT NULL`, Default `0`)
  - `days_inactive`: `SMALLINT` (`NOT NULL`, Default `0`)
  - `explainability_reason`: `TEXT` (`NOT NULL`, Default `'Initial enrolment baseline'`)
  - `last_calculated_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Unique index on `student_id`
  - Index on `(health_status, last_calculated_at DESC)`

#### 11.2 `student_activities`
- **Purpose**: Unified daily presence log recording key student pedagogical interactions.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `student_id`: `UUID` (`NOT NULL`, FK `users.id` `ON DELETE CASCADE`)
  - `activity_type`: `VARCHAR(50)` (`NOT NULL`, Check: `activity_type IN ('LOGIN', 'WATCH_LECTURE', 'SUBMIT_ASSIGNMENT', 'ATTEMPT_TEST', 'JOIN_LIVE', 'ASK_DOUBT')`)
  - `entity_id`: `UUID` (`NULL`) -- ID of lecture, assignment, test, etc.
  - `metadata`: `JSONB` (`NULL`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Composite index on `(student_id, created_at DESC)`
  - Index on `(activity_type, created_at DESC)`

---

### Domain 12: Security & Teacher Action Audit Logs

#### 12.1 `audit_events`
- **Purpose**: Immutable security audit trail recording teacher and administrative actions.
- **Fields**:
  - `id`: `UUID` (PK, `gen_random_uuid()`)
  - `actor_id`: `UUID` (`NOT NULL`, FK `users.id` `ON DELETE RESTRICT`)
  - `action`: `VARCHAR(100)` (`NOT NULL`) -- e.g. 'GRADE_MODIFIED', 'STUDENT_SUSPENDED', 'PASSWORD_RESET', 'TEST_DEADLINE_EXTENDED'
  - `target_entity_type`: `VARCHAR(50)` (`NOT NULL`)
  - `target_entity_id`: `UUID` (`NOT NULL`)
  - `previous_state`: `JSONB` (`NULL`)
  - `new_state`: `JSONB` (`NULL`)
  - `ip_address`: `INET` (`NULL`)
  - `user_agent`: `VARCHAR(500)` (`NULL`)
  - `created_at`: `TIMESTAMPTZ` (`NOT NULL`, Default `NOW()`)
- **Indexes**:
  - Index on `(actor_id, created_at DESC)`
  - Index on `(target_entity_type, target_entity_id)`
  - Index on `(action, created_at DESC)`
