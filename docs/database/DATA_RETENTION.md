# Data Retention, Archival & Purge Policies

- **Lead Author**: `@Security_Agent` & `@Database_Agent`
- **Approving Authority**: `@Education_CTO_Agent`
- **Status**: Ratified Policy Document

---

## 1. Data Classification & Lifecycle Overview

The platform partitions data into three lifecycles:
1. **Permanent Academic Records**: Courses, lectures, notes, evaluated student submissions, test scores, certificates.
2. **Operational State & Diagnostics**: Student health snapshots, doubt threads, live class schedules, in-app notifications.
3. **High-Frequency Ephemeral Telemetry**: Raw video heartbeat sessions, raw access logs, expired refresh tokens.

```
┌─────────────────────────────────┬────────────────────┬─────────────────────────────┐
│ Category                        │ Minimum Retention  │ Purge / Archival Action     │
├─────────────────────────────────┼────────────────────┼─────────────────────────────┤
│ User Identities & Profiles      │ Duration of Enrol  │ Soft-delete on exit         │
│ Curriculum (Courses, Lectures)  │ Indefinite         │ Soft-delete / Unpublish     │
│ Submissions & Test Attempts     │ 3 Academic Years   │ Archive to Cold S3 Glacier  │
│ Video Progress (Cumulative)     │ 1 Academic Year    │ Retain summary rollups      │
│ Video Watch Sessions (Raw Logs) │ 90 Days            │ Rolling automated purge     │
│ In-App Notifications            │ 60 Days            │ Auto-delete read notices    │
│ Expired Refresh Tokens          │ 30 Days past exp.  │ Daily cleanup job           │
│ Audit Events (Security Logs)    │ 2 Calendar Years   │ Immutable audit retention   │
└─────────────────────────────────┴────────────────────┴─────────────────────────────┘
```

---

## 2. Telemetry Ingestion vs. Ephemeral Purge Policy

1. **Cumulative Progress vs Raw Sessions**:
   - `video_progress` stores the **authoritative cumulative watch state** (`seconds_watched`, `completion_percentage`, `is_completed`). This table is permanent throughout the academic year.
   - `video_watch_sessions` captures the **granular 10-second playback chunks** used to audit suspicious watch jumps.
   - **Purge Rule**: Raw rows in `video_watch_sessions` older than **90 days** are automatically pruned via a scheduled background cleanup job:
     ```sql
     DELETE FROM video_watch_sessions 
     WHERE recorded_at < NOW() - INTERVAL '90 days';
     ```

---

## 3. Student Account Deactivation & Archival

1. **Academic Integrity Protection**:
   - When a student leaves or finishes an academic year, their account is marked `is_active = FALSE`.
   - The user record and their historical submissions/test scores are **NEVER hard-deleted** via automated cascades during ordinary operations.
   - This ensures historical cohort performance statistics and teacher evaluation records remain mathematically accurate.

2. **Submission Media Archival**:
   - S3 homework photos for completed academic batches can be moved to cheaper storage tiers (e.g. Cloudflare R2 infrequent access or AWS S3 Glacier Flexible Retrieval) after 180 days, reducing storage costs to less than $0.004/GB/month.

---

## 4. Security Audit Log Retention

1. **Immutability of `audit_events`**:
   - `audit_events` rows are strictly append-only.
   - No `UPDATE` or `DELETE` API endpoints or application-level queries exist for `audit_events`.
   - Database user permissions configured for production prevent row modification on `audit_events`.
   - Minimum retention: 2 full academic years to resolve any grade dispute or administrative investigation.
