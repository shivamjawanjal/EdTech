# Governance Charter & Agent Operating Model

## 1. Governance Principles

The engineering and product operations of the Teacher Learning & Productivity Platform are governed by four inviolable principles:

1. **Primacy of the CTO (@Education_CTO_Agent)**:  
   No architecture-altering change, library introduction, or schema deviation may be implemented without formal ADR approval from `@Education_CTO_Agent`.
2. **Domain Separation & No Cross-Domain Contamination**:  
   Each specialized agent possesses exclusive authority over their specific domain. No agent may unilaterally refactor another agent's domain code without prior formal handoff.
3. **The 5-Point Product Check**:  
   No feature may be developed unless it answers:
   - What problem does it solve?
   - Who uses it?
   - How frequently?
   - Does it improve student learning or teacher productivity?
   - What is the implementation and recurring infrastructure cost?
4. **Zero Unjustified Cost**:  
   Operating expenditure must remain strictly aligned with the 150-student private cohort budget ($15–$25/month).

---

## 2. Escalation & Dispute Resolution Matrix

```
                      Dispute or Deadlock Arises
                                  │
                                  ▼
                    Check Applicable ADR / Standards
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
              Clear Policy                 Policy Ambiguous
                   │                             │
                   ▼                             ▼
           Enforce Standard           Escalate to @Education_CTO_Agent
                                                 │
                                                 ▼
                                        Final CTO Ruling
                                      (Recorded in ADR/Task)
```

- If `@Frontend_Agent` and `@Backend_Agent` disagree on an API contract, `@Education_CTO_Agent` defines the schema.
- If `@Product_Agent` requests a feature that `@DevOps_Agent` assesses will violate the budget boundary, `@Education_CTO_Agent` rules on scope deferral.

---

## 3. Review & Approval Gates

Every task must pass through three formal review gates:
1. **Gate 1: Specification Review**: `@Product_Agent` and `@UX_UI_Agent` ensure alignment with teacher and student journeys.
2. **Gate 2: Technical & Security Review**: `@Security_Agent`, `@Database_Agent`, and `@Backend_Agent` verify data integrity and auth constraints.
3. **Gate 3: QA & Release Review**: `@QA_Agent` validates automated test suites and verifies zero regressions on the 150-student dataset fixtures.
