# ADR-0004: External Integration with Google Meet for Live Classes

- **Status**: Accepted
- **Date**: 2026-10-23
- **Proposing Agent**: `@Education_CTO_Agent`
- **Approving Authority**: `@Education_CTO_Agent`
- **Consulted Agents**: `@Product_Agent`, `@DevOps_Agent`

---

## 1. Context & Problem Statement
The teacher requires periodic live interactive problem-solving and doubt-clearing sessions. Building custom real-time video conferencing (WebRTC, SFU/MCU media servers like Mediasoup or Jitsi) requires dedicated high-CPU infrastructure, TURN/STUN servers, complex bandwidth adaptation algorithms, and constant operational maintenance.

## 2. Decision Drivers (5-Point Check)
1. **Problem Solved**: Provides high-quality live video interaction with zero infrastructure investment.
2. **Who it impacts**: Teacher and students during live schedules.
3. **Usage Frequency**: 2–4 times per week.
4. **Pedagogical Impact**: Immediate, crystal-clear face-to-face interaction without buggy custom video players.
5. **Cost**: $0 infrastructure cost (uses standard Google Workspace / Google Meet infrastructure).

## 3. Decision Outcome
**Integrate Google Meet via an intelligent scheduled launcher within the platform:**
- The teacher schedules a live session within the Course/Subject schedule (Title, Date, Time, Batch, Google Meet URL).
- The platform displays an interactive countdown banner to enrolled students.
- When the class goes live (e.g., 10 minutes prior), an authenticated "Join Live Class" button unlocks.
- The platform logs student click-through to record presence/attendance telemetry.
- Recording links can subsequently be pasted into the Lecture archive as a recorded lecture asset.
