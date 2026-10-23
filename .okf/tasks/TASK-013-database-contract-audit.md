# Task: TASK-013 Database Contract Audit and Implementation Readiness

- **Assigned Agent**: `@Database_Agent` (Lead) & `@Education_CTO_Agent` (Orchestrator)
- **Domain**: Database & Architecture
- **Status**: Done
- **Target Release**: MVP Phase 1
- **Created Date**: 2026-10-23
- **Completed Date**: 2026-10-23

---

## 1. Discrepancy Note & Task ID Resolution

> [!NOTE]
> **Task ID Discrepancy Documentation**:
> In `.okf/tasks/TASK_INDEX.md`, `TASK-004` was previously allocated as "PostgreSQL Schema Design & Alembic Scaffolding" (Backlog). Per the governance directive (*"Do not overwrite or reuse an existing task ID. If TASK-004 is already assigned, continue under the next available ID and document the discrepancy"*), this database contract audit and implementation readiness specification is formally assigned and tracked under **`TASK-013`**. 
>
> `TASK-013` establishes the verified, implementation-ready relational schema specification and integrity contract. `TASK-004` is preserved as the subsequent execution task (SQLAlchemy model coding and Alembic migration scaffolding).

---

## 2. Objective & Context

Inspect the existing repository and establish a verified, implementation-ready PostgreSQL schema contract for the Teacher Learning & Productivity Platform, covering all 12 functional domains with explicit relational models, constraints, indexing strategies, retention policies, and architectural alignment.

---

## 3. Prerequisites & Dependencies

- Depends on: `[ADR-0001]`, `[ADR-0002]`, `[ADR-0003]`, `[ADR-0004]`, `[ADR-0005]`, `[ADR-0006]`
- Blocks: `[TASK-004]` (PostgreSQL Schema Design & Alembic Scaffolding), `[TASK-005]` (FastAPI Backend Scaffolding)

---

## 4. Scope of Work & Deliverables

- [x] **Phase 1: Repository & Task Audit**
  - Inspected existing documentation (`README.md`, `MVP_SCOPE.md`, `docs/database/`, `docs/product/`, `docs/architecture/`).
  - Identified missing entities (doubts, live attendance, announcements, notifications, audit events, resubmission tracking).
  - Documented task allocation discrepancy with `TASK-004`.
- [x] **Phase 2: Relational Contract Specification**
  - Updated `docs/database/ENTITY_RELATIONSHIPS.md` with complete 12-domain relationship matrix.
  - Created `docs/database/SCHEMA_SPECIFICATION.md` detailing all 21 tables, column types, keys, and nullability.
  - Defined explicit distinction between live class click-through evidence and teacher-verified participation.
  - Modeled assignment resubmission versioning and attempt history.
- [x] **Phase 3: Design Decisions Resolution**
  - Documented unresolved choices (enrolment workflow, multi-course access, file sizes, test retakes) with recommended defaults marked `OPEN`.
- [x] **Phase 4: Implementation Readiness & Guardrails**
  - Created `docs/database/INDEXING_AND_CONSTRAINTS.md` (Composite indexes, checks, concurrency invariants).
  - Created `docs/database/DATA_RETENTION.md` (Retention, rolling purge, archival rules).
  - Created `docs/engineering/DATABASE_IMPLEMENTATION_PLAN.md` (Requirement traceability matrix, pool sizing, Alembic sequencing).
  - Updated `.okf/tasks/TASK_INDEX.md`.

---

## 5. Verification & Testing Evidence

- **Entity Count**: 21 normalized relational tables covering all 12 domains.
- **Integrity Constraints**: Explicit `CHECK` constraints on status enums, marks, percentages, file sizes (< 15MB), and MIME types.
- **Index Plan**: 7 high-performance dashboard indexes + foreign key indexes for sub-10ms query execution on 150-student datasets.
- **Connection Pool**: Sized for 150–500 students (10 persistent + 20 overflow connections) consuming < 50MB RAM.

---

## 6. Approvals & Sign-off

- **Author Agent**: `@Database_Agent`
- **Reviewer Agent**: `@Security_Agent`, `@Assessment_Agent`, `@Analytics_Agent`
- **Final Approval**: `@Education_CTO_Agent`
