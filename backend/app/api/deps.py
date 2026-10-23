import secrets
import uuid
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.identity import User

settings = get_settings()


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extract JWT access token with priority:
    1. HttpOnly cookie 'access_token'
    2. Authorization header 'Bearer <token>'
    """
    token = request.cookies.get("access_token")
    if token:
        return token

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


async def verify_csrf_protection(request: Request) -> None:
    """
    Verify CSRF protection for state-changing requests when authenticated via cookies.
    Requests using Authorization header Bearer token are immune to browser cross-origin auto-submission
    and are therefore exempt from CSRF double-submit token checking.
    """
    if not settings.CSRF_PROTECTION_ENABLED:
        return

    # Safe HTTP methods do not require CSRF protection
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    # Check if request relied on cookie authentication
    has_auth_cookie = "access_token" in request.cookies or "refresh_token" in request.cookies
    if not has_auth_cookie:
        return

    # Login and refresh establish or rotate credentials and are exempt from CSRF
    path = request.url.path
    if path.endswith("/auth/login") or path.endswith("/auth/refresh"):
        return

    csrf_header = request.headers.get("X-CSRF-Token")
    csrf_cookie = request.cookies.get("csrf_token")

    if not csrf_header or not csrf_cookie or not secrets.compare_digest(csrf_header, csrf_cookie):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed: Missing or invalid X-CSRF-Token header",
        )


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_csrf_protection),
) -> User:
    """
    Authenticate request and return current active user.
    Rejects missing, expired, malformed, or inactive credentials.
    """
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_type = payload.get("typ")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token purpose: Expected access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = (
        select(User)
        .where(User.id == user_uuid)
        .options(selectinload(User.profile))
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Contact instructor.",
        )

    return user


async def require_teacher(current_user: User = Depends(get_current_user)) -> User:
    """Authorize teacher-only endpoints. Rejects students with 403 Forbidden."""
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Teacher privileges required",
        )
    return current_user


async def require_student(current_user: User = Depends(get_current_user)) -> User:
    """Authorize student-only endpoints. Rejects teachers with 403 Forbidden."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Student privileges required",
        )
    return current_user
