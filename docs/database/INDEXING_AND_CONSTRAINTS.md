# Indexing Strategy, Database Constraints & Concurrency Rules

- **Target Engine**: PostgreSQL 15+
- **Architect**: `@Database_Agent`
- **Reviewed by**: `@Security_Agent`, `@QA_Agent`, `@Education_CTO_Agent`
- **Status**: Ratified Implementation Contract

---

## 1. Concurrency Invariants & Integrity Guarantees

In an educational platform where 150 students simultaneously submit assignments, take timed tests, or stream video lectures, race conditions must be mitigated at the database constraint level:

### 1.1 Invariant 1: Assignment Submission Uniqueness & Resubmission History
- **Problem**: When a teacher requests a resubmission, updating the existing row in-place destroys the original upload and teacher feedback, making grade disputes unverifiable.
- **Contract Solution**:
  ```sql
  ALTER TABLE submissions 
    ADD CONSTRAINT uq_submissions_attempt 
    UNIQUE (assignment_id, student_id, attempt_number);

  -- Partial unique index ensuring only one active 'latest' submission exists per student
  CREATE UNIQUE INDEX uq_submissions_single_latest 
    ON submissions (assignment_id, student_id) 
    WHERE is_latest = TRUE;
  ```

### 1.2 Invariant 2: Timed Test Sitting Expiry & Single Active Attempt
- **Problem**: Student might open multiple browser tabs or replay submit requests to alter test answers.
- **Contract Solution**:
  ```sql
  ALTER TABLE test_attempts 
    ADD CONSTRAINT uq_test_attempts_attempt 
    UNIQUE (test_id, student_id, attempt_number);

  ALTER TABLE test_answers 
    ADD CONSTRAINT uq_test_answers_question 
    UNIQUE (attempt_id, question_id);

  -- Check constraint ensuring attempt cannot be submitted before it started
  ALTER TABLE test_attempts
    ADD CONSTRAINT chk_test_attempt_timestamps 
    CHECK (submitted_at IS NULL OR submitted_at >= started_at);
  ```

### 1.3 Invariant 3: Video Watch Heartbeat Telemetry Idempotency
- **Problem**: 150 students emit a telemetry heartbeat every 10 seconds (15 requests/sec). Heartbeat updates must be atomic and avoid row-level lock contention.
- **Contract Solution**:
  ```sql
  ALTER TABLE video_progress 
    ADD CONSTRAINT uq_video_progress_student_lecture 
    UNIQUE (student_id, lecture_id);

  -- In FastAPI repository, use atomic upsert:
  -- INSERT INTO video_progress (student_id, lecture_id, seconds_watched, ...)
  -- VALUES (...)
  -- ON CONFLICT (student_id, lecture_id) 
  -- DO UPDATE SET 
  --   seconds_watched = video_progress.seconds_watched + EXCLUDED.seconds_watched,
  --   last_position_seconds = EXCLUDED.last_position_seconds,
  --   completion_percentage = LEAST(100, ROUND(((video_progress.seconds_watched + EXCLUDED.seconds_watched)::numeric / NULLIF(EXCLUDED.duration_seconds, 0)) * 100)),
  --   is_completed = CASE WHEN ((video_progress.seconds_watched + EXCLUDED.seconds_watched)::numeric / NULLIF(EXCLUDED.duration_seconds, 0)) >= 0.85 THEN TRUE ELSE video_progress.is_completed END,
  --   last_heartbeat_at = NOW();
  ```

### 1.4 Invariant 4: Attendance Telemetry vs. Verified Participation
- **Problem**: A student clicking a Google Meet link does not prove they actually stayed for the 60-minute class.
- **Contract Solution**:
  ```sql
  ALTER TABLE live_attendance_records
    ADD CONSTRAINT uq_live_attendance_session_student
    UNIQUE (session_id, student_id);

  -- verified_participation can only be marked TRUE by an authenticated teacher
  ```

---

## 2. Check Constraints Catalog

