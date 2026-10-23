import asyncio
import os
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings
from app.models import Base

settings = get_settings()

# Use TEST_DATABASE_URL for running automated tests
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
    Rolls back transaction at the end of each test to maintain state cleanliness.
    """
    async with test_async_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        yield session

        await session.close()
        await transaction.rollback()
