# Security & Student Data Protection Standards

## 1. Authentication & Token Security

- **Algorithm**: `RS256` or `HS256` with strong 256-bit environment secrets.
- **Token Delivery**: Secure HTTP-only, SameSite=Strict cookies to guard against XSS token exfiltration.
- **Token Expiry**:
  - Access Token: 15–30 minutes expiration.
  - Refresh Token: 7 days with rotation and server-side revocation on logout.
- **Passwords**: Hashed exclusively using `bcrypt` (work factor 12) or `argon2id`.

---

## 2. Authorization & RBAC Boundaries

- **Roles**:
  - `teacher`: Full read/write access across all curriculum, student records, assignments, tests, and analytics.
  - `student`: Strictly restricted to enrolled courses, own submissions, own test results, and own doubt threads.
- **Anti-IDOR Policy (Insecure Direct Object Reference)**:
  - Every query accessing student-sensitive data (e.g., `/api/v1/submissions/{id}`) MUST assert that `submission.student_id == current_user.id` or `current_user.is_teacher == True`.
  - Violations must trigger an immediate `403 Forbidden` response and an audit security log.

---

## 3. Media Asset Access Protection

- **No Public S3 Buckets**: All buckets configured with `Block Public Access: ON`.
- **Pre-signed URLs**:
  - Generated on-demand with maximum lifetime of 30 minutes for videos and 15 minutes for homework uploads.
  - URL generation endpoints verify active enrollment before signing.
- **File Validation**:
  - Uploaded files validated against both MIME type header and magic byte inspection (preventing `.exe` renamed as `.pdf`).
  - Strict upload payload size limits:
    - Assignment photo/PDF: Max 15MB.
    - Teacher lecture video: Max 1.5GB (direct client-to-S3 upload).

---

## 4. OWASP & Infrastructure Hardening

- **CORS**: Strictly locked to allowed origins (no `Allow-Origin: *` in production).
- **Rate Limiting**:
  - Login endpoint: Max 5 failed attempts per IP per 10 minutes.
  - Telemetry heartbeat: Max 1 ping per 5 seconds per client.
- **Input Sanitization**: Pydantic models automatically sanitize and strip script tags from student doubt inputs.
