# Development Workflow & Engineering Lifecycle

## 1. Core Development Philosophy: CLI-First & Lightweight

The platform is explicitly designed for fast, frictionless local development:
- **No Mandatory Docker**: Developers can run FastAPI (`uvicorn`) and React (`vite`) directly from native CLI environments.
- **Minimal Local Overhead**: Local PostgreSQL can be installed natively or via a lightweight single-command container if desired, but native local service execution is fully supported.
- **Predictable Toolchains**: Standard Python (`venv` / `poetry` / `uv`) and Node.js (`npm` or `pnpm`).

---

## 2. Standard Local Development Lifecycle

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ 1. ASSIGN TASK │────▶│ 2. WRITE SPEC  │────▶│ 3. DRAFT SCHEMA│────▶│ 4. CODE API &  │
│ (From Backlog) │     │ (PRD & AC)     │     │ & API CONTRACT │     │    FRONTEND    │
└────────────────┘     └────────────────┘     └────────────────┘     └───────┬────────┘
                                                                             │
                                                                             ▼
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ 8. MERGE TO    │◀────│ 7. CTO REVIEW  │◀────│ 6. QA PASS     │◀────│ 5. LOCAL RUN & │
│    MAIN        │     │  & ADR SIGN-OFF│     │ (Unit & Int.)  │     │   FORMAT CHECK │
└────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
```

### Step 1: Task Initialization
- Select task from `.okf/tasks/`.
- Ensure prerequisite user stories and acceptance criteria exist in `docs/product/`.

### Step 2: Architecture & Contract Review
- If database modifications are needed, `@Database_Agent` prepares the migration draft.
- If new endpoints or data models are needed, `@Backend_Agent` defines Pydantic schemas and OpenAPI response shapes before writing business logic.
- If new UI views are introduced, `@UX_UI_Agent` supplies component hierarchy and responsive layouts.

### Step 3: Local Implementation & Testing
- **Backend Running**:
  ```bash
  cd backend
  python -m venv .venv
  .venv\Scripts\activate  # Windows Powershell
  pip install -r requirements.txt
  uvicorn app.main:app --reload --port 8000
  ```
- **Frontend Running**:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
- **Testing Run**:
  ```bash
  # Run backend unit & integration tests
  pytest tests/ -v
  # Run frontend linters and typechecks
  npm run lint
  npm run build
  ```

### Step 4: Verification Gate
- No pull request / code merge proceeds without `@QA_Agent` validating:
  - All automated test suites pass.
  - No secrets or hardcoded credentials committed.
  - Zero performance regressions on 150-student synthetic dataset fixtures.

---

## 3. Branching & Commit Conventions

### Branch Strategy
- `main`: Production-ready, deployable code.
- `staging`: Integration branch for validating release candidates.
- `feature/<agent-domain>-<short-description>`: Active development branches (e.g., `feature/assessment-mcq-engine`, `feature/auth-jwt-guard`).
- `fix/<short-description>`: Urgent defect resolution.

### Commit Message Format (Conventional Commits)
```plaintext
<type>(<scope>): <concise imperative summary>

[optional detailed body explaining WHY, not just WHAT]

Refs: #<task-id>
Agent: @<AgentName>
```

**Types**:
- `feat`: New user-facing capability.
- `fix`: Bug fix.
- `refactor`: Internal structure change with zero functional impact.
- `test`: Addition or modification of tests.
- `docs`: Documentation updates.
- `chore`: Toolchain, dependency, or config updates.

---

## 4. Architectural Change Protocol

Any change meeting any of these conditions requires a formal **Architectural Decision Record (ADR)** in `.okf/decisions/` approved by `@Education_CTO_Agent`:
1. Introduces a new third-party dependency or external paid SaaS service.
2. Modifies core authentication, authorization, or role boundaries.
3. Changes media storage strategy or video delivery protocol.
4. Alters the data model across core domains (e.g., `Course → Subject → Chapter → Lecture`).
5. Deviates from the modular monolith pattern.
