# Multi-Tier Testing Strategy & QA Guardrails

## 1. Testing Pyramid & Verification Tiers

To ensure system reliability without slowing development velocity, the platform relies on a 4-tier testing hierarchy:

```
                      ┌─────────────────────────┐
                      │    TIER 4: E2E Tests    │ (5% - Playwright critical paths)
                      ├─────────────────────────┤
                      │  TIER 3: Security &     │ (15% - IDOR, JWT, Rate Limits)
                      │      Permission Scans   │
                      ├─────────────────────────┤
                      │  TIER 2: Integration    │ (30% - FastAPI TestClient, DB)
                      │       API Tests         │
                      ├─────────────────────────┤
                      │   TIER 1: Unit Tests    │ (50% - Scoring, Telemetry, Rules)
                      └─────────────────────────┘
```

---

## 2. Test Execution Tiers

### Tier 1: Unit Tests
- Domain models and validation logic (Pydantic schemas).
- Deterministic at-risk rule engine calculations (`RULE_BASED_AT_RISK_ENGINE.md`).
- MCQ instant scoring algorithms.
- Run time: `< 5 seconds`.

### Tier 2: Integration API Tests
- Built using `pytest` and `httpx.AsyncClient` targeting an isolated test PostgreSQL database.
- Verifies:
  - Role-based route access (`401 Unauthorized` without token, `403 Forbidden` if student accesses teacher endpoints).
  - Curriculum CRUD and lecture video attachment.
  - Assignment submission state transitions.
  - S3 pre-signed URL response format.

### Tier 3: Security & IDOR Penetration Testing
- Explicit test cases attempting:
  - Student A requesting `/api/v1/assessments/submissions/{student_b_submission_id}`.
  - Student attempting to submit homework past hard deadline without permission.
  - Brute force login attempts hitting rate-limit throttle.

### Tier 4: End-to-End Scenarios (Playwright)
- Tests complete student workflow in mobile viewport (390px x 844px):
  - Login → view today's lecture → trigger video progress → submit test → check score.

---

## 3. Synthetic 150-Student Dataset Fixtures

The test environment includes an automated generator script (`scripts/seed_dev_data.py`) populating:
- 1 Teacher account
- 150 Student accounts divided into 3 batches (Class 10A, 10B, Foundation)
- 3 Subjects (Mathematics, Science, Reasoning)
- 12 Chapters with 45 Lectures
- 150 Simulated video watch records
- 300 Assignment submissions with realistic states:
  - 240 `evaluated` submissions with marks
  - 40 `submitted` submissions waiting for evaluation
  - 20 `late` / `missing` submissions to trigger `At Risk` alerts
- 1 Timed MCQ Test with completed student attempts
