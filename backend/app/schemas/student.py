from typing import Optional
from pydantic import BaseModel, ConfigDict


class StudentProfileResponse(BaseModel):
    roll_number: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    school_name: Optional[str] = None
    grade_level: Optional[str] = None
    target_exam: Optional[str] = None
    teacher_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
