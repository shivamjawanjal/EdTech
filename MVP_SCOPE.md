# MVP Scope: 150-Student Private Deployment

## 1. MVP Purpose & Guiding Directive

The Phase 1 MVP is designed to solve one core problem: **Allow 1 teacher to manage, teach, assign, track, and evaluate 90–150 students across Mathematics, Science, and Reasoning without relying on spreadsheets or unstructured chat apps.**

Every proposed feature for MVP is measured by this test:
> *Does this eliminate manual teacher tracking, or directly improve student submission & study habits?*

---

## 2. Included in MVP (Phase 1 Manifest)

### 2.1 Authentication & Profile
- [x] Secure JWT authentication (Teacher vs. Student role-based access control).
- [x] Student profile overview (enrolled batch, overall completion stats).
- [x] Teacher student management (create student, toggle active/inactive, reset password, batch assign).

### 2.2 Learning Hierarchy & Content Delivery
- [x] Course → Subject (`Math`, `Science`, `Reasoning`) → Chapter → Lecture navigation tree.
- [x] Teacher content management: Create chapters, create lectures, attach video metadata, attach PDF notes.
- [x] HTML5 Video Player with playback rate controls (1x, 1.25x, 1.5x, 2x), resume playback position, and full-screen support.
- [x] Pre-signed secure video streaming URLs (S3/Cloudflare R2 compatible).
- [x] PDF Notes viewer & controlled download (configurable toggle per file).

### 2.3 Assignments & Evaluation
- [x] Teacher creates Daily Assignment attached to a Lecture (Title, instructions, deadline, max marks, optional question PDF).
- [x] Student Assignment Submission: File upload (photo/PDF from mobile phone camera or file picker) with status indicator (`Submitted`, `Late`, `Pending`).
- [x] Teacher Grading Console: Rapid-review modal displaying student submission preview, marks entry, brief written feedback, and "Mark as Evaluated" button.
- [x] Student Assignment Feedback View: Score display, teacher commentary, and resubmission request if marked deficient.

### 2.4 Objective Tests & Instant Scoring
- [x] Teacher creates Chapter Test: Timed MCQ quiz (Question text, options A/B/C/D, correct answer key, marks per question).
- [x] Student Test Taking: Countdown timer, question pagination, answer selection, submission confirmation.
- [x] Automated instant grading for MCQ tests with score report, breakdown of correct vs. incorrect answers, and solution explanations.

### 2.5 Automated Telemetry & Tracking Engine
- [x] Video Watch Tracking: Client-side heartbeat reports current timestamp every 10 seconds; calculates total watch % and sets "Watched" milestone when ≥ 85% completed.
- [x] Daily Activity Tracker: Records student login, lecture visits, and assignment submissions.

### 2.6 Teacher Productivity & Diagnostic Analytics
- [x] **Today's Operational Dashboard**:
  - Who watched today's newly posted lecture (Watched vs. Not Watched list).
  - Who submitted today's assignment (Submitted vs. Missing list).
  - Submissions waiting for evaluation queue.
- [x] **Student Health Triage** (Rule-based classification):
  - 🟢 `On Track`: Assignment submission rate ≥ 80%, watch rate ≥ 75%, test average ≥ 60%.
  - 🟡 `Needs Attention`: Assignment submission rate 60–79%, or 1–2 missed assignments in last 7 days.
  - 🔴 `At Risk`: Inactive for > 4 days, > 3 consecutive missing assignments, or test score average < 40%.
- [x] **Chapter & Topic Diagnostic**: Identifies chapters with lowest average test scores or lowest assignment completion.

### 2.7 Doubts & Live Classes
- [x] Simple Doubt Submission: Student raises doubt tagged to a specific Lecture or Assignment; teacher replies via threaded response.
- [x] Google Meet Live Class Scheduler: Teacher sets date, time, subject, topic, and Google Meet URL; student sees countdown and "Join Class" button.

### 2.8 In-App Notifications
- [x] Notification feed for students: New lecture posted, assignment deadline approaching (24h/2h reminders), test results published.
- [x] Notification feed for teacher: Daily summary of pending evaluations, high-priority student doubts.

---

## 3. Explicitly Deferred / Post-MVP (Do NOT Build in Phase 1)

| Feature | Deferral Justification | Target Phase |
| :--- | :--- | :--- |
| **AI Tutor / AI Answers** | High operational cost, risk of hallucinations; direct teacher feedback is priority. | Phase 3 |
| **AI Lesson Generation** | Teacher already possesses specialized curriculum notes and video lessons. | Phase 3 |
| **E-Commerce & Online Payments** | Offline fee collection works smoothly for 90–150 local students; avoids payment gateway compliance overhead. | Phase 2 |
| **Custom WebRTC Video Streaming** | High infrastructure complexity and server costs; Google Meet is free and proven. | Deferred |
| **Mobile Native Stores (iOS/Android App)** | Requires Apple Developer ($99/yr) + Google Play fees and ongoing multi-platform build maintenance. PWA provides immediate mobile app experience. | Phase 2 |
| **Multi-Teacher / Multi-Institute Marketplace** | Architecture would unnecessarily double complexity; single-tenant modular design meets all current requirements. | Future |
| **Gamification, Badges & Leaderboards** | Can create unhealthy competition or distraction; progress mastery bars are sufficient for STEM foundation. | Phase 2 |
| **Public Discussion Forum / Social Feed** | Requires heavy moderation; 1-on-1 doubt clearing maintains pedagogical safety. | Future |
| **Hardware DRM / Encrypted Media Streams (Widevine)** | Excessive licensing cost; pre-signed ephemeral URLs + dynamic watermarking are cost-effective first defenses. | Phase 2 |

---

## 4. MVP Launch Criteria (Definition of Ready for 150 Students)

1. **Teacher Test**: The teacher can post 1 week's worth of Math, Science, and Reasoning curriculum and evaluate 30 test submissions in under 30 minutes total.
2. **Student Mobile UX Test**: A student on a low-end Android mobile browser can open the PWA, watch a 25-minute video without buffering stalls, upload a 2-page homework photo, and complete a 10-question MCQ test.
3. **Data Integrity**: Zero missing submissions, zero spreadsheet exports required for daily operational awareness.
4. **Hosting Budget**: Complete backend + DB + S3 storage running within budget ($10–$25/month for the initial cohort).
