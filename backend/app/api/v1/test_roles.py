from fastapi import APIRouter, Depends
from app.api.deps import require_student, require_teacher
from app.models.identity import User
from app.schemas.auth import UserSummary

router = APIRouter(prefix="/roles", tags=["Role Verification"])


@router.get("/teacher-only", response_model=UserSummary)
async def teacher_dashboard_endpoint(
    current_user: User = Depends(require_teacher),
) -> UserSummary:
    """Restricted endpoint accessible exclusively to users with the teacher role."""
    return UserSummary.model_validate(current_user)


@router.get("/student-only", response_model=UserSummary)
async def student_portal_endpoint(
    current_user: User = Depends(require_student),
) -> UserSummary:
    """Restricted endpoint accessible exclusively to users with the student role."""
    return UserSummary.model_validate(current_user)
