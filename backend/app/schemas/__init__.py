from app.schemas.common import ErrorResponse, HealthResponse, MessageResponse
from app.schemas.student import StudentProfileResponse
from app.schemas.auth import (
    LoginRequest,
    UserSummary,
    UserProfileResponse,
    TokenResponse,
)

__all__ = [
    "ErrorResponse",
    "HealthResponse",
    "MessageResponse",
    "StudentProfileResponse",
    "LoginRequest",
    "UserSummary",
    "UserProfileResponse",
    "TokenResponse",
]
