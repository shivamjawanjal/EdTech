# Authentication & FastAPI Backend Scaffolding

This document describes the FastAPI modular monolith application architecture, JWT token rotation mechanics, cookie-based session management, CSRF defense, and developer verification procedures implemented in **TASK-005**.

---

## 1. Application Architecture

The backend application is structured as a modular monolith:

```text
backend/
├── app/
│   ├── api/
│   │   ├── deps.py               # get_current_user, require_teacher, require_student, verify_csrf_protection
│   │   └── v1/
│   │       ├── auth.py           # /login, /refresh, /logout, /me
│   │       ├── health.py         # /health (distinguishes app and db connectivity)
│   │       └── test_roles.py     # Role verification endpoints
│   ├── core/
│   │   ├── config.py             # Pydantic v2 Settings with connection pool & CORS
│   │   ├── cookies.py            # Secure HttpOnly & CSRF double-submit cookie helpers
│   │   ├── database.py           # Async SQLAlchemy engine & session dependency
│   │   └── security.py           # Bcrypt hashing, SHA-256 token hashing, JWT creation/decoding
│   ├── models/                   # SQLAlchemy 2.0 Declarative models (29 tables across 12 domains)
│   ├── schemas/                  # Pydantic v2 request/response schemas
│   ├── services/
│   │   └── auth_service.py       # Authentication, atomic token rotation, reuse detection, revocation
│   └── main.py                   # FastAPI app factory, CORS, correlation logging, exception handlers
├── scripts/
│   └── seed_dev_data.py          # Idempotent 150-student synthetic development fixture generator
└── tests/
    ├── conftest.py               # Isolated savepoint transaction rollback fixture & AsyncClient
    ├── test_auth_api.py          # 12 authentication integration tests
    ├── test_security_deps.py     # 15 RBAC, token integrity, CSRF, CORS, and health tests
    ├── test_database_infra.py    # Database pooling & transaction rollback tests
    ├── test_migrations.py        # Alembic head consistency and schema drift tests
    ├── test_models.py            # Domain constraints and foreign key tests
    └── test_seed.py              # Synthetic seed distribution and idempotency tests
```

---

## 2. Token & Session Lifecycle

The platform uses a short-lived access token with rotating refresh tokens:

```
┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
│  Browser / PWA  │             │   FastAPI API   │             │   PostgreSQL    │
└────────┬────────┘             └────────┬────────┘             └────────┬────────┘
         │ 1. POST /api/v1/auth/login    │                               │
         ├──────────────────────────────▶│ 2. Verify Bcrypt hash         │
         │                               │ 3. Generate Access Token (30m)│
         │                               │ 4. Generate Refresh Token (7d)│
         │                               │ 5. Save SHA-256 token hash    │
         │                               ├──────────────────────────────▶│
         │ 6. Set-Cookie: access_token   │                               │
         │    Set-Cookie: refresh_token  │                               │
         │    Set-Cookie: csrf_token     │                               │
         │◀──────────────────────────────┤                               │
```

### 2.1 Cookie Security Attributes
- **`access_token`**:
  - `HttpOnly`: `True` (mitigates XSS exfiltration)
  - `Path`: `/`
  - `SameSite`: `lax` (or `strict`)
  - `Secure`: `False` in dev, `True` in production
  - `Max-Age`: 1800s (30 minutes)
- **`refresh_token`**:
  - `HttpOnly`: `True`
  - `Path`: `/api/v1/auth` (scoped strictly to auth endpoints for least privilege)
  - `SameSite`: `strict`
  - `Secure`: `False` in dev, `True` in production
  - `Max-Age`: 604800s (7 days)
- **`csrf_token`**:
  - `HttpOnly`: `False` (accessible to client JavaScript for Double-Submit CSRF header)
  - `Path`: `/`
  - `SameSite`: `lax`
  - `Max-Age`: 604800s

