# Master Architectural & Technical Decision Log

This log chronicles all foundational and ongoing architectural, operational, and structural decisions made for the Teacher Learning & Productivity Platform.

---

## Decision Index

| ID | Title | Status | Date | Driving Agent |
| :--- | :--- | :--- | :--- | :--- |
| **ADR-0001** | [Modular Monolith Architecture over Microservices](file:///.okf/decisions/ADR-0001-modular-monolith-architecture.md) | **Accepted** | 2026-10-23 | `@Education_CTO_Agent` |
| **ADR-0002** | [Core Technology Stack (React+Vite, Tailwind, FastAPI, PostgreSQL)](file:///.okf/decisions/ADR-0002-technology-stack-selection.md) | **Accepted** | 2026-10-23 | `@Education_CTO_Agent` |
| **ADR-0003** | [External S3-Compatible Object Storage with Pre-signed URLs for Media](file:///.okf/decisions/ADR-0003-media-storage-and-signed-delivery.md) | **Accepted** | 2026-10-23 | `@Media_Agent` |
| **ADR-0004** | [External Integration with Google Meet for Live Classes](file:///.okf/decisions/ADR-0004-external-live-class-integration.md) | **Accepted** | 2026-10-23 | `@Education_CTO_Agent` |
| **ADR-0005** | [Rule-Based Deterministic Student Health Engine over AI](file:///.okf/decisions/ADR-0005-deterministic-student-health-engine.md) | **Accepted** | 2026-10-23 | `@Analytics_Agent` |
| **ADR-0006** | [Mobile-First PWA Over Native Store Application](file:///.okf/decisions/ADR-0006-mobile-first-pwa-over-native-apps.md) | **Accepted** | 2026-10-23 | `@UX_UI_Agent` |

---

## Detailed Summaries

### ADR-0001: Modular Monolith Architecture
- **Context**: The platform targets an initial cohort of 90–150 students with 1 teacher, with room to scale to 500+.
- **Decision**: Avoid microservices, Kubernetes, and distributed event buses. Adopt a single FastAPI backend structured internally with strict domain boundaries (`auth`, `courses`, `assessments`, `analytics`, `media`, `doubts`).
- **Consequence**: Dramatically reduced hosting costs ($10–$20/mo), simplified local CLI debugging, atomic transactions across domains, and zero network latency between services.

### ADR-0002: Core Technology Stack
- **Context**: Need a responsive, developer-friendly, high-performance ecosystem with rapid time-to-market.
- **Decision**:
  - Frontend: React 18+ with Vite and Tailwind CSS.
  - Backend: Python 3.11+ with FastAPI and Pydantic v2.
  - Database: PostgreSQL 15+ using SQLAlchemy 2.0 (asyncio) and Alembic migrations.
- **Consequence**: Rapid prototyping with strong typing and high execution performance.

### ADR-0003: External Object Storage with Pre-signed Delivery
- **Context**: Video lectures, PDF notes, and homework submission photos consume significant bandwidth and storage.
- **Decision**: No binary files will ever be stored on the application server or in the PostgreSQL database. We will use S3-compatible storage (e.g., Cloudflare R2 or AWS S3) with zero-egress or low-egress fees, using temporary pre-signed URLs (15–30 minute expiration) for media access.
- **Consequence**: Predictable, minimal storage costs, zero bandwidth strain on the API server, and protected video content.

### ADR-0004: External Google Meet Integration for Live Classes
- **Context**: Live doubt-solving and interactive sessions are required, but custom video conferencing (WebRTC/Jitsi) requires heavy DevOps and high server compute.
- **Decision**: Teacher creates scheduled live classes with Google Meet links. Platform provides countdown timer, access control, and presence tracking without hosting video streams.
- **Consequence**: Zero infrastructure video costs, 100% reliable stream quality managed by Google, fast MVP rollout.

### ADR-0005: Deterministic Rule-Based Student Health Engine
- **Context**: The teacher must automatically know who is struggling without manual spreadsheet calculations.
- **Decision**: Compute student health status (`On Track`, `Needs Attention`, `At Risk`) using transparent, explainable rule-based weights (submission rate, video completion %, test score averages).
- **Consequence**: Full transparency for teacher and students; zero AI API billing; immediate diagnostic utility.

### ADR-0006: Mobile-First PWA Strategy
- **Context**: Students primarily learn on mobile devices, but publishing to Apple App Store / Google Play introduces developer fees, review delays, and maintenance overhead.
- **Decision**: Build a responsive web application adhering to Progressive Web App (PWA) standards (service worker, manifest, installable to home screen).
- **Consequence**: Instant zero-friction deployment to students on any device, immediate update propagation, and future option to wrap in a Trusted Web Activity (TWA) if desired.
