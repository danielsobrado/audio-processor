# Suggested Commands for Development

## Windows System Commands
- **List files**: `dir` or `ls` (if using PowerShell/WSL)
- **Navigate**: `cd path\to\directory`
- **Find files**: `findstr` or `Select-String` (PowerShell)
- **Git operations**: `git status`, `git add .`, `git commit -m "message"`

## Environment Setup
```bash
# Copy environment variables
copy .env.example .env

# Install dependencies (Poetry recommended)
poetry install

# Or with pip
pip install -r requirements.txt

# Start database and Redis services
docker-compose -f deployment/docker/docker-compose.yml up -d db redis

# Run database migrations
poetry run alembic upgrade head
# OR: alembic upgrade head
```

## Development Commands
```bash
# Start FastAPI development server
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# OR: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Celery worker (separate terminal)
poetry run celery -A app.workers.celery_app worker -l info
# OR: celery -A app.workers.celery_app worker -l info

# Start all services with Docker Compose
docker-compose -f deployment/docker/docker-compose.yml up --build -d
```

## Testing Commands

### Using Test Scripts (Recommended)
```bash
# Windows - First time setup
scripts\setup-tests.bat

# Windows - Run tests
scripts\run-tests.bat               # All tests
scripts\run-tests.bat unit          # Unit tests only
scripts\run-tests.bat coverage      # With coverage
scripts\test-quick.bat              # Fast tests only

# WSL/Linux - First time setup
./scripts/setup-tests.sh

# WSL/Linux - Run tests  
./scripts/run-tests.sh              # All tests
./scripts/run-tests.sh unit         # Unit tests only
./scripts/run-tests.sh coverage     # With coverage
./scripts/test-quick.sh             # Fast tests only

# PowerShell
.\scripts\run-tests.ps1             # All tests
.\scripts\run-tests.ps1 coverage    # With coverage
```

### Direct pytest Commands
```bash
# Run all tests
poetry run pytest
# OR: pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/unit/test_audio_processor.py

# Run integration tests only
poetry run pytest tests/integration/

# Run environment tests
poetry run pytest tests/unit/test_environment.py
```

## Code Quality Commands
```bash
# Format code (if using black/isort - not explicitly configured)
black app/ tests/
isort app/ tests/

# Lint code (if using flake8/pylint - not explicitly configured)
flake8 app/ tests/
pylint app/
```

## API Testing
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/api/v1/health

## File Organization
- **Test scripts**: `scripts/` folder (run-tests.*, test-quick.*, setup-tests.*)
- **Test documentation**: `tests/TESTING.md`
- **Environment config**: `.env.test` (root directory)
- **Test files**: `tests/unit/`, `tests/integration/`