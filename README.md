# Teacher Learning & Productivity Platform (EdtechWeb)

A private, high-efficiency digital classroom platform built for an independent educator teaching **Mathematics, Science, and Reasoning** to an initial cohort of 90–150 students.

---

## 🎯 Core Operating Thesis

> **TEACH → ASSIGN → TRACK → EVALUATE → IDENTIFY WEAK STUDENTS → IMPROVE**

The platform is designed to replace chaotic spreadsheets, fragmented WhatsApp groups, and unmanaged file links with a unified, automated, and secure digital teaching ecosystem. It simultaneously maximizes student mastery and amplifies teacher productivity with zero unnecessary administrative friction.

---

## 📐 Architecture & Technology Foundations

- **Frontend**: React (Vite), Tailwind CSS, Responsive Web Application / Progressive Web App (PWA) first.
- **Backend**: Python 3.11+, FastAPI (Modular Monolith with strict domain boundaries).
- **Database**: PostgreSQL (relational integrity, JSONB support for structured assessment rubrics, optimized indices).
- **Media & File Delivery**: Cloud Object Storage (S3-compatible) with pre-signed ephemeral URLs; no heavy binaries stored or served by FastAPI.
- **Live Class**: Seamless external provider integration (Google Meet via secure calendar links/deep links).
- **Environment & DX**: CLI-first local development without mandatory Docker virtualization overhead.
- **Budget Target**: Ultra low-cost operational profile tailored for 150–500 active learners.

---

## 🧭 Repository Structure

```plaintext
EdtechWeb/
├── .okf/                       # Orchestration & Knowledge Framework (Agent governance)
│   ├── agents/                 # Specifications for all 12 specialized agents
│   ├── decisions/              # Architectural Decision Records (ADRs)
│   ├── governance/             # Operating charter, review gates, escalation rules
│   ├── standards/              # Coding, API, and security standards
│   ├── tasks/                  # Task backlog and state tracking
│   └── templates/              # Standardized templates for ADRs, Tasks, Specs, Handoffs
├── docs/                       # Technical and Domain Documentation
│   ├── architecture/           # System topology, modular boundaries, security models
│   ├── product/                # PRD specs, workflows, teacher persona, student journey
│   ├── ux/                     # UX architecture, design tokens, responsive guidelines
│   ├── engineering/            # Local developer onboarding, project scaffolding spec
│   ├── database/               # Entity relationship models, indexing strategies
│   ├── analytics/              # Rule-based health classification ("On Track", "Needs Attention", "At Risk")
│   ├── testing/                # Multi-tier QA strategy, integration, and security test plans
│   └── deployment/             # Low-cost infrastructure topology, CI/CD runbooks
├── README.md                   # Project overview and index
├── PROJECT_CONTEXT.md          # Domain context, institute profile, pedagogical model
├── PRODUCT_VISION.md           # Product philosophy, outcomes, and value proposition
├── SCOPE.md                    # Total system scope and feature boundaries
├── MVP_SCOPE.md                # Ruthlessly prioritized Phase-1 feature manifest
├── ROADMAP.md                  # Staged progression: MVP → Scale → Future phases
├── AGENT_HIERARCHY.md          # Multi-agent role matrix, decision gates, handoff flows
├── DEVELOPMENT_WORKFLOW.md     # Git conventions, review process, CLI workflow
├── CONTRIBUTION_RULES.md       # Engineering standards, change policies, DoD
└── DECISION_LOG.md             # Chronological record of major technical & product choices
```

---

## 👥 Multi-Agent Operating Model

Development and governance are stewarded by 12 specialized autonomous roles:

| Agent Identifier | Domain Ownership |
| :--- | :--- |
| **`@Education_CTO_Agent`** | System Architecture, ADR Approval, Technical Governance, Scope Discipline |
| **`@Product_Agent`** | Requirements, PRD, User Stories, Pedagogy Workflows, Value Realization |
| **`@UX_UI_Agent`** | Design System, Mobile-First UX, Dashboards, Interaction Specs |
| **`@Frontend_Agent`** | React + Vite, Tailwind CSS, PWA, Client State, Routing, API Clients |
| **`@Backend_Agent`** | FastAPI, Modular Architecture, Auth, Business Rules, Worker Jobs |
| **`@Database_Agent`** | PostgreSQL Schema, Migrations, Query Tuning, Relational Integrity |
| **`@Media_Agent`** | Object Storage, Pre-signed URLs, Bandwidth Efficiency, Streaming & PDFs |
| **`@Assessment_Agent`** | Homework, Quizzes, Grading Workflows, Question Banks, Timed Tests |
| **`@Analytics_Agent`** | Progress Engine, At-Risk Detection, Topic Deficiency Diagnostics |
| **`@QA_Agent`** | Automated Unit/API Testing, End-to-End Scenarios, Regression Guardrails |
| **`@DevOps_Agent`** | CI/CD, CLI Environments, Cost-Effective Hosting, Observability |
| **`@Security_Agent`** | Token Auth, Media Authorization, RBAC, Rate Limiting, OWASP Hardening |

---

## 🚦 Governance & Next Steps

Application code implementation is deliberately held back until foundational governance, specifications, schemas, and UX architectures are ratified.

Refer to [`.okf/governance/GOVERNANCE_CHARTER.md`](file:///d:/EdtechWeb/.okf/governance/GOVERNANCE_CHARTER.md) and [`MVP_SCOPE.md`](file:///d:/EdtechWeb/MVP_SCOPE.md) for current directives.
