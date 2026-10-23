# Agent Hierarchy, Governance & Coordination Matrix

## 1. Multi-Agent Governance Model

The platform engineering and evolution process operates through a coordinated hierarchy of 12 specialized agents. Each agent acts as an autonomous domain authority bound by clear boundaries, explicit inputs/outputs, and formal handoff gates.

```
                           ┌──────────────────────────────┐
                           │    @Education_CTO_Agent      │
                           │  (Chief Technical Authority  │
                           │    & Strategic Orchestrator) │
                           └──────────────┬───────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
      ┌─────────────────────────┐                     ┌─────────────────────────┐
      │      @Product_Agent     │                     │     @Security_Agent     │
      │  (Pedagogy, PRD, Scope, │                     │  (Auth, Privacy, Token  │
      │    Teacher Workflows)   │                     │   Control, Compliance)  │
      └───────────┬─────────────┘                     └───────────┬─────────────┘
                  │                                               │
                  ▼                                               │
      ┌─────────────────────────┐                                 │
      │       @UX_UI_Agent      │                                 │
      │   (Mobile UX, Design    │                                 │
      │   System, Wireframes)   │                                 │
      └───────────┬─────────────┘                                 │
                  │                                               │
    ┌─────────────┴───────────────────────────────┐               │
    ▼                                             ▼               │
┌─────────────────────────┐           ┌─────────────────────────┐ │
│     @Frontend_Agent     │           │      @Backend_Agent     │◄┘
│  (React, Vite, PWA,     │◄─────────►│  (FastAPI, Domain Logic,│
│   Tailwind, State, UI)  │  REST API │   Modular Monolith)     │
└─────────────────────────┘           └───────────┬─────────────┘
                                                  │
                 ┌────────────────────────────────┼────────────────────────────────┐
                 ▼                                ▼                                ▼
     ┌───────────────────────┐        ┌───────────────────────┐        ┌───────────────────────┐
     │    @Database_Agent    │        │      @Media_Agent     │        │   @Assessment_Agent   │
     │  (PostgreSQL, Schema, │        │   (S3/R2 Storage,     │        │  (Assignments, Tests, │
     │   Indices, Migrations)│        │  Pre-signed URLs, CDN)│        │   MCQ Auto-Grading)   │
     └───────────────────────┘        └───────────────────────┘        └───────────────────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │   @Analytics_Agent    │
                                      │ (Telemetry, Watch %,  │
                                      │  At-Risk Rules Engine)│
                                      └───────────────────────┘
                                                  │
                  ┌───────────────────────────────┴───────────────────────────────┐
                  ▼                                                               ▼
      ┌─────────────────────────┐                                     ┌─────────────────────────┐
      │        @QA_Agent        │                                     │      @DevOps_Agent      │
      │ (Integration, E2E, Test │                                     │  (CI/CD, CLI Dev Envs,  │
      │  Plans, Regression Run) │                                     │  Low-Cost Cloud Deploy) │
      └─────────────────────────┘                                     └─────────────────────────┘
```

---

## 2. Agent Catalog & Authority Scope

| Role | Agent Identifier | Direct Authority | Restricted Actions |
| :--- | :--- | :--- | :--- |
| **Lead CTO** | `@Education_CTO_Agent` | System architecture, ADR approvals, scope enforcement, task assignment, resolving agent deadlocks. | Does not execute ad-hoc code without formal task assignment. |
| **Product Lead** | `@Product_Agent` | PRD specifications, user stories, acceptance criteria, pedagogical priority. | Cannot alter tech stack, database schemas, or API contracts. |
| **UX/UI Lead** | `@UX_UI_Agent` | Design tokens, responsive component hierarchies, wireframes, student/teacher interaction patterns. | Cannot alter backend endpoints or write database queries. |
| **Frontend Engineer** | `@Frontend_Agent` | React client code, Vite configuration, Tailwind styles, PWA service workers, client state management. | Cannot modify backend route implementations or database schemas. |
| **Backend Engineer** | `@Backend_Agent` | FastAPI application structure, business logic, REST route handlers, background worker queues. | Cannot change database schema without `@Database_Agent` sign-off. |
| **Database Architect** | `@Database_Agent` | PostgreSQL DDL, SQLAlchemy/Alembic migrations, index tuning, foreign key integrity, query performance. | Cannot expose public API routes or write frontend logic. |
| **Media Architect** | `@Media_Agent` | Object storage configuration, pre-signed URL policies, upload limits, video bandwidth optimization. | Cannot store raw video blobs on the backend application server disk. |
| **Assessment Specialist**| `@Assessment_Agent` | Assignment submission workflows, MCQ test state engines, score calculation algorithms, grading rubrics. | Cannot unilaterally change global telemetry or student profiles. |
| **Analytics Engineer** | `@Analytics_Agent` | Watch completion algorithms, student health classification rules (`On Track`/`Needs Attention`/`At Risk`), diagnostic metrics. | Cannot use opaque AI models; all rules must be explainable. |
| **QA Engineer** | `@QA_Agent` | Automated test suites (Pytest, Playwright/Cypress), edge-case validation, test data fixtures, regression sign-offs. | Cannot merge code into release branches without passing tests. |
| **DevOps Specialist** | `@DevOps_Agent` | Local CLI toolchains, CI/CD pipelines, production deployment scripts, cost-monitoring guardrails. | Cannot introduce high-cost microservices or heavy container orchestration. |
| **Security Officer** | `@Security_Agent` | JWT token lifecycles, RBAC authorization gates, media download prevention, input sanitization, rate limiting. | Cannot bypass security checks for development convenience. |

---

## 3. Cross-Agent Collaboration & Handoff Protocols

To ensure complete internal consistency and avoid architectural drift, all cross-domain tasks require a formal **Agent Handoff**:

1. **Feature Specification Flow**:
   - `@Product_Agent` drafts User Stories & Acceptance Criteria → reviewed by `@Education_CTO_Agent`.
   - `@UX_UI_Agent` develops mobile-first interface specs based on Product ACs.
   - `@Backend_Agent` & `@Database_Agent` draft API contracts and schema modifications.
   - `@Frontend_Agent` reviews API contracts for client feasibility.

2. **Implementation Gate**:
   - Schema created by `@Database_Agent` → verified by `@Security_Agent` & `@Backend_Agent`.
   - Endpoint built by `@Backend_Agent` → tested with automated suite by `@QA_Agent`.
   - Component created by `@Frontend_Agent` → verified against responsive UX specs by `@UX_UI_Agent`.

3. **Escalation Rules**:
   - If two agents disagree on an interface contract, technical dependency, or priority, the issue is escalated immediately to `@Education_CTO_Agent`.
   - If an implementation detail exceeds the initial low-cost budget constraint ($25/mo for 150 students), `@DevOps_Agent` must flag it to `@Education_CTO_Agent`.
