# Student Learning Journey & Mobile Experience

## 1. The Student's Daily Study Loop

The student experience is optimized for focused, distraction-free learning on mobile devices:

```
┌────────────────────────────────────────────────────────┐
│ 1. TODAY'S DASHBOARD                                  │
│ - Instant visual summary:                              │
│   • Today's Lecture: Math - Quadratic Equations        │
│   • Pending Assignment: Due at 08:00 PM (Countdown)    │
│   • Upcoming Live Session: 06:00 PM (Google Meet)      │
│   • My Progress: 82% ("On Track" 🟢)                   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 2. LECTURE & NOTES IMMERSION                           │
│ - One-tap video play with resume memory.               │
│ - Speed toggles: 1.25x / 1.5x for fast revision.       │
│ - In-app PDF reader for accompanying formulas & notes. │
│ - Video telemetry passively records watch progress.    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 3. DAILY HOMEWORK SUBMISSION                           │
│ - View problem set assigned by teacher.                │
│ - Solve problems on paper notebook.                    │
│ - Tap "Submit Homework" → camera opens directly.       │
│ - Snap 1-3 photos, review clarity, tap "Upload".       │
│ - Immediate green checkmark: "Submitted On-Time".      │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 4. DOUBT RESOLUTION & LIVE CLASS                       │
│ - If stuck, tap "Ask Doubt" on specific lecture time.  │
│ - Join 06:00 PM Google Meet with single tap.           │
│ - Teacher reviews doubt during live session or in app. │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 5. FEEDBACK & TEST MASTERY                             │
│ - Receive push/in-app alert: "Homework Evaluated: 9/10"│
│ - View teacher comments on calculations.               │
│ - Take Sunday 20-minute timed Chapter MCQ test.        │
│ - Instant score card + solution breakdown.             │
└────────────────────────────────────────────────────────┘
```

---

## 2. Mobile Ergonomics & Offline Considerations

1. **One-Handed Reachability**:
   - Primary action buttons (Submit, Play, Next Question) are located in the bottom 40% of the screen.
2. **Bandwidth Resilience**:
   - If network drops during assignment photo upload, client retries automatically without losing image selection.
   - During timed MCQ tests, answers are cached in `localStorage` so refreshing the browser never loses selected choices.
3. **PWA Standalone Experience**:
   - Student can tap "Add to Home Screen" to install the platform like a native app.
   - Clean, full-screen display without browser address bar clutter.
