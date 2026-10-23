from app.models.base import Base, TimestampMixin, utc_now

# Domain 1: Identity & Authentication (3 tables)
from app.models.identity import User, StudentProfile, RefreshToken

# Domain 2: Enrolment & Cohorts (4 tables)
from app.models.enrolment import Batch, Course, CourseBatch, Enrollment

# Domain 3 & 4: Curriculum Hierarchy & Media (4 tables)
from app.models.curriculum import Subject, Chapter, Lecture, LectureNote

# Domain 5: Telemetry & Heartbeat (2 tables)
from app.models.telemetry import VideoProgress, VideoWatchSession

# Domain 6 & 7: Assessment & Objective Tests (7 tables)
from app.models.assessment import (
    Assignment,
    Submission,
    SubmissionAttachment,
    Test,
    Question,
    TestAttempt,
    TestAnswer,
)

# Domain 8, 9 & 10: Communication, Doubts, Live & Notifications (6 tables)
from app.models.communication import (
    DoubtThread,
    DoubtMessage,
    LiveSession,
    LiveAttendanceRecord,
    Announcement,
    Notification,
)

# Domain 11 & 12: Analytics & Security Audit (3 tables)
from app.models.analytics import (
    StudentHealthSummary,
    StudentActivity,
    AuditEvent,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "utc_now",
    # Domain 1
    "User",
    "StudentProfile",
    "RefreshToken",
    # Domain 2
    "Batch",
    "Course",
    "CourseBatch",
    "Enrollment",
    # Domain 3 & 4
    "Subject",
    "Chapter",
    "Lecture",
    "LectureNote",
    # Domain 5
    "VideoProgress",
    "VideoWatchSession",
    # Domain 6 & 7
    "Assignment",
    "Submission",
    "SubmissionAttachment",
    "Test",
    "Question",
    "TestAttempt",
    "TestAnswer",
    # Domain 8, 9 & 10
    "DoubtThread",
    "DoubtMessage",
    "LiveSession",
    "LiveAttendanceRecord",
    "Announcement",
    "Notification",
    # Domain 11 & 12
    "StudentHealthSummary",
    "StudentActivity",
    "AuditEvent",
]
