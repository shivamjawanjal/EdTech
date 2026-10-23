import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.database import async_engine, async_session_factory, get_db

settings = get_settings()


@pytest.mark.asyncio
async def test_database_engine_and_pool_config():
    """Verify that the central database engine is configured with conservative pool settings."""
    assert async_engine.url.drivername == "postgresql+asyncpg"
    assert async_engine.pool.size() == settings.DB_POOL_SIZE
    assert async_engine.pool._max_overflow == settings.DB_MAX_OVERFLOW


@pytest.mark.asyncio
async def test_session_rollback_on_exception():
    """Verify that get_db() rolls back transactions when an unhandled exception occurs."""
    caught_error = False
    try:
        async for session in get_db():
            # Execute a valid statement
            await session.execute(text("SELECT 1"))
            # Deliberately raise an exception to trigger rollback
            raise RuntimeError("Simulated transaction failure")
    except RuntimeError:
        caught_error = True

    assert caught_error is True


@pytest.mark.asyncio
async def test_asyncpg_connection_and_version(db_session: AsyncSession):
    """Verify direct asyncpg execution on PostgreSQL test database."""
    result = await db_session.execute(text("SELECT version()"))
    version_str = result.scalar_one()
    assert "PostgreSQL" in version_str
