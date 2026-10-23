# ADR-0002: Core Technology Stack Selection

- **Status**: Accepted
- **Date**: 2026-10-23
- **Proposing Agent**: `@Education_CTO_Agent`
- **Approving Authority**: `@Education_CTO_Agent`
- **Consulted Agents**: `@Frontend_Agent`, `@Backend_Agent`, `@Database_Agent`

---

## 1. Context & Problem Statement
We need a robust, high-performance, developer-friendly technology foundation for a responsive web application and API serving 150 students and 1 teacher. The stack must support rapid CLI development, type safety, low server resource consumption, and frictionless UI prototyping.

## 2. Decision Drivers (5-Point Check)
1. **Problem Solved**: Provides cohesive modern foundations for frontend UX and backend data integrity.
2. **Who it impacts**: Engineering velocity and student mobile experience.
3. **Usage Frequency**: Entire application lifecycle.
4. **Pedagogical Impact**: Fast page loads, zero lag when watching lessons or submitting homework.
5. **Cost**: Zero license fees, open source, lightweight compute footprint.

## 3. Technology Selections

### 3.1 Frontend: React (Vite) + Tailwind CSS
- **React 18+ (Vite)**: Instant Hot Module Replacement (HMR), lightweight build outputs, massive ecosystem of battle-tested components (video players, timers, PDF view utilities).
- **Tailwind CSS**: Utility-first styling enables rapid mobile-first responsive styling without CSS bundle bloat or naming overhead. Provides a design-token approach for consistent color palettes and typography.
- **PWA Capabilities**: Service worker for caching core UI shells, offline status detection, and install-to-homescreen prompt on Android and iOS.

### 3.2 Backend: Python 3.11+ + FastAPI
- **FastAPI**: Asynchronous ASGI framework providing native OpenAPI/Swagger documentation, strict data validation with Pydantic v2, and high throughput.
- **Python**: Unmatched ecosystem for data processing, analytics, and future machine learning integrations.

### 3.3 Database: PostgreSQL 15+
- **PostgreSQL**: Industry standard ACID-compliant relational database. Supports strict foreign-key integrity for nested hierarchies (`Course → Subject → Chapter → Lecture`) and JSONB columns for flexible question bank rubrics.
- **ORM / Migrations**: SQLAlchemy 2.0 (asyncio) + Alembic for deterministic schema versioning.

## 4. Decision Outcome
**Accepted**. The application will be organized as a two-tier workspace:
- `frontend/` (React + Vite + Tailwind CSS)
- `backend/` (FastAPI + SQLAlchemy + PostgreSQL)
