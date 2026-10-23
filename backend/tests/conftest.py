import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models.identity import StudentProfile, User

settings = get_settings()

test_async_engine = create_async_engine(
    settings.TEST_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

test_session_factory = async_sessionmaker(
    bind=test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an isolated transactional database session for each test function.
    Uses a savepoint so that internal application session commits only release the savepoint,
    and the outer transaction rollback reliably wipes all test changes.
    """
    async with test_async_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        yield session

        await session.close()
        await transaction.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX AsyncClient with database session dependency override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_teacher(db_session: AsyncSession) -> User:
    """Create a verified teacher user for testing."""
    teacher = User(
        phone="+919800000000",
        email="teacher@edtech.local",
        hashed_password=hash_password("TeacherPassword123!"),
        full_name="Prof. Rajesh Sharma",
        role="teacher",
        is_active=True,
    )
    db_session.add(teacher)
    await db_session.flush()
    return teacher


@pytest_asyncio.fixture(scope="function")
async def test_student(db_session: AsyncSession) -> User:
    """Create a verified student user with profile for testing."""
    student = User(
        phone="+919800000001",
        email="student001@edtech.local",
        hashed_password=hash_password("StudentPassword123!"),
        full_name="Student 001",
        role="student",
        is_active=True,
    )
    db_session.add(student)
    await db_session.flush()

    profile = StudentProfile(
        user_id=student.id,
        roll_number="2026-001",
        parent_name="Parent 001",
        parent_phone="+919800000101",
        school_name="Central Academy",
        grade_level="Class 10",
        target_exam="Board Exam",
    )
    db_session.add(profile)
    await db_session.flush()
    return student


@pytest_asyncio.fixture(scope="function")
async def test_inactive_student(db_session: AsyncSession) -> User:
    """Create an inactive student user for testing access denial."""
    inactive = User(
        phone="+919800000999",
        email="inactive@edtech.local",
        hashed_password=hash_password("StudentPassword123!"),
        full_name="Inactive Student",
        role="student",
        is_active=False,
    )
    db_session.add(inactive)
    await db_session.flush()
    return inactive
