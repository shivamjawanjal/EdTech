# ADR-0005: Rule-Based Deterministic Student Health Engine

- **Status**: Accepted
- **Date**: 2026-10-23
- **Proposing Agent**: `@Analytics_Agent`
- **Approving Authority**: `@Education_CTO_Agent`
- **Consulted Agents**: `@Product_Agent`, `@Backend_Agent`

---

## 1. Context & Problem Statement
The teacher cannot manually cross-reference 150 students' attendance, video watch times, assignment submissions, and test scores on spreadsheets. At the same time, deploying black-box machine learning models or probabilistic AI scoring adds unnecessary hosting expenses, risks opaque hallucinations, and does not provide understandable explanations to the teacher.

## 2. Decision Drivers (5-Point Check)
1. **Problem Solved**: Automatically flags falling or disengaged students without manual calculations.
2. **Who it impacts**: Teacher (immediate intervention capability) and students (timely support).
3. **Usage Frequency**: Calculated in batch/daily and updated on event completions.
4. **Pedagogical Impact**: Catches disengaged students within 48 hours rather than waiting for exam failures.
5. **Cost**: Zero external AI API costs; pure relational database aggregation queries.

## 3. Decision Outcome
**Adopt a 100% transparent, explainable rule-based health classification engine:**

### Health Status Definitions
1. 🟢 **`On Track`**:
   - Assignment submission rate ≥ 80% (last 14 days)
   - Lecture video completion rate ≥ 75%
   - Test score average ≥ 60%
   - Last activity ≤ 48 hours ago
2. 🟡 **`Needs Attention`**:
   - Assignment submission rate between 60% and 79% OR
   - 1 or 2 missed assignments in the current active chapter OR
   - Test score average between 40% and 59% OR
   - Inactive for 3–4 days
3. 🔴 **`At Risk`**:
   - Inactive for > 4 consecutive days OR
   - ≥ 3 consecutive missing assignments OR
   - Test score average < 40% OR
   - Video watch completion < 30% on active chapter

### Transparency Guarantee
Whenever a student is displayed in the teacher dashboard with a `Needs Attention` or `At Risk` badge, the UI displays explicit audit reasons (e.g., *"Flagged At Risk: Missed 3 consecutive assignments (HW 4, 5, 6); Inactive for 5 days"*).
