# Engineering Project Structure & Module Boundaries

## 1. Top-Level Directory Layout

```plaintext
EdtechWeb/
├── .okf/                       # Multi-agent governance and decision framework
├── docs/                       # Technical and domain documentation
├── backend/                    # Python FastAPI application
├── frontend/                   # React + Vite + Tailwind CSS application
├── scripts/                    # Development, database seeding, and diagnostic scripts
├── README.md                   # Project overview
└── DECISION_LOG.md             # Master decision log
```

---

## 2. Backend Module Structure (`backend/app/`)

The backend is organized into explicit domain modules within a modular monolith:

```plaintext
backend/app/
├── core/
│   ├── config.py               # Pydantic Settings loaded from .env
│   ├── database.py             # Async SQLAlchemy engine & session factory
│   ├── security.py             # Password hashing (bcrypt) and JWT encode/decode
│   ├── exceptions.py           # Custom domain exception classes
│   └── middleware.py           # CORS, Request timing, Rate limiters
├── domains/
│   ├── identity/               # Domain: IAM & Roles
│   │   ├── models.py           # User, Role, Batch, Enrollment models
│   │   ├── schemas.py          # Pydantic login, user create, token response
│   │   ├── service.py          # Auth logic, password verification
│   │   └── router.py           # /api/v1/auth & /api/v1/students routes
│   ├── curriculum/             # Domain: Courses, Subjects, Chapters, Lectures
│   │   ├── models.py           # Course, Subject, Chapter, Lecture, Note models
│   │   ├── schemas.py          # Pydantic payload models
│   │   ├── service.py          # Hierarchy queries and CRUD
│   │   └── router.py           # /api/v1/curriculum routes
│   ├── media/                  # Domain: S3 Storage & Pre-signed URL Signing
│   │   ├── s3_client.py        # Boto3 client wrapper
│   │   ├── service.py          # Pre-signed GET/PUT URL generator
│   │   └── router.py           # /api/v1/media routes
│   ├── assessment/             # Domain: Homework & Timed MCQ Tests
│   │   ├── models.py           # Assignment, Submission, Test, Question, Attempt
│   │   ├── schemas.py          # Submission schemas, Test taker schemas
│   │   ├── service.py          # Rapid grading rubric logic, MCQ evaluator
│   │   └── router.py           # /api/v1/assessments routes
│   ├── telemetry/              # Domain: Video Heartbeats & Presence
│   │   ├── models.py           # VideoHeartbeat, DailyStudentPresence
│   │   ├── service.py          # Heartbeat buffer, watch % aggregator
│   │   └── router.py           # /api/v1/telemetry routes
│   ├── analytics/              # Domain: Health Triage & Teacher Dashboard
│   │   ├── engine.py           # Rule-based calculation (On Track, Needs Attention, At Risk)
│   │   ├── service.py          # Aggregated dashboard metrics queries
│   │   └── router.py           # /api/v1/analytics routes
│   ├── doubts/                 # Domain: Inbound Q&A Threads
│   │   ├── models.py           # DoubtThread, DoubtMessage
│   │   └── router.py           # /api/v1/doubts routes
│   └── live/                   # Domain: Google Meet Session Scheduler
│       ├── models.py           # LiveSession
│       └── router.py           # /api/v1/live routes
├── main.py                     # Root FastAPI application mounting domain routers
└── tests/                      # Automated test suite mirroring domains
```

---

## 3. Frontend Architecture Layout (`frontend/src/`)

```plaintext
frontend/src/
├── assets/                     # SVG icons, logo assets
├── components/
│   ├── ui/                     # Generic atomic UI (Button, Modal, Card, Badge, Input)
│   ├── layout/                 # Navbar, MobileBottomBar, TeacherSidebar
│   └── feedback/               # Toast notifications, Loading spinners, Empty states
├── features/
│   ├── auth/                   # Login screen, password reset, auth state
│   ├── dashboard/              # Student dashboard & Teacher overview console
│   ├── curriculum/             # Subject list, Chapter explorer, Lecture study view
│   ├── video/                  # Custom HTML5 video player with heartbeat emitter
│   ├── assessment/             # Assignment submit modal, Rapid grading console, MCQ runner
│   ├── analytics/              # Student health status badges, weak-topic cards
│   ├── doubts/                 # Q&A thread list, ask doubt modal
│   └── live/                   # Google Meet countdown banner and join launcher
├── hooks/
│   ├── useAuth.js              # Current user context and permissions
│   ├── useVideoProgress.js     # Heartbeat telemetry hook
│   └── useMediaQuery.js        # Responsive viewport detection
├── services/
│   ├── api.js                  # Axios/Fetch client configured with base URL & cookies
│   └── storage.js              # Direct S3 upload client
├── App.jsx                     # Route definitions & React Query / Context providers
└── main.jsx                    # Root ReactDOM render
```
