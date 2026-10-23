from fastapi import Response
from app.core.config import Settings


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    settings: Settings,
) -> None:
    """
    Set HttpOnly authentication cookies and CSRF double-submit cookie.
    Follows OWASP standards:
    - access_token: HttpOnly, SameSite configured via settings, path="/"
    - refresh_token: HttpOnly, SameSite=Strict, path scoped to /api/v1/auth
    - csrf_token: Non-HttpOnly (readable by SPA client for X-CSRF-Token header)
    """
    access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

    # 1. Access Token Cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=access_max_age,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )

    # 2. Refresh Token Cookie (strictly scoped to auth path)
    auth_path = f"{settings.API_V1_STR}/auth"
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
        max_age=refresh_max_age,
        path=auth_path,
        domain=settings.COOKIE_DOMAIN,
    )

    # 3. CSRF Token Cookie (Readable by SPA JavaScript)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=refresh_max_age,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    """Clear all authentication and CSRF cookies on logout or revocation."""
    auth_path = f"{settings.API_V1_STR}/auth"
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key="refresh_token",
        path=auth_path,
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite="strict",
    )
    response.delete_cookie(
        key="csrf_token",
        path="/",
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=False,
        samesite=settings.COOKIE_SAMESITE,
    )
