# Local Developer Setup Guide (CLI-First, No Docker Required)

## 1. Prerequisites

Ensure the following tools are installed on your host operating system (Windows, macOS, or Linux):
- **Python**: Version 3.11 or higher (`python --version`)
- **Node.js**: Version 18.x or 20.x (`node -v`) & `npm`
- **PostgreSQL**: Version 14+ installed locally or via lightweight local service (`psql --version`)
- **Git**: (`git --version`)

*Note: Docker is NOT required for local development.*

---

## 2. Step-by-Step Local Workspace Setup

### Step 2.1: Clone and Prepare Workspace
```bash
# In your terminal:
git clone <repo-url> EdtechWeb
cd EdtechWeb
```

### Step 2.2: Setup PostgreSQL Database
Ensure your local PostgreSQL server is running, then create the project database:
```sql
-- In psql or pgAdmin:
CREATE DATABASE edtech_dev;
CREATE USER edtech_user WITH PASSWORD 'edtech_password';
GRANT ALL PRIVILEGES ON DATABASE edtech_dev TO edtech_user;
```

### Step 2.3: Backend Setup (FastAPI)
```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment:
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run database migrations with Alembic
alembic upgrade head

# (Optional) Seed 150-student synthetic development fixtures
python -m scripts.seed_dev_data

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```
FastAPI server will be live at: `http://localhost:8000`  
Interactive OpenAPI documentation: `http://localhost:8000/docs`

### Step 2.4: Frontend Setup (React + Vite + Tailwind)
Open a second terminal window:
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start Vite development server
npm run dev
```
React application will be live at: `http://localhost:5173`

---

## 3. Environment Variables Reference

### Backend (`backend/.env`)
```ini
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=postgresql+asyncpg://edtech_user:edtech_password@localhost:5432/edtech_dev
JWT_SECRET_KEY=supersecretdevkeychangeinproduction1234567890
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Media Object Storage (Mock or Local MinIO / Cloudflare R2 test credentials)
STORAGE_PROVIDER=mock  # Options: mock, s3, r2
S3_BUCKET_NAME=edtech-media-dev
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=test_key
S3_SECRET_ACCESS_KEY=test_secret
S3_REGION=us-east-1
```

### Frontend (`frontend/.env`)
```ini
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME="EdtechWeb Academy"
```

---

## 4. Running Automated Tests

```bash
# Run backend tests with coverage
cd backend
pytest tests/ -v --cov=app

# Run frontend tests & linting
cd frontend
npm run lint
npm run test
```
