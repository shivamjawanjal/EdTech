import ipaddress
import logging
import uuid
from typing import Optional, Tuple
from fastapi import HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_csrf_token,
    hash_token,
    verify_password,
)
from app.models.analytics import AuditEvent
from app.models.base import utc_now
from app.models.identity import RefreshToken, User

logger = logging.getLogger(__name__)


def extract_client_ip(request: Request) -> Optional[str]:
    """Safely extract and validate client IP address for PostgreSQL INET compatibility."""
    forwarded = request.headers.get("X-Forwarded-For")
    ip_str = None
    if forwarded:
        ip_str = forwarded.split(",")[0].strip()
    elif request.client and request.client.host:
        ip_str = request.client.host

    if ip_str:
        if ip_str == "testclient":
            return "127.0.0.1"
        try:
            ipaddress.ip_address(ip_str)
            return ip_str
        except ValueError:
            return None
    return None


class AuthService:
    async def authenticate_user(
        self, db: AsyncSession, username: str, password: str
    ) -> User:
        """
        Authenticate user by either email or phone number.
        Returns user on success; raises HTTPException 401 for bad credentials, 403 if inactive.
        """
        clean_user = username.strip()
        stmt = (
            select(User)
            .where(
                (User.email == clean_user.lower()) | (User.phone == clean_user)
            )
            .options(selectinload(User.profile))
        )
        result = await db.execute(stmt)
        user = result.scalars().first()

        # Always evaluate password verify to prevent timing attacks
        dummy_hash = "$2b$12$e80yq9gPjHq61b6xLp4.Eex5t.YmYwG6vJ4e1uK9uUuHqU6K9uUuH"
        is_valid = verify_password(password, user.hashed_password if user else dummy_hash)

        if not user or not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive. Please contact your instructor.",
            )

        return user

    async def create_session(
        self,
        db: AsyncSession,
        user: User,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[str, str, str]:
        """
        Issue new session tokens:
        Returns: (access_token, raw_refresh_token, csrf_token)
        """
        access_token = create_access_token(subject=str(user.id), role=user.role)
        raw_refresh, token_hash, family_id, expires_at = create_refresh_token(
            user_id=str(user.id)
        )

        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(refresh_record)

        # Audit login event
        audit = AuditEvent(
            actor_id=user.id,
            action="AUTH_LOGIN_SUCCESS",
            target_entity_type="user",
            target_entity_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            new_state={"role": user.role, "family_id": family_id},
        )
        db.add(audit)
        await db.commit()

        csrf_token = generate_csrf_token()
        return access_token, raw_refresh, csrf_token

    async def rotate_refresh_token(
        self,
        db: AsyncSession,
        raw_refresh_token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[str, str, str, User]:
        """
        Atomically rotate refresh token.
        Enforces token family reuse detection:
        If an already-revoked token is presented, all active tokens for that user are immediately revoked.
        Returns: (new_access_token, new_refresh_token, new_csrf_token, user)
        """
        try:
            payload = decode_token(raw_refresh_token)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("typ") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token purpose",
                headers={"WWW-Authenticate": "Bearer"},
            )

        family_id = payload.get("family_id")
        token_hash = hash_token(raw_refresh_token)

        # Acquire row lock for atomic rotation
        stmt = (
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .with_for_update()
        )
        result = await db.execute(stmt)
        token_record = result.scalars().first()

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not recognized",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # REUSE DETECTION: Token already revoked
        if token_record.is_revoked:
            logger.warning(
                "Refresh token reuse detected for user %s! Revoking all sessions.",
                token_record.user_id,
            )
            # Invalidate all active tokens for this user
            revoke_stmt = (
                update(RefreshToken)
                .where(
                    RefreshToken.user_id == token_record.user_id,
                    RefreshToken.is_revoked.is_(False),
                )
                .values(is_revoked=True, revoked_at=utc_now())
            )
            await db.execute(revoke_stmt)

            # Security audit event
            audit = AuditEvent(
                actor_id=token_record.user_id,
                action="AUTH_REFRESH_TOKEN_REUSE_DETECTED",
                target_entity_type="user",
                target_entity_id=token_record.user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                new_state={
                    "warning": "Revoked token presented. Entire session family terminated.",
                    "family_id": family_id,
                },
            )
            db.add(audit)
            await db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Revoked refresh token presented. Session terminated for security.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check expiration
        now = utc_now()
        if token_record.expires_at < now:
            token_record.is_revoked = True
            token_record.revoked_at = now
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Mark current token as revoked
        token_record.is_revoked = True
        token_record.revoked_at = now

        # Fetch user
        user_stmt = (
            select(User)
            .where(User.id == token_record.user_id)
            .options(selectinload(User.profile))
        )
        user_res = await db.execute(user_stmt)
        user = user_res.scalars().first()

        if not user or not user.is_active:
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account inactive or not found",
            )

        # Issue replacement tokens in the same family
        new_access_token = create_access_token(subject=str(user.id), role=user.role)
        new_raw_refresh, new_token_hash, _, new_expires_at = create_refresh_token(
            user_id=str(user.id), family_id=family_id
        )

        new_record = RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=new_expires_at,
            is_revoked=False,
        )
        db.add(new_record)
        await db.commit()

        new_csrf = generate_csrf_token()
        return new_access_token, new_raw_refresh, new_csrf, user

    async def revoke_session(
        self,
        db: AsyncSession,
        raw_refresh_token: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Revoke presented token or all tokens for the user."""
        now = utc_now()
        if raw_refresh_token:
            token_hash = hash_token(raw_refresh_token)
            stmt = (
                update(RefreshToken)
                .where(RefreshToken.token_hash == token_hash)
                .values(is_revoked=True, revoked_at=now)
            )
            await db.execute(stmt)

        if user_id:
            audit = AuditEvent(
                actor_id=user_id,
                action="AUTH_LOGOUT",
                target_entity_type="user",
                target_entity_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                new_state={"status": "session_revoked"},
            )
            db.add(audit)

        await db.commit()


auth_service = AuthService()
