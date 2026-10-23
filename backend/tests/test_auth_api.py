import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.models.analytics import AuditEvent
from app.models.identity import RefreshToken, User


@pytest.mark.asyncio
async def test_login_success_with_email(client: AsyncClient, test_teacher: User):
    """Verify successful login using email address returns user and sets HttpOnly cookies."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher@edtech.local", "password": "TeacherPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert data["user"]["email"] == "teacher@edtech.local"
    assert data["user"]["role"] == "teacher"
    assert "access_token" in data
    assert "hashed_password" not in data["user"]
    assert "token_hash" not in data

    # Verify cookie flags
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
    assert "csrf_token" in response.cookies


@pytest.mark.asyncio
async def test_login_success_with_phone(client: AsyncClient, test_student: User):
    """Verify successful login using phone number."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "+919800000001", "password": "StudentPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["phone"] == "+919800000001"
    assert data["user"]["role"] == "student"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_teacher: User):
    """Verify that an invalid password returns 401 Unauthorized with generic error message."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher@edtech.local", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "Invalid username or password"
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Verify that a non-existent user returns 401 Unauthorized with the same generic error."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "unknown@edtech.local", "password": "SomePassword123!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "Invalid username or password"


@pytest.mark.asyncio
async def test_login_inactive_user_rejected(
    client: AsyncClient, test_inactive_student: User
):
    """Verify that inactive accounts are rejected during login."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "+919800000999", "password": "StudentPassword123!"},
    )
    assert response.status_code == 403
    data = response.json()
    assert "inactive" in data["error"].lower()


@pytest.mark.asyncio
async def test_login_validation_error(client: AsyncClient):
    """Verify that empty credentials trigger a structured 422 validation error."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "", "password": "123"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_get_me_authenticated_via_cookies(
    client: AsyncClient, test_student: User
):
    """Verify /auth/me returns current student profile when authenticated via cookie."""
    # 1. Login to establish session
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "student001@edtech.local", "password": "StudentPassword123!"},
    )
    assert login_resp.status_code == 200

    # 2. Query /auth/me (client preserves cookies from login_resp)
    me_resp = await client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["email"] == "student001@edtech.local"
    assert data["role"] == "student"
    assert data["profile"] is not None
    assert data["profile"]["roll_number"] == "2026-001"
    assert data["profile"]["grade_level"] == "Class 10"


@pytest.mark.asyncio
async def test_get_me_authenticated_via_bearer_header(
    client: AsyncClient, test_teacher: User
):
    """Verify /auth/me works when authenticated via Authorization: Bearer header."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher@edtech.local", "password": "TeacherPassword123!"},
    )
    access_token = login_resp.json()["access_token"]

    # Clear cookies on client to test header-only path
    client.cookies.clear()

    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["email"] == "teacher@edtech.local"
    assert data["role"] == "teacher"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """Verify /auth/me rejects unauthenticated requests with 401."""
    client.cookies.clear()
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_refresh_token_rotation_success(
    client: AsyncClient, test_student: User, db_session: AsyncSession
):
    """
    Verify /auth/refresh rotates the refresh token:
    - Old refresh token becomes is_revoked = True
    - New refresh token is persisted and returned in cookie
    - New access token is issued
    """
    # 1. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "student001@edtech.local", "password": "StudentPassword123!"},
    )
    assert login_resp.status_code == 200
    first_refresh_cookie = login_resp.cookies.get("refresh_token")
    first_access_token = login_resp.json()["access_token"]

    # Verify first token in database
    first_hash = hash_token(first_refresh_cookie)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == first_hash)
    res = await db_session.execute(stmt)
    token_record = res.scalars().first()
    assert token_record is not None
    assert token_record.is_revoked is False

    # 2. Rotate token
    refresh_resp = await client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    new_access_token = refresh_resp.json()["access_token"]
    new_refresh_cookie = refresh_resp.cookies.get("refresh_token")

    assert new_access_token != first_access_token
    assert new_refresh_cookie != first_refresh_cookie

    # Verify old token is revoked in database
    res = await db_session.execute(stmt)
    token_record = res.scalars().first()
    assert token_record.is_revoked is True
    assert token_record.revoked_at is not None

    # Verify new token is valid in database
    new_hash = hash_token(new_refresh_cookie)
    new_stmt = select(RefreshToken).where(RefreshToken.token_hash == new_hash)
    new_res = await db_session.execute(new_stmt)
    new_token_record = new_res.scalars().first()
    assert new_token_record is not None
    assert new_token_record.is_revoked is False


@pytest.mark.asyncio
async def test_refresh_token_reuse_detection_and_family_revocation(
    client: AsyncClient, test_student: User, db_session: AsyncSession
):
    """
    Verify security reuse detection:
    When an already-revoked refresh token is presented, the system detects a potential theft,
    revokes ALL active refresh tokens for that user, records an audit event, and returns 401.
    """
    # 1. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "student001@edtech.local", "password": "StudentPassword123!"},
    )
    first_refresh_cookie = login_resp.cookies.get("refresh_token")

    # 2. Legitimate rotation
    refresh_resp = await client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    new_refresh_cookie = refresh_resp.cookies.get("refresh_token")

    # 3. Malicious attempt: Replay the first (now revoked) refresh token
    client.cookies.set("refresh_token", first_refresh_cookie)
    reuse_resp = await client.post("/api/v1/auth/refresh")
    assert reuse_resp.status_code == 401
    assert "revoked" in reuse_resp.json()["error"].lower()

    # 4. Check database: The active token (new_refresh_cookie) MUST now also be revoked!
    new_hash = hash_token(new_refresh_cookie)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == new_hash)
    res = await db_session.execute(stmt)
    active_record = res.scalars().first()
    assert active_record.is_revoked is True

    # Check security audit event
    audit_stmt = select(AuditEvent).where(
        AuditEvent.actor_id == test_student.id,
        AuditEvent.action == "AUTH_REFRESH_TOKEN_REUSE_DETECTED",
    )
    audit_res = await db_session.execute(audit_stmt)
    audit_event = audit_res.scalars().first()
    assert audit_event is not None


@pytest.mark.asyncio
async def test_logout_and_revocation(
    client: AsyncClient, test_teacher: User, db_session: AsyncSession
):
    """Verify logout revokes the refresh token and clears all auth cookies."""
    # 1. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher@edtech.local", "password": "TeacherPassword123!"},
    )
    refresh_cookie = login_resp.cookies.get("refresh_token")
    csrf_token = login_resp.cookies.get("csrf_token")

    # 2. Logout (supplying X-CSRF-Token header because client uses cookies)
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Logout successful"

    # Verify cookies deleted
    assert client.cookies.get("access_token") is None

    # Verify refresh token is revoked in database
    token_hash = hash_token(refresh_cookie)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    res = await db_session.execute(stmt)
    record = res.scalars().first()
    assert record.is_revoked is True
