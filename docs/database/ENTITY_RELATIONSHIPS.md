# Entity Relationship Model & Relational Schema Specification

- **Primary Architect**: `@Database_Agent`
- **Approving Authority**: `@Education_CTO_Agent`
- **Status**: Complete 12-Domain Production Contract (Phase 1 MVP)

---

## 1. Relational Schema Architecture Overview

The database architecture is designed in PostgreSQL with strict foreign key constraints, cascading deletions for structural hierarchies, protective `RESTRICT` rules for academic artifacts, and composite B-tree indexes optimized for the 150-student scale.

```
                               ┌─────────────────┐
                               │     batches     │
                               │(id, name, year) │
                               └────────┬────────┘
                                        │1
                    ┌───────────────────┼───────────────────┐
                    │*                  │*                  │*
         ┌──────────▼──────────┐ ┌──────▼──────┐ ┌──────────▼──────────┐
         │   course_batches    │ │ enrollments │ │    live_sessions    │
         │(course_id, batch_id)│ │(student,btch│ │(meet_url, sched_time│
         └──────────▲──────────┘ └──────┬──────┘ └──────────┬──────────┘
                    │*                  │*                  │1
         ┌──────────┴──────────┐        │                   │*
         │       courses       │        │        ┌──────────▼──────────┐
         │(id, title, slug...) │        │        │live_attendance_recs │
         └──────────┬──────────┘        │        │(click_time, verified│
                    │1                  │        └──────────▲──────────┘
                    │*                  │                   │*
         ┌──────────▼──────────┐        │                   │
         │      subjects       │        │                   │
         │ (id, name, code...) │        │                   │
         └──────────┬──────────┘        │                   │
                    │1                  │                   │
                    │*                  │                   │
         ┌──────────▼──────────┐        │                   │
         │      chapters       │        │                   │
         │ (id, title, desc...)│        │                   │
         └──────────┬──────────┘        │                   │
                    │1                  │                   │
                    ├───────────────────┼───────────────────┤
                    │*                  │*                  │*
         ┌──────────▼──────────┐ ┌──────▼──────┐ ┌──────────▼──────────┐
         │      lectures       │ │    tests    │ │    doubt_threads    │
         │(video_key, duration)│ │(dur, marks) │ │(title, status, subj)│
         └──────────┬──────────┘ └──────┬──────┘ └──────────┬──────────┘
                    │1                  │1                  │1
     ┌──────────────┼──────────────┐    │*                  │*
     │*             │*             │*   ▼        ┌──────────▼──────────┐
┌────▼────┐    ┌────▼────┐    ┌────▼────┐┌─────┐ │   doubt_messages    │
│  notes  │    │ assign- │    │video_   ││ques-│ │(sender, msg, attach)│
│ (s3_key)│    │  ments  │    │progress ││tions│ └─────────────────────┘
└─────────┘    └────┬────┘    └────┬────┘└─────┘
                    │1             │*       │1
                    │*             │        │*
               ┌────▼────┐         │     ┌──▼──────────┐
               │submiss- │         │     │test_attempts│
               │  ions   │         │     │(score, timer│
               └────┬────┘         │     └──┬──────────┘
                    │1             │        │1
                    │*             │        │*
               ┌────▼────┐         │     ┌──▼──────────┐
               │submiss_ │         │     │test_answers │
               │attachmts│         │     │(selected, ok│
               └─────────┘         │     └─────────────┘
                                   ▼
                       ┌─────────────────────────┐
                       │          users          │
                       │   (id, phone, role...)  │
                       └───────────┬─────────────┘
                                   │1
       ┌───────────────────────────┼───────────────────────────┐
       │1                          │1                          │1
┌──────▼──────┐             ┌──────▼──────┐             ┌──────▼──────┐
│student_prof-│             │health_summa-│             │refresh_tok- │
│    iles     │             │    ries     │             │    ens      │
└─────────────┘             └─────────────┘             └─────────────┘
```

---

## 2. Domain Relationship Catalog

### 2.1 Identity & Enrolment
- `users` (1) ── (1) `student_profiles` [ON DELETE CASCADE]
- `users` (1) ── (*) `refresh_tokens` [ON DELETE CASCADE]
- `users` (1) ── (*) `enrollments` [ON DELETE CASCADE]
- `batches` (1) ── (*) `enrollments` [ON DELETE CASCADE]
- `batches` (*) ── (*) `courses` [via `course_batches` junction table]
- `batches` (1) ── (*) `live_sessions` [ON DELETE CASCADE]
- `batches` (1) ── (*) `announcements` [ON DELETE CASCADE]

### 2.2 Curriculum & Media Hierarchy
- `courses` (1) ── (*) `subjects` [ON DELETE CASCADE]
- `subjects` (1) ── (*) `chapters` [ON DELETE CASCADE]
- `chapters` (1) ── (*) `lectures` [ON DELETE CASCADE]
- `lectures` (1) ── (*) `lecture_notes` [ON DELETE CASCADE]
- `lectures` (1) ── (*) `assignments` [ON DELETE CASCADE]
- `chapters` (1) ── (*) `tests` [ON DELETE RESTRICT]

### 2.3 Assessment & Evaluation
- `assignments` (1) ── (*) `submissions` [ON DELETE RESTRICT]
- `submissions` (1) ── (*) `submission_attachments` [ON DELETE CASCADE]
- `tests` (1) ── (*) `questions` [ON DELETE CASCADE]
- `tests` (1) ── (*) `test_attempts` [ON DELETE RESTRICT]
- `test_attempts` (1) ── (*) `test_answers` [ON DELETE CASCADE]
- `questions` (1) ── (*) `test_answers` [ON DELETE RESTRICT]

### 2.4 Telemetry, Doubts & Live Classes
- `lectures` (1) ── (*) `video_progress` [ON DELETE CASCADE]
- `lectures` (1) ── (*) `video_watch_sessions` [ON DELETE CASCADE]
- `doubt_threads` (1) ── (*) `doubt_messages` [ON DELETE CASCADE]
- `live_sessions` (1) ── (*) `live_attendance_records` [ON DELETE CASCADE]

### 2.5 Analytics & Auditing
- `users` (1) ── (1) `student_health_summaries` [ON DELETE CASCADE]
- `users` (1) ── (*) `student_activities` [ON DELETE CASCADE]
- `users` (1) ── (*) `notifications` [ON DELETE CASCADE]
- `users` (1) ── (*) `audit_events` [ON DELETE RESTRICT]

---

## 3. Data Integrity & Concurrency Guarantees

1. **Submission Attempt Versioning**:
   - `submissions` records contain `attempt_number` and `is_latest: boolean`.
   - Unique invariant: `(assignment_id, student_id, attempt_number)` guarantees audit trails for resubmissions.
2. **Attendance Integrity**:
   - `live_attendance_records` records `click_through_at` (telemetry evidence) separately from `verified_participation: boolean` (teacher-confirmed attendance).
3. **Double Submission Prevention**:
   - Active test sitting uniqueness is preserved by unique constraint on `(test_id, student_id, attempt_number)`.
