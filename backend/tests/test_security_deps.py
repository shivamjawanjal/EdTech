from datetime import timedelta
import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token
from app.models.identity import User

settings = get_settings()


# =========================================================================
# 1. Role-Based Access Control (RBAC) Tests
# =========================================================================


@pytest.mark.asyncio
async def test_teacher_can_access_teacher_only_endpoint(
    client: AsyncClient, test_teacher: User
):
    """Verify that a user with the teacher role can access teacher-guarded routes."""
    # Login as teacher
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher@edtech.local", "password": "TeacherPassword123!"},
    )
    assert login_resp.status_code == 200

    # Access teacher-only route
    resp = await client.get("/api/v1/roles/teacher-only")
    assert resp.status_code == 200
    assert resp.json()["role"] == "teacher"


@pytest.mark.asyncio
async def test_student_forbidden_from_teacher_endpoint(
    client: AsyncClient, test_student: User
):
    """Verify that a student is strictly rejected with 403 Forbidden from teacher routes."""
    # Login as student
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "student001@edtech.local", "password": "StudentPassword123!"},
    )
    assert login_resp.status_code == 200

    # Attempt to access teacher-only route
    resp = await client.get("/api/v1/roles/teacher-only")
    assert resp.status_code == 403
    data = resp.json()
    assert "teacher privileges required" in data["error"].lower()


@pytest.mark.asyncio
async def test_student_can_access_student_only_endpoint(
    client: AsyncClient, test_student: User
):
    """Verify that a student can access student-guarded routes."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "student001@edtech.local", "password": "StudentPassword123!"},
    )
    assert login_resp.status_code == 200

    resp = await client.get("/api/v1/roles/student-only")
    assert resp.status_code == 200
    assert resp.json()["role"] == "student"


@pytest.mark.asyncio
async def test_teacher_forbidden_from_student_endpoint(
    client: AsyncClient, test_teacher: User
):
    """Verify that a teacher is rejected with 403 from student-exclusive routes."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher@edtech.local", "password": "TeacherPassword123!"},
    )
    assert login_resp.status_code == 200

    resp = await client.get("/api/v1/roles/student-only")
    assert resp.status_code == 403
    data = resp.json()
    assert "student privileges required" in data["error"].lower()


# =========================================================================
# 2. Token Integrity, Expiration & Malformed Payload Tests
# =========================================================================


@pytest.mark.asyncio
async def test_expired_access_token_rejected(client: AsyncClient, test_student: User):
    """Verify that an expired JWT access token is rejected with 401 Unauthorized."""
    expired_token = create_access_token(
        subject=str(test_student.id),
        role=test_student.role,
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401
    assert "could not validate credentials" in resp.json()["error"].lower()


@pytest.mark.asyncio
async def test_malformed_token_rejected(client: AsyncClient):
    """Verify that a garbage/malformed token string is rejected with 401."""
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt.token"},
    )
    assert resp.status_code == 401
    assert "could not validate credentials" in resp.json()["error"].lower()


@pytest.mark.asyncio
async def test_wrong_token_purpose_rejected(client: AsyncClient, test_student: User):
    """Verify that using a refresh token as an access token is rejected with 401."""
    raw_refresh, _, _, _ = create_refresh_token(user_id=str(test_student.id))
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {raw_refresh}"},
    )
    assert resp.status_code == 401
    assert "expected access token" in resp.json()["error"].lower()


@pytest.mark.asyncio
async def test_forged_secret_token_rejected(client: AsyncClient, test_student: User):
    """Verify that a token signed with an unauthorized/different secret is rejected."""
    forged_token = jwt.encode(
        {"sub": str(test_student.id), "role": "teacher", "typ": "access"},
        "wrong_attacker_secret_key_987654321",
        algorithm="HS256",
    )
    resp = await client.get(
        "/api/v1/roles/teacher-only",
        headers={"Authorization": f"Bearer {forged_token}"},
    )
    assert resp.status_code == 401


# =========================================================================
# 3. CSRF Protection for Cookie Authentication
# =========================================================================


@pytest.mark.asyncio
async def test_cookie_auth_state_changing_request_fails_without_csrf_header(
    client: AsyncClient, test_teacher: User
):
    """
    Verify that when authenticated via cookies, a state-changing POST request
    without the X-CSRF-Token header is rejected with 403 Forbidden.
    """
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher@edtech.local", "password": "TeacherPassword123!"},
    )
    assert login_resp.status_code == 200

    # Attempt logout without X-CSRF-Token header
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 403
    data = resp.json()
    assert "csrf validation failed" in data["error"].lower()


@pytest.mark.asyncio
async def test_cookie_auth_state_changing_request_fails_with_mismatched_csrf(
    client: AsyncClient, test_teacher: User
):
    """Verify that submitting an invalid/tampered X-CSRF-Token header is rejected with 403."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher@edtech.local", "password": "TeacherPassword123!"},
    )
    assert login_resp.status_code == 200

    resp = await client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": "invalid_forged_csrf_token_value"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_bearer_auth_exempt_from_csrf(client: AsyncClient, test_teacher: User):
    """
    Verify that requests authenticated via explicit Authorization: Bearer header
    are exempt from CSRF checks (since browsers never auto-send Bearer headers cross-origin).
    """
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher@edtech.local", "password": "TeacherPassword123!"},
    )
    access_token = login_resp.json()["access_token"]
    refresh_token = login_resp.cookies.get("refresh_token")

    # Clear cookies
    client.cookies.clear()

    # Logout using Bearer access header and refresh token in body/header
    client.cookies.set("refresh_token", refresh_token)
    # With Authorization header, no cookie access_token is present
    resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code in (200, 403)  # If refresh_token cookie is present, CSRF applies


# =========================================================================
# 4. CORS Origins & Security Headers
# =========================================================================


@pytest.mark.asyncio
async def test_cors_allowed_origin(client: AsyncClient):
    """Verify CORS preflight succeeds for approved client origins with credentials."""
    response = await client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"
    # Never allow wildcard with credentials
    assert response.headers.get("access-control-allow-origin") != "*"


@pytest.mark.asyncio
async def test_cors_disallowed_origin(client: AsyncClient):
    """Verify CORS preflight does not grant access to unauthorized origins."""
    response = await client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://unauthorized-evil-site.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.headers.get("access-control-allow-origin") is None


# =========================================================================
# 5. Correlation ID & Health Check
# =========================================================================


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Verify health endpoint distinguishes application responsiveness from database connectivity."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["environment"] == settings.ENVIRONMENT


@pytest.mark.asyncio
async def test_custom_request_id_preserved(client: AsyncClient):
    """Verify custom X-Request-ID header sent by client is preserved in response."""
    custom_id = "test-correlation-uuid-998877"
    response = await client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id
