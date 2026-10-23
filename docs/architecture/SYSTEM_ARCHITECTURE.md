# System Architecture & Topology Specification

## 1. High-Level System Architecture

The platform follows a clean, decoupled **Client-API-Storage** architecture designed for maximum performance, minimum operational cost, and zero distributed system overhead.

```
                     ┌──────────────────────────────────────┐
                     │          CLIENT APPLICATION          │
                     │  (React 18 + Vite + Tailwind PWA)   │
                     │   - Mobile-First Android Viewports   │
                     │   - Desktop Teacher Command Console  │
                     └──────────────────┬───────────────────┘
                                        │
                         REST JSON APIs │ Pre-Signed Ephemeral
                         (HTTPS Only)   │ Direct Upload & Streaming
                                        ▼
             ┌──────────────────────────────────────────────────────┐
             │            APPLICATION SERVER (Modular Monolith)     │
             │           FastAPI (Python 3.11+) + Uvicorn           │
             │                                                      │
             │  ├── Core Middleware (CORS, Rate Limiter, Auth JWT)  │
             │  ├── Domain: Identity & Roles (Teacher/Student)      │
             │  ├── Domain: Curriculum (Course/Subject/Chapter)     │
             │  ├── Domain: Media Signer (S3 Pre-signed URLs)       │
             │  ├── Domain: Assessments (Submissions, MCQ Engine)   │
             │  ├── Domain: Telemetry (Heartbeat Ingestion)         │
             │  ├── Domain: Analytics (Rule-Based Health Engine)    │
             │  ├── Domain: Doubts (Q&A Threads)                    │
             │  └── Domain: Live Class (Google Meet Scheduler)      │
             └──────────┬────────────────────────────┬──────────────┘
                        │                            │
          SQLAlchemy 2.0│Async Queries               │ S3 API (Boto3)
                        ▼                            ▼
         ┌─────────────────────────────┐   ┌─────────────────────────────┐
         │     POSTGRESQL DATABASE     │   │   CLOUD OBJECT STORAGE      │
         │  (Relational Tables + JSONB │   │ (Cloudflare R2 / AWS S3)    │
         │   B-Tree Indices, Alembic)  │   │ - Video MP4 / HLS Chunks    │
         │  - Identity & Batches       │   │ - Lecture PDF Notes         │
         │  - Curriculum Hierarchy     │   │ - Student Submission Photos │
         │  - Assessments & Grades     │   │ - Zero Egress / Encrypted   │
         │  - Telemetry Rollups        │   └─────────────────────────────┘
         └─────────────────────────────┘
```

---

## 2. Key Architectural Tenets

### 2.1 The Modular Monolith Principle
All backend domains run inside a single Python process and share an async database connection pool. Cross-domain interactions occur via in-memory Python service calls rather than HTTP microservice calls or message queues. This guarantees:
- Sub-millisecond communication between domains.
- Atomicity across database transactions (e.g., student submission + activity record).
- Ultra-low memory footprint (< 150MB RAM).
- Frictionless CLI local development without Docker virtualization.

### 2.2 Decoupled Media Delivery Pipeline
The application server **NEVER** receives, handles, or streams binary video or PDF files.
1. **Teacher Upload**: Frontend requests pre-signed `PUT` URL from `/api/v1/media/upload-url` → Uploads file directly to S3.
2. **Student Watch**: Frontend requests streaming URL from `/api/v1/curriculum/lectures/{id}/stream` → FastAPI validates enrollment and returns 30-minute pre-signed `GET` URL → Video streams directly from S3/CDN.
3. **Student Submission**: Frontend requests upload ticket from `/api/v1/assessments/submissions/upload-url` → Direct upload to private S3 folder → Student posts confirmation with file metadata to FastAPI.

### 2.3 External Live Video Conferencing
Rather than hosting custom WebRTC media servers (which require high CPU servers and complex scaling), live classes use Google Meet. The platform manages the schedule, access permissions, countdown timers, and presence logs, launching Google Meet seamlessly.

---

## 3. Directory Layout Specification

```plaintext
EdtechWeb/
├── backend/
│   ├── alembic/                # DB Migration scripts
│   ├── app/
│   │   ├── core/               # App configuration, security, DB engine
│   │   ├── domains/
│   │   │   ├── identity/       # Users, Auth, Batch enrollment
│   │   │   ├── curriculum/     # Courses, Subjects, Chapters, Lectures
│   │   │   ├── media/          # S3 Pre-signed URL services
│   │   │   ├── assessment/     # Daily Assignments, MCQ Tests, Grading
│   │   │   ├── telemetry/      # Video Heartbeat, Daily Presence
│   │   │   ├── analytics/      # At-Risk Engine, Dashboard Metrics
│   │   │   ├── doubts/         # Q&A Thread Management
│   │   │   └── live/           # Google Meet Scheduling
│   │   └── main.py             # FastAPI entrypoint
│   ├── tests/                  # Pytest test suites & fixtures
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Backend environment variables
├── frontend/
│   ├── public/                 # Static assets, PWA manifest, service worker
│   ├── src/
│   │   ├── components/         # Shared UI components (Button, Modal, Card)
│   │   ├── features/           # Feature views (dashboard, curriculum, assessment)
│   │   ├── hooks/              # Custom React hooks (auth, video player)
│   │   ├── services/           # Axios / Fetch API clients
│   │   ├── App.jsx             # React router & root provider
│   │   ├── main.jsx            # React root mount
│   │   └── index.css           # Tailwind CSS directives
│   ├── package.json            # Node dependencies
│   ├── vite.config.js          # Vite build config
│   ├── tailwind.config.js      # Tailwind design tokens
│   └── .env.example            # Frontend environment variables
```
