# Teacher Operational Workflow & Productivity Optimization

## 1. The Teacher's Daily Operational Cycle

The platform is designed around the teacher's exact daily timeline, minimizing manual touches at each phase:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 08:00 AM - MORNING SETUP (5-10 minutes)                                │
│ - Publish today's recorded lecture video + PDF notes.                  │
│ - Set today's daily assignment & submission deadline (e.g., 08:00 PM). │
│ - (Optional) Schedule evening Google Meet live problem-solving class.  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 02:00 PM - MIDDAY PULSE CHECK (2 minutes)                              │
│ - Glance at "Today's Pulse" widget:                                    │
│   • 62 / 90 students have watched the lecture.                         │
│   • 28 have not started.                                               │
│ - Filter to unviewed list; trigger single-click batch alert.           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 06:00 PM - LIVE CLASS / DOUBTS (45-60 minutes)                         │
│ - Review pending doubts submitted on today's lecture.                  │
│ - Launch Google Meet session directly from dashboard.                  │
│ - Address common questions identified in the doubt queue.              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 08:30 PM - EVENING RAPID-GRADING (20-25 minutes for 90 students)       │
│ - Open Rapid Grading Console.                                          │
│ - Split-screen: Student homework image preview on left, grading rubric │
│   and score input on right.                                            │
│ - Fast keyboard shortcuts: type score, press Enter to submit & advance │
│   to next student automatically.                                       │
│ - Total time: ~15 seconds per student.                                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 09:00 PM - DIAGNOSTIC & AT-RISK REVIEW (5 minutes)                     │
│ - Check "At-Risk Alert" drawer:                                        │
│   • 3 students have missed 3 consecutive assignments.                  │
│   • 2 students have dropped below 40% test score threshold.            │
│ - Send personalized WhatsApp nudge or note to parents/students.        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Quantitative Productivity Improvements

| Task | Legacy Spreadsheet / Chat Method | Platform Automated Method | Efficiency Gain |
| :--- | :--- | :--- | :--- |
| **Publishing Lecture & Notes** | Upload to Drive + copy link + compose WhatsApp message (~15 min) | Upload file once, click "Publish" (~2 min) | **7.5x faster** |
| **Tracking Lecture Attendance** | Impossible; zero viewing telemetry | Real-time automated "Watched / Not Watched" list | **100% automated** |
| **Collecting Homework** | 90 individual photo messages in WhatsApp; messy gallery | Unified assignment submission queue | **Zero lost submissions** |
| **Grading 90 Submissions** | Download photo, open photo editor, reply to chat: ~2.5 hours | Rapid-grading console with keyboard navigation: ~25 mins | **6x faster** |
| **Identifying Failing Students** | Manual calculation at end of month or after term failure | Instant rule-based `At Risk` badge within 48 hours | **Proactive intervention** |
| **Live Class Coordination** | Generating Meet link, pasting in group, handling lost links | Dedicated "Live Now" banner with countdown launcher | **Frictionless** |

---

## 3. The Rapid Grading Console UI Specification

The Rapid Grading Console is the teacher's highest-frequency evaluation surface:
- **Left Panel (70% width)**: High-resolution zoomable viewer for student photo/PDF submissions. Includes rotate, brightness toggle, and pan controls for mobile camera uploads.
- **Right Panel (30% width)**:
  - Student identity, avatar, and submission timestamp (`On-Time` vs `Late (+2h)`).
  - Quick Score Input (`[  ] / 10 marks`).
  - Pre-defined one-click feedback chips (*"Well done"*, *"Check step 3 calculation"*, *"Handwriting unclear"*, *"Complete all questions"*).
  - Optional custom text feedback field.
  - Action Buttons: `Save & Next (Enter)` and `Request Resubmission (R)`.
