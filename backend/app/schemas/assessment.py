import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------
# Assignments & Submissions
# -------------------------------------------------------------------------


class AssignmentCreate(BaseModel):
    lecture_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=250)
    instructions: str = Field(..., min_length=1)
    max_marks: int = Field(default=10, gt=0, le=1000)
    deadline: datetime
    allow_late_submission: bool = True
    late_deadline: Optional[datetime] = None
    is_published: bool = True


class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=250)
    instructions: Optional[str] = Field(default=None, min_length=1)
    max_marks: Optional[int] = Field(default=None, gt=0, le=1000)
    deadline: Optional[datetime] = None
    allow_late_submission: Optional[bool] = None
    late_deadline: Optional[datetime] = None
    is_published: Optional[bool] = None


class SubmissionAttachmentResponse(BaseSchema):
    id: uuid.UUID
    s3_key: str
    file_name: str
    file_size_bytes: int
    mime_type: str
    page_order: int
    created_at: datetime


class SubmissionCreateRequest(BaseModel):
    student_content: Optional[str] = None


class SubmissionGradeRequest(BaseModel):
    obtained_marks: Decimal = Field(..., ge=0)
    teacher_feedback: Optional[str] = None
    is_released: bool = False


class SubmissionResponse(BaseSchema):
    id: uuid.UUID
    assignment_id: uuid.UUID
    student_id: uuid.UUID
    attempt_number: int
    is_latest: bool
    status: str
    student_content: Optional[str] = None
    submitted_at: datetime
    is_evaluated: bool
    obtained_marks: Optional[Decimal] = None
    teacher_feedback: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    is_released: bool
    released_at: Optional[datetime] = None
    attachments: List[SubmissionAttachmentResponse] = []
    student_name: Optional[str] = None
    student_email: Optional[str] = None


class AssignmentResponse(BaseSchema):
    id: uuid.UUID
    lecture_id: uuid.UUID
    title: str
    instructions: str
    max_marks: int
    deadline: datetime
    allow_late_submission: bool
    late_deadline: Optional[datetime] = None
    is_published: bool
    created_at: datetime
    updated_at: datetime
    course_id: Optional[uuid.UUID] = None
    course_title: Optional[str] = None
    lecture_title: Optional[str] = None
    submission_count: int = 0
    evaluated_count: int = 0
    pending_count: int = 0
    missing_count: int = 0
    my_submission: Optional[SubmissionResponse] = None


class AssignmentSubmissionQueueResponse(BaseModel):
    assignment: AssignmentResponse
    total_enrolled: int
    submitted_count: int
    evaluated_count: int
    pending_count: int
    late_count: int
    missing_count: int
    submissions: List[SubmissionResponse]


# -------------------------------------------------------------------------
# Timed MCQ Tests & Questions
# -------------------------------------------------------------------------


class OptionItem(BaseModel):
    key: str  # e.g. "A", "B", "C", "D"
    text: str


class QuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=1)
    options: Any  # List of OptionItem dicts or key-val dict
    correct_option: str = Field(..., pattern="^[A-D]$")
    marks: int = Field(default=1, gt=0, le=100)
    negative_marks: Decimal = Field(default=Decimal("0.00"), ge=0, le=50)
    solution_explanation: Optional[str] = None
    order_index: int = 0


class QuestionResponse(BaseSchema):
    id: uuid.UUID
    test_id: uuid.UUID
    question_text: str
    question_image_s3_key: Optional[str] = None
    options: Any
    correct_option: Optional[str] = None  # None if redacted for student
    marks: int
    negative_marks: Decimal
    solution_explanation: Optional[str] = None  # None if redacted for student
    order_index: int


class TestCreate(BaseModel):
    chapter_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=250)
    description: Optional[str] = None
    duration_minutes: int = Field(..., gt=0, le=180)
    pass_percentage: int = Field(default=40, ge=0, le=100)
    deadline: datetime
    max_attempts: int = Field(default=1, ge=1, le=10)
    is_published: bool = False
    solutions_released_at: Optional[datetime] = None
    results_released_at: Optional[datetime] = None


class TestUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=250)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(default=None, gt=0, le=180)
    pass_percentage: Optional[int] = Field(default=None, ge=0, le=100)
    deadline: Optional[datetime] = None
    max_attempts: Optional[int] = Field(default=None, ge=1, le=10)
    is_published: Optional[bool] = None
    solutions_released_at: Optional[datetime] = None
    results_released_at: Optional[datetime] = None


class TestResponse(BaseSchema):
    id: uuid.UUID
    chapter_id: uuid.UUID
    title: str
    description: Optional[str] = None
    duration_minutes: int
    total_marks: int
    pass_percentage: int
    deadline: datetime
    max_attempts: int
    is_published: bool
    solutions_released_at: Optional[datetime] = None
    results_released_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    chapter_title: Optional[str] = None
    course_id: Optional[uuid.UUID] = None
    course_title: Optional[str] = None
    question_count: int = 0
    my_attempts_count: int = 0
    my_best_score: Optional[Decimal] = None
    active_attempt_id: Optional[uuid.UUID] = None


class TestDetailResponse(TestResponse):
    questions: List[QuestionResponse] = []


class AttemptStartResponse(BaseModel):
    attempt_id: uuid.UUID
    test_id: uuid.UUID
    attempt_number: int
    started_at: datetime
    expires_at: datetime
    remaining_seconds: int
    is_resumed: bool = False
    saved_answers: dict[str, str] = {}  # str(question_id) -> selected_option


class SaveAnswerRequest(BaseModel):
    question_id: uuid.UUID
    selected_option: Optional[str] = Field(default=None, pattern="^[A-D]?$")

    @field_validator("selected_option")
    @classmethod
    def empty_str_to_none(cls, v: Optional[str]) -> Optional[str]:
        if v == "":
            return None
        return v


class AnswerDetailItem(BaseModel):
    question_id: uuid.UUID
    selected_option: Optional[str] = None
    correct_option: Optional[str] = None  # None if solutions not released
    is_correct: Optional[bool] = None     # None if solutions not released
    marks_awarded: Optional[Decimal] = None
    solution_explanation: Optional[str] = None


class AttemptResultResponse(BaseModel):
    attempt_id: uuid.UUID
    test_id: uuid.UUID
    attempt_number: int
    is_completed: bool
    score: Decimal
    total_marks: int
    percentage: Decimal
    passed: bool
    total_questions: int
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    started_at: datetime
    submitted_at: Optional[datetime] = None
    solutions_released: bool
    results_released: bool = True
    results_released_at: Optional[datetime] = None
    answers: Optional[List[AnswerDetailItem]] = None
