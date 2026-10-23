# Change Management & Versioning Protocol

## 1. Classification of Changes

To maintain high development velocity while preventing unintended regressions, all project modifications are categorized into three tiers:

| Tier | Classification | Examples | Approval Requirement |
| :--- | :--- | :--- | :--- |
| **Tier 1: Architectural** | Data model structural changes, new infrastructure dependencies, auth changes, protocol shifts. | Changing video delivery protocol, altering Course-Subject-Chapter hierarchy, introducing third-party services. | Mandatory ADR in `.okf/decisions/` approved by `@Education_CTO_Agent`. |
| **Tier 2: Feature & API** | New API endpoints, new UI views, modifications to grading algorithms, new user stories. | Adding a doubt resolution filter, creating a chapter test creation modal, updating student health thresholds. | Product Spec in `docs/product/` approved by `@Product_Agent` + domain agent sign-off. |
| **Tier 3: Internal / Maintenance** | Bug fixes, internal refactoring within domain boundaries, styling polish, unit test additions. | Fixing a date formatting error, improving CSS alignment, adding test cases for edge boundary values. | Peer review and QA pass by `@QA_Agent`. |

---

## 2. Deprecation & Migration Policy

1. **Database Schema Evolution**:
   - Destructive migrations (`DROP COLUMN`, `DROP TABLE`) are strictly forbidden on active data without a 2-phase migration strategy.
   - All migrations must have a forward (`upgrade()`) and backward (`downgrade()`) path tested in Alembic.
2. **API Endpoint Evolution**:
   - Breaking API payload changes require versioning or backwards-compatible deprecation notices before removal.
