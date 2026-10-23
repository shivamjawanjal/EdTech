# Contribution Rules & Engineering Principles

## 1. The 5-Point Product Justification Rule

**No feature may be designed or coded simply because it is technically intriguing or trendy.**

Every proposed feature, component, or enhancement must explicitly pass the **5-Point Justification Test** before inclusion in any sprint or task backlog:

1. **What specific problem does it solve?**  
   *(e.g., "The teacher spends 45 minutes every evening matching WhatsApp screenshot photos to a paper roll call sheet.")*
2. **Who uses it?**  
   *(Explicitly: Teacher, Student, or System Orchestrator)*
3. **How frequently will it be used?**  
   *(Daily, weekly, or once per semester)*
4. **Does it demonstrably improve student learning or teacher productivity?**  
   *(If it does not directly accelerate comprehension, submission adherence, or teacher diagnostic speed, it is rejected.)*
5. **What is its ongoing implementation and maintenance cost?**  
   *(In compute, database storage, third-party API fees, and developer cognitive load.)*

---

## 2. Definition of Done (DoD)

A task or feature branch is considered **Done** only when all of the following conditions are satisfied:

### 2.1 Specification & Alignment
- [ ] User story and acceptance criteria documented and approved by `@Product_Agent`.
- [ ] UI follows design tokens and mobile-first guidelines set by `@UX_UI_Agent`.
- [ ] Any architectural shift is documented in `.okf/decisions/` and approved by `@Education_CTO_Agent`.

### 2.2 Code Quality & Structure
- [ ] Strict adherence to domain boundaries within the modular monolith (no circular imports between modules).
- [ ] All Python code typed with Pydantic / Python typing annotations and formatted via `black` / `ruff`.
- [ ] All React code uses functional components, custom hooks, and Tailwind CSS (no inline hardcoded hex color values).
- [ ] Clear docstrings and comments preserved; no orphaned debugging statements (`console.log`, `print`).

### 2.3 Automated Testing & Reliability
- [ ] Unit tests cover domain logic and edge cases (minimum 80% coverage on core business algorithms).
- [ ] API integration tests verify endpoint response codes, payload validation, and authorization guards.
- [ ] Verified against simulated 150-student concurrent load fixtures (no N+1 query bottlenecks).

### 2.4 Security & Compliance
- [ ] Zero exposed credentials, API keys, or private S3 buckets.
- [ ] Media assets strictly delivered through authenticated pre-signed URLs.
- [ ] Endpoints protected by RBAC; student cannot read another student's assignment or test submission.

### 2.5 Documentation & Handoff
- [ ] API OpenAPI docs automatically refreshed.
- [ ] Task status updated in `.okf/tasks/` with sign-off from `@QA_Agent` and `@Education_CTO_Agent`.

---

## 3. Prohibited Practices (Anti-Patterns)

- ❌ **No Direct Storage of Video Blobs in FastAPI or PostgreSQL**: All videos must reside in external object storage.
- ❌ **No Premature Microservices**: Everything runs within a single modular backend repo; microservice sprawl is banned.
- ❌ **No Silent Architectural Shifts**: Modifying database schemas or auth flows without an ADR will result in an immediate revert.
- ❌ **No Opaque Black-Box Algorithms**: Student health categories (`On Track`, `Needs Attention`, `At Risk`) must be based on auditable, deterministic criteria.
- ❌ **No Desktop-Only Interfaces**: Every student interface must be designed mobile-first (360px–420px viewports tested first).
