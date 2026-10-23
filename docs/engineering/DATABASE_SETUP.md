# Database Setup, Migration & Seeding Runbook

- **Engine**: PostgreSQL 15+ (tested on PostgreSQL 18.6 x86_64)
- **Driver**: `asyncpg` (runtime) / `psycopg2-binary` (Alembic sync runner)
- **Primary Architect**: `@Database_Agent`
- **Reviewed by**: `@DevOps_Agent`, `@QA_Agent`, `@Education_CTO_Agent`

---

## 1. Prerequisites

- **Python**: Version 3.11 or 3.12 (`python --version`)
- **PostgreSQL**: Version 14+ installed locally (via installer or Scoop `scoop install postgresql`)
- **Git**: (`git --version`)

*Note: Docker is NOT required for local development.*

---

## 2. Environment Configuration

Copy the sample environment file in `backend/`:
```bash
cd backend
cp .env.example .env
```

Ensure `.env` matches your local PostgreSQL credentials:
```ini
ENVIRONMENT=development
DEBUG=True

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/edtech_dev
SYNC_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/edtech_dev
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/edtech_test
TEST_SYNC_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/edtech_test

# Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# Security (Development placeholder)
JWT_SECRET_KEY=local_development_insecure_jwt_secret_key_1234567890_antigravity
JWT_ALGORITHM=HS256
```

---

## 3. Creating Local Databases

Using `psql` (or pgAdmin):
```sql
CREATE DATABASE edtech_dev;
CREATE DATABASE edtech_test;
```

---

## 4. Virtual Environment & Dependency Installation

From the `backend/` directory:
```bash
# Create virtual environment
python -m venv .venv

# Activate environment:
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# Install locked dependencies
pip install -r requirements.txt
```

---

## 5. Running Alembic Migrations

To apply all migrations to the development database:
```bash
# Apply migrations to latest revision
alembic upgrade head

# Check current revision
alembic current

# Verify zero schema drift between models and database
alembic check

# (Optional) Revert all migrations
alembic downgrade base
```

---

## 6. Seeding Synthetic Development Fixtures

An idempotent seed script creates a complete, coherent dataset containing:
- 1 Teacher (`Prof. Rajesh Sharma`, `phone: +919999900000`, password: `TeacherPassword123!`)
- 150 Synthetic Students (`student001@edtechweb.local` to `student150@edtechweb.local`, password: `StudentPassword123!`)
- 3 Cohort Batches (Morning, Evening, Olympiad)
- 1 Course ("Class 10 STEM & Reasoning Comprehensive 2026") mapped to Batches
- 3 Subjects (Mathematics, Science, Reasoning)
- 3 Chapters & 3 Lectures with attached PDF formula notes
- 1 Daily Homework Assignment with submitted and late submissions
- 1 Chapter Milestone Test with 5 MCQ questions
- 1 Resubmission attempt history (Student 105: attempt 1 requested resubmit, attempt 2 submitted)
- 1 Google Meet Scheduled Live Class with attendance telemetry and verified participation
- 1 Inbound Doubt Thread with teacher-student Q&A
- Student Health snapshot distribution:
  - 100 Students: 🟢 `ON_TRACK`
  - 30 Students: 🟡 `NEEDS_ATTENTION`
  - 20 Students: 🔴 `AT_RISK`

To execute the seed script:
```bash
python -m scripts.seed_dev_data
```
The script is safe to rerun multiple times without duplicating records or throwing constraint errors.

---

## 7. Running the Automated Test Suite

From `backend/`:
```bash
# Run all tests with verbose output
pytest -v

# Run with test coverage report
pytest --cov=app tests/
```

Test inventory:
- `tests/test_database_infra.py`: Verifies engine pool sizing, asyncpg execution, and automatic rollback on unhandled exceptions.
- `tests/test_migrations.py`: Verifies Alembic head consistency and clean migration execution.
- `tests/test_models.py`: Verifies role constraints, password/token hashing, course-to-batch M:N relationships, submission attempt uniqueness, attendance evidence vs verified participation, and MCQ answer integrity.
- `tests/test_seed.py`: Verifies seed idempotency, referential integrity, and exact 100/30/20 health triage counts.

---

## 8. Reset Procedure for Disposable Development Database

To cleanly reset a corrupted or dirty development database:
```bash
# Option A: Alembic rollback
alembic downgrade base
alembic upgrade head
python -m scripts.seed_dev_data

# Option B: Complete recreate via psql
psql -U postgres -c "DROP DATABASE edtech_dev;" -c "CREATE DATABASE edtech_dev;"
alembic upgrade head
python -m scripts.seed_dev_data
```

---

## 9. Common Setup Errors & Troubleshooting

1. **`ModuleNotFoundError: No module named 'greenlet'`**:
   - Cause: SQLAlchemy asyncio requires `greenlet` for async concurrency shims.
   - Fix: Ensure `greenlet` is installed (`pip install greenlet`).
2. **`psql: error: connection to server at localhost failed: Connection refused`**:
   - Cause: PostgreSQL server is not running on port 5432.
   - Fix: Start local service or run `pg_ctl start -D <data_dir>`.
3. **`UnicodeEncodeError: 'charmap' codec can't encode character`**:
   - Cause: Windows PowerShell default codepage cp1252 rejecting non-ASCII checkmarks.
   - Fix: Resolved in repository scripts using standard ASCII markers (`[OK]`, `[*]`).