```sql
-- Role and identity validation
ALTER TABLE users ADD CONSTRAINT chk_users_role 
  CHECK (role IN ('teacher', 'student'));

-- File size validation (Max 15MB for student submissions)
ALTER TABLE submission_attachments ADD CONSTRAINT chk_attachment_size 
  CHECK (file_size_bytes > 0 AND file_size_bytes <= 15728640);

ALTER TABLE submission_attachments ADD CONSTRAINT chk_attachment_mime 
  CHECK (mime_type IN ('image/jpeg', 'image/png', 'image/webp', 'application/pdf'));

-- Percentage boundaries
ALTER TABLE video_progress ADD CONSTRAINT chk_completion_percentage 
  CHECK (completion_percentage BETWEEN 0 AND 100);

ALTER TABLE tests ADD CONSTRAINT chk_test_pass_percentage 
  CHECK (pass_percentage BETWEEN 0 AND 100);

-- Marks boundaries
ALTER TABLE assignments ADD CONSTRAINT chk_assignment_max_marks 
  CHECK (max_marks > 0);

ALTER TABLE submissions ADD CONSTRAINT chk_submission_marks 
  CHECK (obtained_marks IS NULL OR obtained_marks >= 0);

-- Status enum sanity
ALTER TABLE submissions ADD CONSTRAINT chk_submission_status 
  CHECK (status IN ('submitted', 'late', 'resubmission_requested', 'evaluated'));

ALTER TABLE doubt_threads ADD CONSTRAINT chk_doubt_status 
  CHECK (status IN ('open', 'resolved', 'closed'));

ALTER TABLE live_sessions ADD CONSTRAINT chk_live_status 
  CHECK (status IN ('scheduled', 'live', 'completed', 'cancelled'));

ALTER TABLE student_health_summaries ADD CONSTRAINT chk_health_status 
  CHECK (health_status IN ('ON_TRACK', 'NEEDS_ATTENTION', 'AT_RISK'));
```

---

## 3. High-Performance B-Tree Index Matrix

### 3.1 Composite Indexes (Critical Dashboard Paths)
```sql
-- 1. Teacher Rapid Grading Queue (Find latest unevaluated submissions for an assignment)
CREATE INDEX idx_submissions_grading_queue 
  ON submissions (assignment_id, is_latest, is_evaluated) 
  WHERE is_latest = TRUE AND is_evaluated = FALSE;

-- 2. Student Submissions Feed (Find student's active submissions)
CREATE INDEX idx_submissions_student_latest 
  ON submissions (student_id, assignment_id, is_latest);

-- 3. Teacher Today's Lecture Watch Compliance (Who watched vs unwatched)
CREATE INDEX idx_video_progress_compliance 
  ON video_progress (lecture_id, is_completed);

-- 4. Student Health Triage Cache (Filter at-risk students for teacher alerts)
CREATE INDEX idx_health_summaries_triage 
  ON student_health_summaries (health_status, last_calculated_at DESC);

-- 5. Student Notifications Unread Feed
CREATE INDEX idx_notifications_unread 
  ON notifications (user_id, is_read, created_at DESC) 
  WHERE is_read = FALSE;

-- 6. Inbound Teacher Doubt Triage Queue
CREATE INDEX idx_doubt_threads_open 
  ON doubt_threads (status, created_at DESC) 
  WHERE status = 'open';

-- 7. Test Item Difficulty Analytics (Which questions had highest failure rates)
CREATE INDEX idx_test_answers_item_analysis 
  ON test_answers (question_id, is_correct);
```

### 3.2 Foreign Key & Structural Navigation Indexes
```sql
-- Curriculum hierarchy order traversal
CREATE INDEX idx_subjects_course_order ON subjects (course_id, order_index);
CREATE INDEX idx_chapters_subject_order ON chapters (subject_id, order_index);
CREATE INDEX idx_lectures_chapter_order ON lectures (chapter_id, order_index);
CREATE INDEX idx_lecture_notes_lecture ON lecture_notes (lecture_id, order_index);

-- Batch and live schedules
CREATE INDEX idx_course_batches_batch ON course_batches (batch_id);
CREATE INDEX idx_enrollments_student ON enrollments (student_id);
CREATE INDEX idx_live_sessions_batch_time ON live_sessions (batch_id, scheduled_start_time ASC);

-- Security audit lookups
CREATE INDEX idx_audit_events_actor ON audit_events (actor_id, created_at DESC);
CREATE INDEX idx_audit_events_target ON audit_events (target_entity_type, target_entity_id);
```
