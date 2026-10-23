# ADR-0003: Media Storage and Signed Delivery Architecture

- **Status**: Accepted
- **Date**: 2026-10-23
- **Proposing Agent**: `@Media_Agent`
- **Approving Authority**: `@Education_CTO_Agent`
- **Consulted Agents**: `@Backend_Agent`, `@Security_Agent`, `@DevOps_Agent`

---

## 1. Context & Problem Statement
The platform handles three categories of heavy binary media:
1. High-resolution lecture videos (100MB – 600MB per lecture).
2. Lecture notes and question sheets (PDFs, 1MB – 15MB).
3. Student homework submissions (Camera photos and PDFs, 2MB – 10MB per submission).

Serving these binaries directly through FastAPI endpoints or storing them on the application server disk causes severe disk exhaustion, degrades API worker responsiveness, and exposes permanent media URLs to unauthorized scraping or hotlinking.

## 2. Decision Drivers (5-Point Check)
1. **Problem Solved**: Offloads all streaming and download traffic from the API server and prevents unauthorized content leakage.
2. **Who it impacts**: Students (streaming speed), Teacher (upload speed), System (stability & cost).
3. **Usage Frequency**: Every video watched, note downloaded, or assignment submitted.
4. **Pedagogical Impact**: Fast, buffer-free playback on mobile cellular connections.
5. **Cost**: S3-compatible object storage (e.g., Cloudflare R2 has $0 egress fees; AWS S3 is pennies for 150 students).

## 3. Decision Outcome
**All media storage is strictly decoupled from the application server:**
1. **Direct Pre-Signed Uploads**:
   - When the teacher uploads a video or PDF, the backend issues an ephemeral pre-signed `PUT` URL. The client uploads directly to the object store bucket.
   - When a student submits homework photos/PDFs, the client uploads directly via an ephemeral pre-signed URL.
2. **Authenticated Pre-Signed Retrieval**:
   - Video streaming URLs and PDF download links are NEVER publicly accessible.
   - When an authenticated student requests a lecture, FastAPI validates enrollment and issues a time-limited pre-signed `GET` URL (TTL: 15–30 minutes).
3. **Download Permission Control**:
   - The teacher can configure per-asset flags: `allow_download = True/False`.
   - If false, the PDF viewer renders in a protected in-browser canvas view and video download headers are omitted.

### Positive Consequences
- API server stays ultra-lightweight; handles only JSON API requests.
- Video bandwidth does not saturate application server network interfaces.
- Zero risk of student video links being shared on public internet forums.