### 2.2 Token Family Reuse Detection
When `/api/v1/auth/refresh` is called:
1. The incoming token hash is queried in `refresh_tokens` using `with_for_update()` for concurrency safety.
2. If `is_revoked == True`:
   - An adversary or replay attack is attempting to reuse an already rotated token.
   - The auth service **immediately revokes all active refresh tokens for that user** (`UPDATE refresh_tokens SET is_revoked = TRUE WHERE user_id = :id`).
   - A security audit event (`AUTH_REFRESH_TOKEN_REUSE_DETECTED`) is written to `audit_events`.
   - The request is terminated with `401 Unauthorized`.
3. If valid, the current token is marked `is_revoked = True, revoked_at = NOW()`, and a replacement token is issued in the same `family_id`.

---

## 3. Local Development & Verification

### 3.1 Start Local PostgreSQL
Ensure PostgreSQL is active on port 5432:
```powershell
& "C:\Users\<username>\scoop\apps\postgresql\current\bin\postgres.exe" -D "C:\Users\<username>\scoop\apps\postgresql\current\data"
```

### 3.2 Run Migrations & Seed Data
```powershell
cd d:\EdtechWeb\backend
.venv\Scripts\alembic upgrade head
.venv\Scripts\python scripts/seed_dev_data.py
```

### 3.3 Run the Development Server
```powershell
cd d:\EdtechWeb\backend
.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive API Documentation: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/health`

### 3.4 Execute Automated Test Suite
```powershell
cd d:\EdtechWeb\backend
.venv\Scripts\pytest tests
```
Current test suite status: **38 passed in ~12 seconds** with 0 warnings.

---

## 4. API Request Examples

### 4.1 Login (Teacher or Student)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "teacher@edtechweb.local", "password": "TeacherPassword123!"}' \
  -c cookies.txt
```
Response:
```json
{
  "message": "Login successful",
  "token_type": "bearer",
  "user": {
    "id": "3b889789-f4d0-4261-ab32-43aff3ab6488",
    "phone": "+919999900000",
    "email": "teacher@edtechweb.local",
    "full_name": "Prof. Rajesh Sharma",
    "role": "teacher",
    "is_active": true,
    "must_change_password": false
  },
  "access_token": "eyJhbGciOiJIUz..."
}
```

### 4.2 Query Profile (`GET /api/v1/auth/me`)
Using stored cookies:
```bash
curl -X GET http://127.0.0.1:8000/api/v1/auth/me -b cookies.txt
```
Or using Authorization Bearer header:
```bash
curl -X GET http://127.0.0.1:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### 4.3 Rotate Refresh Token (`POST /api/v1/auth/refresh`)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/refresh \
  -b cookies.txt \
  -c cookies.txt
```

### 4.4 Logout (`POST /api/v1/auth/logout`)
When authenticated via cookies, include the CSRF token from the `csrf_token` cookie:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/logout \
  -b cookies.txt \
  -H "X-CSRF-Token: <value_of_csrf_token_cookie>" \
  -c cookies.txt
```

---

## 5. Security & Authorization Policy

1. **Role Enforcement (`require_teacher`, `require_student`)**:
   - Enforced strictly on the server by inspecting `User.role` from the validated JWT payload and active database record.
   - Unauthorized role attempts return `403 Forbidden` (`{"error": "Access restricted: Teacher privileges required"}`).
2. **Anti-IDOR Defense Strategy**:
   - Role dependencies guard route categories, but **do not prevent Insecure Direct Object References (IDOR)** on individual entity resources.
   - When downstream domain endpoints (`/courses`, `/assignments`, `/submissions`, `/doubts`) are created, service methods MUST assert that:
     ```python
     if not current_user.role == "teacher" and entity.student_id != current_user.id:
         raise HTTPException(status_code=403, detail="Access denied")
     ```
3. **No Plaintext Secrets**:
   - Password hashes: `bcrypt` (work factor 12).
   - Refresh token database values: `SHA-256` token digest. Reusable plaintext tokens are never written to disk or database tables.
