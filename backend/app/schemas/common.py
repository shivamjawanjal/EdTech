from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    database: str
    environment: str
    version: str = "1.0.0"


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
