# Strategic Product Roadmap

```
┌──────────────────────────┐    ┌──────────────────────────┐    ┌──────────────────────────┐
│         PHASE 1          │    │         PHASE 2          │    │         PHASE 3          │
│        MVP CORE          │───▶│     SCALE & MOBILE       │───▶│   INTELLIGENT INSIGHTS   │
│   (150 Students Cohort)  │    │  (300–500 Students + PWA)│    │   (500+ Students + AI)   │
└──────────────────────────┘    └──────────────────────────┘    └──────────────────────────┘
```

---

## Phase 1: MVP Core (Foundational Operational Mastery)
**Target Horizon**: Weeks 1 – 6  
**Primary Focus**: Replace all spreadsheets, WhatsApp submission threads, and unsecured links with a functional private learning portal.

- **Milestone 1.1**: Governance, architecture specifications, relational DB schema, and UI design tokens.
- **Milestone 1.2**: Identity & Authentication (Teacher & Student RBAC) + Student Batch Management.
- **Milestone 1.3**: Curriculum Hierarchy (`Course → Subject → Chapter → Lecture`) with S3 pre-signed video & PDF delivery.
- **Milestone 1.4**: Daily Assignment submission (photo/PDF) & Teacher Rapid-Grading Console.
- **Milestone 1.5**: Chapter Timed MCQ Tests with automated scoring and student answer key review.
- **Milestone 1.6**: Video telemetry heartbeat & Automated Student Health triage (`On Track`, `Needs Attention`, `At Risk`).
- **Milestone 1.7**: Doubts submission, Google Meet schedule launcher, and in-app alerts.
- **Milestone 1.8**: Comprehensive End-to-End verification with mock 150-student data fixtures.

---

## Phase 2: Scale, Mobile & Enhanced Automation
**Target Horizon**: Months 2 – 4  
**Primary Focus**: Deepen mobile engagement, introduce automated reminders, and reduce teacher assessment time further.

- **PWA Enhancements**: Push notifications for assignments due and class start alerts (Web Push API).
- **Automated Communication**: WhatsApp/SMS webhook notifications (via low-cost API) for students flagged `At Risk` or missing assignments 2 days in a row.
- **Android TWA (Trusted Web Activity) / Capacitor Wrapper**: One-click installable APK for Android students without rewriting frontend code.
- **Dynamic Watermarking on Video & Notes**: Embed student ID/phone number subtly over video frames and PDF footer to deter unauthorized leak.
- **Fee Status Tracking**: Basic manual ledger for tracking monthly tuition payments without payment gateway fees.
- **Teacher Audio Notes**: Allow teacher to record 15-second voice memos directly on homework grading.

---

## Phase 3: Intelligent Diagnostics & Pedagogical Expansion
**Target Horizon**: Months 5 – 8  
**Primary Focus**: Intelligent remedial pathways, multi-batch scheduling, and AI-assisted teacher productivity.

- **Remedial Recommendations**: Rule engine automatically assigns specific foundational practice sets when a student fails a chapter test.
- **AI-Assisted Doubt Triaging**: Pre-index past answered teacher doubts; suggest previous teacher answers to matching questions before escalating.
- **Detailed Question Item Analysis**: Psychometric analysis on test questions (difficulty index, discrimination index) to improve test quality.
- **Assistant Teacher Role**: Sub-admin credentials for teaching assistants (TAs) to grade assignments under teacher supervision.
