import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.student import StudentProfileResponse


class LoginRequest(BaseModel):
    username: str = Field(..., description="Phone number (e.g. +919800000000) or email address")
    password: str = Field(..., min_length=6, description="Plaintext password")


class UserSummary(BaseModel):
    id: uuid.UUID
    phone: str
    email: Optional[str] = None
    full_name: str
    role: str
    is_active: bool
    must_change_password: bool

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    phone: str
    email: Optional[str] = None
    full_name: str
    role: str
    is_active: bool
    must_change_password: bool
    profile: Optional[StudentProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    message: str = "Authentication successful"
    token_type: str = "bearer"
    user: UserSummary
    access_token: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
