# Project Context

## 1. Background & Target Audience

### 1.1 The Educator Persona
- **Role**: Private educator running a specialized coaching/tutoring practice.
- **Subjects Taught**:
  - **Mathematics** (conceptual foundations, formulas, step-by-step problem solving).
  - **Science** (Physics, Chemistry, Biology: concept explanation, visual experiments, diagrams).
  - **Reasoning** (Logical, verbal, non-verbal analytical problem solving).
- **Current Student Base**: ~90 enrolled students.
- **Initial Scaling Target**: 150 students across multiple grades/batches.
- **Future Potential**: Growth to 500+ students within the same single-teacher / boutique institute setup.

### 1.2 Current Operational Friction
Before this platform, the educator relied on fragmented, manual channels:
1. **Spreadsheets**: Tracking attendance, fee statuses, and homework submissions manually across 90 students leads to cognitive fatigue and data blindness.
2. **Messaging Apps (WhatsApp/Telegram)**: Homework submissions arrive as unorganized phone photos; questions and doubts get buried in chat feeds; announcements are missed.
3. **Unprotected File Links (Google Drive/YouTube unlisted)**: Videos and proprietary PDF notes are circulated openly without viewing telemetry or access revocation.
4. **Zero Diagnostic Insights**: The teacher cannot easily identify which students didn't watch a lecture before class, which students are falling behind in quadratic equations, or who has stopped submitting assignments for 3 consecutive days.

---

## 2. Core Educational Philosophy & Workflow Loop

```
┌─────────────────────────────────────────────────────────────┐
│                           TEACH                             │
│   (Recorded Video Lectures, Live Problem-Solving sessions)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                          ASSIGN                             │
│  (Daily Problem Sets, Curated PDF Notes, Timed Mock Tests)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                          TRACK                              │
│   (Telemetry on Video Watch %, Submission Deadlines, Tests) │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                         EVALUATE                            │
│    (Auto-grading for MCQs, Fast Teacher Rubric for Written) │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 IDENTIFY WEAK STUDENTS                      │
│ (Rule-based: "At Risk" alerts, repeated non-submissions)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                         IMPROVE                             │
│  (Targeted doubt clarification, revision nudges, feedback)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Structural Constraints & Boundaries

1. **Private Institute Ecosystem, NOT an Open Marketplace**:
   - No public discovery or self-signup directory.
   - Enrollment is controlled directly by the teacher/admin (or invitation code).
   - Multi-tenancy is deferred; this instance is optimized for a single teacher institute.

2. **Ultra-Low Operating Expense (OpEx)**:
   - For 150 students, high fixed server costs ($100+/mo) or expensive SaaS seats are prohibitive.
   - Cost must scale proportionally with actual bandwidth and storage usage (S3-compatible storage, Cloudflare CDN/R2, modest VPS/PaaS compute).

3. **Pragmatic Technology Choices**:
   - Zero microservice overhead.
   - Single modular FastAPI backend + PostgreSQL.
   - External Google Meet for live video, saving thousands in WebRTC server maintenance.
   - Native-feeling Responsive Web / PWA to avoid immediate Apple App Store / Google Play review overhead.

4. **Security & Content Integrity**:
   - Video streaming URLs and PDF downloads must be protected with short-lived signed tokens.
   - Student test responses and grades must be strictly isolated to the respective student and the teacher.
