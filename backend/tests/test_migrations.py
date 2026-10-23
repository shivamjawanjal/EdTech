import pytest
from alembic import command
from alembic.config import Config
from app.core.config import get_settings

settings = get_settings()


def test_alembic_migration_head_consistency():
    """Verify that Alembic configuration points to valid script directory and current head exists."""
    from pathlib import Path
    alembic_ini_path = str(Path(__file__).parent.parent / "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", settings.TEST_SYNC_DATABASE_URL)

    # Check that upgrade head runs cleanly without raising CommandError
    try:
        command.upgrade(alembic_cfg, "head")
        assert True
    except Exception as e:
        pytest.fail(f"Alembic upgrade head failed: {e}")
