from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, verify_csrf_protection
from app.core.config import get_settings
from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.database import get_db
from app.models.identity import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserProfileResponse,
    UserSummary,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import auth_service, extract_client_ip

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user with phone/email and password.
    Issues short-lived access token and 7-day refresh token in HttpOnly cookies.
    """
    ip_address = extract_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    user = await auth_service.authenticate_user(
        db, username=login_data.username, password=login_data.password
    )

    access_token, refresh_token, csrf_token = await auth_service.create_session(
        db, user=user, user_agent=user_agent, ip_address=ip_address
    )

    set_auth_cookies(
        response=response,
        access_token=access_token,
        refresh_token=refresh_token,
        csrf_token=csrf_token,
        settings=settings,
    )

    return TokenResponse(
        message="Login successful",
        token_type="bearer",
        user=UserSummary.model_validate(user),
        access_token=access_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Rotate refresh token and issue a fresh access token.
    Extracts refresh token from HttpOnly cookie.
    Detects reuse and revokes compromised token families.
    """
    raw_refresh = request.cookies.get("refresh_token")
    if not raw_refresh:
        # Check Authorization header as fallback
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            raw_refresh = auth_header[7:].strip()

    if not raw_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required in cookie or Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ip_address = extract_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    new_access, new_refresh, new_csrf, user = await auth_service.rotate_refresh_token(
        db,
        raw_refresh_token=raw_refresh,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    set_auth_cookies(
        response=response,
        access_token=new_access,
        refresh_token=new_refresh,
        csrf_token=new_csrf,
        settings=settings,
    )

    return TokenResponse(
        message="Token refreshed successfully",
        token_type="bearer",
        user=UserSummary.model_validate(user),
        access_token=new_access,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_csrf_protection),
) -> MessageResponse:
    """
    Revoke current refresh token and clear all auth cookies.
    Protected by CSRF verification when cookie-authenticated.
    """
    raw_refresh = request.cookies.get("refresh_token")
    ip_address = extract_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    await auth_service.revoke_session(
        db,
        raw_refresh_token=raw_refresh,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    clear_auth_cookies(response=response, settings=settings)

    return MessageResponse(
        message="Logout successful",
        detail="Active session and credentials cleared",
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    """
    Get profile information for the authenticated user.
    Accessible by both Teachers and Students.
    """
    return UserProfileResponse.model_validate(current_user)
