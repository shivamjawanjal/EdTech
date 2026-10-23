# Comprehensive System Scope

## 1. Domain Model Hierarchy

The entire curriculum and content architecture adheres strictly to this taxonomy:

```
Course (e.g., "Class 10 STEM & Reasoning Foundation 2026")
  └── Subject (e.g., "Mathematics", "Science", "Reasoning")
        └── Chapter (e.g., "Chapter 4: Quadratic Equations")
              ├── Lecture (e.g., "Lecture 01: Concept of Roots")
              │     ├── Video Asset (Streaming/Signed link)
              │     ├── Lecture Notes (PDF attachment)
              │     ├── Daily Assignment (Problem sheet / task)
              │     └── Practice Question Set (Self-paced drill)
              └── Chapter Milestone Test (Timed mock examination)
```

---

## 2. Functional Domains Matrix

### Domain A: Identity & Access Management (IAM)
- **Teacher Account**: Privileged administrative capabilities, single active teacher tenant initially.
- **Student Accounts**: Managed enrollment, active status toggling, cohort/batch assignment.
- **Session & Security**: Secure HTTP-only JWT/Cookie-based auth, role-based route guards, password reset.

### Domain B: Content & Curriculum Management
- **Course, Subject, Chapter CRUD**: Ordering, publishing states (Draft vs. Published), prerequisites.
- **Lecture Management**: Metadata (title, description, duration), video asset attachment, notes PDF link.
- **Offline & Download Policies**: Controlled download permissions per asset (allow/deny PDF or video download).

### Domain C: Media & File Delivery
- **Object Storage Ingestion**: Direct upload from client or authenticated backend signed upload URL.
- **Secure Retrieval**: Pre-signed URLs with short expiration (e.g., 15–30 minutes) preventing direct leak of permanent S3/R2 links.
- **Asset Types**: Video files (MP4/HLS chunks), PDF lecture notes, student homework submissions (images/PDFs).

### Domain D: Assessments & Homework Engine
- **Daily Assignments**: Created per lecture with explicit submission deadline, instructions, and max marks.
- **Student Submission**: Single/multi-page image or PDF upload from mobile camera or storage.
- **Teacher Evaluation**: Split-screen grading view, score entry, brief audio/text comments, return status.
- **Tests & Quizzes**: Multiple Choice Questions (MCQ) with automated instant scoring, question shuffling, and time limits.

### Domain E: Telemetry, Tracking & Student Activity
- **Video Player Telemetry**: Periodic heartbeat tracking watched intervals, completion %, and re-watch frequency.
- **Submission Timeliness**: On-time vs. late vs. missed assignment status.
- **Activity Log**: Last active timestamp, daily streak count, completed chapters.

### Domain F: Teacher Productivity & Diagnostic Analytics
- **Cohort Overview Dashboard**: Real-time summary: Today's active learners, submissions pending grading, attendance.
- **Student Health Cards**: Automated status categorization:
  - `On Track`: High watch %, timely submissions, test scores above baseline.
  - `Needs Attention`: Falling completion rates, 1–2 missed assignments, inconsistent scores.
  - `At Risk`: Inactive for > 4 days, > 3 consecutive missing assignments, failing test scores.
- **Curriculum Diagnostics**: Aggregate topic difficulty heatmaps (e.g., "70% of students failed question 4 on Physics Chapter 2").

### Domain G: Communication, Doubts & Live Classes
- **Doubt Management**: Student asks doubt linked to specific Lecture timestamp or Assignment question; teacher responds with text/attachment.
- **Live Class Hub**: Schedule Google Meet sessions with batch targeting, automatic countdown, deep-link launcher.
- **Announcements & Notifications**: Batch-wide alerts (new assignment posted, test announced, class rescheduled) with in-app banner and notification center.

---

## 3. Explicit Boundaries & Exclusions (Not in Initial System)

| Feature Category | Inclusion Status | Rationale |
| :--- | :--- | :--- |
| Multi-tenant marketplace / public instructor storefront | **OUT OF SCOPE** | Platform is dedicated to one teacher institute. |
| Custom WebRTC video streaming infrastructure | **OUT OF SCOPE** | High cost, complex DevOps; Google Meet handles live streaming perfectly. |
| In-house Video Encoding Pipeline (AWS MediaConvert/FFmpeg cluster) | **OUT OF SCOPE** | Standard H.264 MP4 pre-compressed files or low-cost CDN/Vimeo/Cloudflare Stream suffice. |
| Native iOS/Android App Store builds | **OUT OF SCOPE** | Progressive Web App (PWA) delivers responsive, installable mobile experience without store fees. |
| E-Commerce & Payment Gateway Processing | **DEFERRED** | Student enrollment and fee handling is handled offline/externally by the teacher in Phase 1. |
| AI Chatbots / Generative Tutoring | **OUT OF SCOPE** | Distracts from foundational teacher-student feedback loops; adds unpredictable API billing. |
