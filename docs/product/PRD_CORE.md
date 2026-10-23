# Product Requirements Document (PRD): Core Platform

- **Project**: Teacher Learning & Productivity Platform (EdtechWeb)
- **Target Audience**: 1 Teacher / Institute, 90–150 Enrolled Students (scaling to 500+)
- **Subjects**: Mathematics, Science (Physics/Chemistry/Biology), Logical & Analytical Reasoning
- **Author**: `@Product_Agent`
- **Approved by**: `@Education_CTO_Agent`

---

## 1. Problem Statement & Strategic Objective

### 1.1 The Operational Bottleneck
An independent educator running a high-performing coaching practice with 90–150 students is overwhelmed by operational friction:
- Homework submitted across disparate WhatsApp threads without structured indexing.
- Manual cross-referencing on paper rolls or spreadsheets to check who watched a recorded lecture, who submitted homework, or who failed recent tests.
- High risk of losing track of disengaged students until they fail end-of-term exams.
- Proprietary video lessons and notes shared as unmonitored links with zero telemetry or access revocation.

### 1.2 Core Objective
To deploy a closed, private digital learning platform centered on the pedagogical feedback loop:
$$\text{TEACH} \longrightarrow \text{ASSIGN} \longrightarrow \text{TRACK} \longrightarrow \text{EVALUATE} \longrightarrow \text{IDENTIFY WEAK STUDENTS} \longrightarrow \text{IMPROVE}$$

The platform must radically streamline teacher productivity while offering students a focused, distraction-free study portal on mobile devices.

---

## 2. Core Personas

### Persona 1: The Teacher / Institute Owner
- **Goals**: Create courses, organize chapters, post video lectures with PDF notes, set daily homework, grade 90 submissions in under 30 minutes, schedule live Google Meet classes, and instantly view which students are `At Risk`.
- **Pain Points**: Time-poor, hates complex software with steep learning curves, needs quick overview of daily student compliance without spreadsheet work.

### Persona 2: The Student (Grades 8–12 / Foundation Aspirants)
- **Goals**: View today's schedule, watch lecture videos at adjustable playback speeds (1x–2x), download/read chapter notes, snap photos of handwritten math homework and upload in seconds, take timed MCQ mock tests, ask doubts, and join live sessions with one tap.
- **Pain Points**: Variable mobile phone specs, patchy mobile data connectivity, easily distracted by social media feeds, needs instant feedback on whether homework was received.

---

## 3. Curriculum & Content Hierarchy

```
Course (e.g., "10th Foundation STEM 2026")
  └── Subject (e.g., "Mathematics")
        └── Chapter (e.g., "Real Numbers & Polynomials")
              ├── Lecture 1: "Introduction & Euclid's Lemma"
              │     ├── Video (Pre-signed streaming)
              │     ├── PDF Notes (Downloadable or view-only)
              │     └── Daily Assignment (Submission deadline + upload zone)
              ├── Lecture 2: "Fundamental Theorem of Arithmetic"
              │     ├── Video + Notes + Daily Assignment
              └── Chapter Milestone Test (Timed 20-question MCQ test)
```

---

## 4. Functional Requirements Matrix (MVP)

### 4.1 Authentication & Cohort Management
- **FR-AUTH-1**: Secure email/phone and password authentication with HTTP-only session cookies.
- **FR-AUTH-2**: Role separation: `Teacher` (admin) vs `Student` (enrolled learner).
- **FR-AUTH-3**: Teacher can create student accounts, assign them to batches, reset passwords, or deactivate accounts.

### 4.2 Content & Curriculum Delivery
- **FR-CONT-1**: Teacher can create, edit, reorder, and publish Courses, Subjects, Chapters, and Lectures.
- **FR-CONT-2**: Teacher can upload lecture videos (stored directly in S3/R2 object storage) and attach PDF notes.
- **FR-CONT-3**: Controlled download permission toggle per asset (`allow_download: boolean`).
- **FR-CONT-4**: Responsive HTML5 video player with speed controls (0.75x, 1x, 1.25x, 1.5x, 2x), resume playback, and full-screen mobile support.

### 4.3 Daily Homework & Rapid Grading
- **FR-ASSG-1**: Teacher can attach a Daily Assignment to any Lecture with a title, description, max marks, and submission deadline.
- **FR-ASSG-2**: Student can submit assignment solutions via mobile camera photo capture or PDF upload.
- **FR-ASSG-3**: System automatically stamps submission status: `On-Time`, `Late`, or `Missing`.
- **FR-ASSG-4**: Teacher Rapid Grading Console: Side-by-side view showing student homework photos, score input, quick feedback remarks, and single-click advance to next student.
- **FR-ASSG-5**: Resubmission workflow: Teacher can request revision with a note (e.g., *"Page 2 is blurry, please re-upload"*).

### 4.4 Objective Mock Tests & Instant Scoring
- **FR-TEST-1**: Teacher can create timed MCQ tests attached to chapters with question text, options (A, B, C, D), correct answer key, marks, and solution explanation.
- **FR-TEST-2**: Student test runner: Fullscreen countdown timer, question navigator, radio button selection, and submit confirmation modal.
- **FR-TEST-3**: Automated instant grading immediately upon submission with score summary and solution review (unlocked after test close).

### 4.5 Automated Telemetry & Teacher Analytics
- **FR-ANLY-1**: Client emits video heartbeat ping every 10 seconds of active playback.
- **FR-ANLY-2**: Lecture marked "Watched" once student reaches ≥ 85% total duration.
- **FR-ANLY-3**: Teacher "Today's Compliance" widget:
  - Who watched today's lecture (Watched vs. Unwatched).
  - Who submitted today's homework (Submitted vs. Missing).
- **FR-ANLY-4**: Rule-based Student Health status:
  - 🟢 `On Track`
  - 🟡 `Needs Attention`
  - 🔴 `At Risk` (Inactive > 4 days, > 3 consecutive missing homeworks, or test score average < 40%).
- **FR-ANLY-5**: Chapter difficulty diagnostic: Highlights chapters where average test score is below 50%.

### 4.6 Doubts & Live Classes
- **FR-DBT-1**: Student can ask doubts linked to a specific lecture or assignment. Teacher replies with text and optional attachment.
- **FR-LIVE-1**: Teacher can schedule Google Meet sessions with batch targeting; students see live countdown and authenticated "Join Live Class" button.

---

## 5. Non-Functional Requirements (NFRs)

- **Performance**: PWA initial load time `< 1.8 seconds` on 4G cellular connections; API response time `< 200ms` for 95th percentile.
- **Scalability**: Zero performance degradation for 150 concurrent active students.
- **Cost**: Total infrastructure hosting + DB + storage `< $25/month`.
- **Reliability**: 99.9% uptime for study portal and video streaming.
