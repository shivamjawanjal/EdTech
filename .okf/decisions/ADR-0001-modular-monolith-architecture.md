# ADR-0001: Modular Monolith Architecture over Microservices

- **Status**: Accepted
- **Date**: 2026-10-23
- **Proposing Agent**: `@Education_CTO_Agent`
- **Approving Authority**: `@Education_CTO_Agent`
- **Consulted Agents**: `@Backend_Agent`, `@DevOps_Agent`, `@Database_Agent`

---

## 1. Context & Problem Statement
The platform is an edtech solution for a single teacher institute serving an initial cohort of 90–150 students with future growth potential to 500+ students. 

Distributed architectures (microservices, event buses like Kafka, separate containerized deployment targets) introduce immense operational complexity, multi-repo overhead, network latency, distributed transaction failure modes, and inflated infrastructure costs. For a team prioritizing rapid time to market and low operating expenditure ($15–$25/month), microservices represent catastrophic premature optimization.

## 2. Decision Drivers (5-Point Check)
1. **Problem Solved**: Eliminates infrastructure sprawl, distributed network failures, and high cloud hosting bills.
2. **Who it impacts**: The engineering team and the teacher (keeps operating costs ultra-low).
3. **Usage Frequency**: Every request in the system.
4. **Pedagogical Impact**: Maximizes system reliability and responsiveness for students while enabling fast feature delivery.
5. **Cost**: Minimizes compute needs to a single lightweight VPS or PaaS dyno ($5–$15/month).

## 3. Considered Options
- **Option 1: Microservices (Auth, Content, Assessment, Analytics as separate microservices)**
  - *Cons*: Requires service discovery, API gateways, multiple databases, distributed tracing, Kubernetes/Docker cluster ($100+/mo).
- **Option 2: Unstructured Monolith (Spaghetti code with intertwined DB calls)**
  - *Cons*: Leads to code rot, tight coupling, impossible to maintain as features grow.
- **Option 3: Modular Monolith (Single FastAPI codebase with strict internal domain boundaries)**
  - *Pros*: Single deployable artifact, fast local CLI execution, clean domain interfaces, zero network latency between modules, shared database with transactional guarantees.

## 4. Decision Outcome
**Chosen: Option 3 (Modular Monolith)**.

The FastAPI application will be structured into explicit domain modules:
```
backend/app/
├── core/               # Configuration, security utilities, database session engine
├── domains/
│   ├── identity/       # Users, roles, auth, batch enrollment
│   ├── curriculum/     # Course, Subject, Chapter, Lecture, Notes
│   ├── media/          # S3 presigning, file metadata, upload quotas
│   ├── assessment/     # Assignments, Submissions, Tests, Grading
│   ├── telemetry/      # Video heartbeats, daily student presence
│   ├── analytics/      # At-risk rule engine, teacher dashboard metrics
│   ├── doubts/         # Student questions, teacher responses
│   └── live/           # Google Meet scheduling, countdowns
└── main.py             # FastAPI entrypoint mounting domain routers
```

### Positive Consequences
- Development can be run directly via `uvicorn app.main:app --reload` from any terminal.
- Single database connection pool; atomic relational transactions across curriculum and assessment.
- Extremely low memory footprint (< 150MB RAM).

### Negative Consequences & Mitigations
- *Risk*: Developers might cross-import private domain internals.
- *Mitigation*: `@Backend_Agent` and `@QA_Agent` enforce domain boundaries; modules may only interact via public domain services.
