# Security Architecture & Data Protection Model

## 1. Threat Modeling & Protection Objectives

The platform safeguards three primary asset classes:
1. **Student Personal Data & Performance**: Grades, submission images, test scores, and activity telemetry.
2. **Proprietary Course Content**: Teacher video lectures, curated notes, and proprietary question banks.
3. **Administrative Access**: Teacher control over student accounts, content publication, and grading.

---

## 2. Authentication & Session Management

```
┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
│     Client      │             │  FastAPI Auth   │             │   PostgreSQL    │
│  (React / PWA)  │             │   Middleware    │             │    Database     │
└────────┬────────┘             └────────┬────────┘             └────────┬────────┘
         │                               │                               │
         │ 1. POST /api/v1/auth/login    │                               │
         │    (email/phone + password)   │                               │
         ├──────────────────────────────▶│ 2. Query user & hash          │
         │                               ├──────────────────────────────▶│
         │                               │◀──────────────────────────────┤
         │                               │ 3. Verify bcrypt hash         │
         │                               │ 4. Issue JWT access token     │
         │ 5. Set-Cookie: access_token   │                               │
         │    (HttpOnly, Secure, SameSite)                               │
         │◀──────────────────────────────┤                               │
```

- **Token Storage**: JWT stored exclusively in `HttpOnly`, `Secure`, `SameSite=Strict` cookies. This mitigates Cross-Site Scripting (XSS) token theft.
- **Access Token TTL**: 30 minutes.
- **Refresh Token TTL**: 7 days with database-backed token family tracking and immediate revocation upon logout.
- **Password Protection**: Passwords hashed with `bcrypt` (work factor 12) with salt.

---

## 3. Role-Based Access Control (RBAC) & IDOR Mitigation

### 3.1 Role Hierarchy
- **`Role: TEACHER`**: Full CRUD permissions across all courses, subjects, chapters, lectures, student rosters, grading consoles, and analytics.
- **`Role: STUDENT`**: Read access to enrolled batch curriculum; read/write access strictly restricted to own submissions, own test attempts, and own doubts.

### 3.2 Insecure Direct Object Reference (IDOR) Defense
To prevent a malicious or curious student from querying another student's assignment submission (`GET /api/v1/assessments/submissions/42`):
```python
# Enforced in domain service layer:
async def get_submission(submission_id: UUID, current_user: User):
    submission = await submission_repo.find_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Assert ownership or teacher privilege
    if not current_user.is_teacher and submission.student_id != current_user.id:
        # Log security audit warning
        logger.warning(f"IDOR attempt: User {current_user.id} accessed {submission_id}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    return submission
```

---

## 4. Object Storage & Media Protection

- **Bucket Policy**: All S3/R2 storage buckets have `Block Public Access` permanently enabled.
- **Signed URL Expiration**:
  - Lecture Video Streaming: 30 minutes TTL.
  - Lecture Notes PDF Download: 15 minutes TTL.
  - Assignment Photo Upload: 10 minutes TTL.
- **Validation on Upload**:
  - Strict MIME type verification using magic byte inspection (prevent executable file masquerading).
  - Size enforcement: Maximum 15MB for student submissions; maximum 1.5GB for teacher videos.
