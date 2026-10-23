# QA Test Plan: [TEST-PLAN-ID] [Feature / Module Name]

- **Target Feature**: `[FEAT-XYZ]`
- **QA Lead**: `@QA_Agent`
- **Reviewed By**: `@Backend_Agent`, `@Frontend_Agent`
- **Execution Date**: YYYY-MM-DD
- **Target Environment**: Local / Staging

---

## 1. Scope of Testing
- **In Scope**: [List of modules, endpoints, UI views tested]
- **Out of Scope**: [Explicit non-tested areas]

## 2. Test Strategy & Tiers
- **Tier 1: Unit Tests** (Domain algorithms, data transformations, validators)
- **Tier 2: API Integration Tests** (FastAPI `TestClient` endpoint status, auth, payload errors)
- **Tier 3: End-to-End Scenarios** (Mobile PWA viewport flow, video heartbeat, assignment submission)
- **Tier 4: Security & Permission Scans** (IDOR tests, token expiration, unauthorized role attempts)

## 3. Test Cases Matrix

| Test Case ID | Description | Preconditions | Action / Payload | Expected Result | Pass / Fail |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-001` | Successful student login | Student enrolled | Valid credentials | 200 OK + JWT cookie | [ ] |
| `TC-002` | Student accesses other student submission | Student logged in | Request another submission ID | 403 Forbidden | [ ] |
| `TC-003` | Video watch heartbeat increment | Lecture active | Send 10s playback ping | Progress updated; status 200 | [ ] |

## 4. Synthetic Load & Performance Validation
- Tested with 150 student fixture records.
- Max response latency under local test: `< 300ms`.
- DB queries checked for N+1 query patterns.

## 5. Defect Log & Blockers
- Bug 1: [Description, severity, assigned agent]

## 6. Sign-off & Release Verdict
- **Status**: [PASSED | BLOCKED | CONDITIONALLY APPROVED]
- **QA Sign-off**: `@QA_Agent` on YYYY-MM-DD
