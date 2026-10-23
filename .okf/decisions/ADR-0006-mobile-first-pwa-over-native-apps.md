# ADR-0006: Mobile-First Progressive Web App (PWA) Architecture

- **Status**: Accepted
- **Date**: 2026-10-23
- **Proposing Agent**: `@UX_UI_Agent`
- **Approving Authority**: `@Education_CTO_Agent`
- **Consulted Agents**: `@Frontend_Agent`, `@DevOps_Agent`

---

## 1. Context & Problem Statement
Students will access the platform predominantly via mobile phones (Android smartphones and tablets). Building and deploying native iOS (Swift) and Android (Kotlin) apps introduces significant overhead:
- Mandatory developer account subscriptions ($99/year Apple, $25 Google).
- App store review delays (often 3–7 days for critical updates).
- Synchronizing changes across three distinct codebases.

## 2. Decision Drivers (5-Point Check)
1. **Problem Solved**: Delivers an app-like mobile experience on any smartphone with a single codebase and instant updates.
2. **Who it impacts**: Students (zero install friction, instant updates) and developers (single codebase).
3. **Usage Frequency**: Every mobile session.
4. **Pedagogical Impact**: Immediate access to study materials from student home screens.
5. **Cost**: Zero additional app store hosting or distribution fees.

## 3. Decision Outcome
**Build the platform as a responsive Progressive Web App (PWA) with Tailwind CSS:**
- Responsive layout targeting mobile viewport widths (360px – 420px) as primary, scaling gracefully to desktop tablets and monitors.
- Web App Manifest (`manifest.json`) providing app icon, standalone display mode, theme colors, and orientation control.
- Service Worker strategy: Cache-first for core application shell (HTML, CSS, JS bundles) and network-first for dynamic API endpoints and media tokens.
- Future path: If app store presence is requested in Phase 2, the PWA can be wrapped in an Android Trusted Web Activity (TWA) with zero code rewrite.
