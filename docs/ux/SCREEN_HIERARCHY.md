# Screen Map & User Experience Hierarchy

## 1. Student Experience Screen Map (Mobile-First)

```
Student Portal
├── /login                            # Simple phone/email login with remember me
├── /app/dashboard                    # Student Command Center
│   ├── "Today's Task" Card           # New lecture + daily assignment countdown
│   ├── "Live Class Now" Banner       # Appears 15 min prior to Google Meet
│   ├── Quick Subject Switcher        # Math | Science | Reasoning tabs
│   └── Weekly Activity Progress Bar  # % Completed & streak counter
├── /app/courses/:courseId            # Course Curriculum Explorer
│   └── /subjects/:subjectId
│       └── /chapters/:chapterId      # Chapter Lecture List + Milestone Test
├── /app/lectures/:lectureId          # Immersive Study Screen
│   ├── Responsive Video Player       # HTML5 player with speed controls
│   ├── Notes / PDF Tab               # Inline preview & download toggle
│   ├── Daily Assignment Tab          # Problem sheet & submission status
│   └── Doubts / Q&A Tab              # Submit timestamped doubt & read replies
├── /app/assignments/:id/submit       # Assignment Camera / Photo Upload Modal
├── /app/tests/:testId                # Timed MCQ Test Runner (Distraction-free)
│   └── /app/tests/:testId/results    # Scorecard & Solution Explanations
└── /app/profile                      # Student profile, attendance, submissions history
```

---

## 2. Teacher Command Console Screen Map (Desktop / Tablet Optimized)

```
Teacher Console
├── /teacher/login                    # Teacher credentials login
├── /teacher/dashboard                # Operational Headquarters
│   ├── Real-Time Compliance Counters # Watched Today (X/90), Submitted HW (Y/90)
│   ├── "At Risk" Triage Carousel     # Flagged students needing immediate attention
│   ├── Pending Evaluations Queue     # Homework submissions waiting for grading
│   └── Today's Schedule              # Post lecture / Schedule Google Meet
├── /teacher/curriculum               # Course, Subject, Chapter & Lecture CRUD
│   ├── /curriculum/new-lecture       # Video upload (S3 pre-signed) + PDF attach
│   └── /curriculum/new-assignment    # Set homework deadline, instructions, marks
├── /teacher/grading                  # Rapid Evaluation Console
│   └── /grading/:assignmentId        # Split-screen photo viewer + score input + next
├── /teacher/tests                    # MCQ Test Creator & Question Bank
│   ├── /tests/create                 # Add questions, options, answer key, timer
│   └── /tests/:id/analytics          # Item analysis & score distribution
├── /teacher/students                 # Student Roster & Cohort Management
│   ├── /students/add-student         # Enrolment modal (name, phone, batch)
│   └── /students/:studentId          # Individual 360-degree Student Health Card
└── /teacher/doubts                   # Inbound Student Doubt Thread Manager
```

---

## 3. Visual Layout Guidelines for Critical Screens

### Student Lecture Screen Layout (Mobile)
```
┌──────────────────────────────────────┐
│ [← Math Chapter 4]           (9:41)  │
├──────────────────────────────────────┤
│ ┌──────────────────────────────────┐ │
│ │                                  │ │
│ │       VIDEO PLAYER (16:9)        │ │
│ │                                  │ │
│ └──────────────────────────────────┘ │
│ Lecture 02: Quadratic Formula (24m)  │
│                                      │
│ [ Notes ]  [ Assignment ]  [ Doubts ]│
│ ──────────────────────────────────── │
│ 📄 Chapter_04_Formula_Sheet.pdf      │
│ [ View PDF ]  [ Download PDF ↓ ]     │
│                                      │
│ 📝 Today's Assignment: Due 8:00 PM   │
│ Status: PENDING                      │
│ [ 📷 Open Camera to Submit Homework ]│
└──────────────────────────────────────┘
```

### Teacher Rapid Grading Console Layout (Desktop)
```
┌────────────────────────────────────────────────────────────────────────┐
│ [← Back to Queue]   HW 04: Real Numbers   Student: 14 of 88 (Rahul S.) │
├──────────────────────────────────────────┬─────────────────────────────┤
│ ┌──────────────────────────────────────┐ │ Student: Rahul Sharma       │
│ │                                      │ │ Status: Submitted On-Time   │
│ │      STUDENT SUBMISSION IMAGE        │ │ Submitted: Today, 04:15 PM  │
│ │       (Pinch / Zoom / Rotate)        │ ├─────────────────────────────┤
│ │                                      │ │ Score: [ 9 ] / 10 marks     │
│ │                                      │ ├─────────────────────────────┤
│ │                                      │ │ Quick Feedback:             │
│ │                                      │ │ [Well Done] [Check Step 3]  │
│ │                                      │ │ Remarks:                    │
│ │                                      │ │ Good step layout in Q2.     │
│ └──────────────────────────────────────┘ ├─────────────────────────────┤
│ Page 1 of 2  [ Prev ] [ Next ]           │ [ 💾 Save & Next (Enter) ]  │
│                                          │ [ 🔄 Request Resubmit ]     │
└──────────────────────────────────────────┴─────────────────────────────┘
```
