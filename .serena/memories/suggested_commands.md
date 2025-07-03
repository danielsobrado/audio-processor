# Suggested Commands for Development (uv-based)

## Windows System Commands
- **List files**: `dir` or `ls` (if using PowerShell/WSL)
- **Navigate**: `cd path\to\directory`
- **Find files**: `findstr` or `Select-String` (PowerShell)
- **Git operations**: `git status`, `git add .`, `git commit -m "message"`

## Environment Setup
```bash
# Create .env file from example
copy .env.example .env

# Install dependencies with uv (recommended)
uv sync --dev

# Or with pip fallback
pip install -r requirements.txt

# Start database and Redis services
docker-compose -f deployment/docker/docker-compose.yml up -d db redis

# Run database migrations
uv run alembic upgrade head
# OR: alembic upgrade head
```

## Development Commands
```bash
# Start FastAPI development server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# OR: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Celery worker (separate terminal)
uv run celery -A app.workers.celery_app worker -l info
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

### Direct uv Commands
```bash
# Run all tests
uv run pytest
# OR: pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/unit/test_audio_processor.py

# Run integration tests only
uv run pytest tests/integration/

# Run environment tests
uv run pytest tests/unit/test_environment.py
```

## Code Quality Commands
```bash
# Format code with uv
uv run black app/ tests/
uv run isort app/ tests/

# Lint code with uv
uv run flake8 app/ tests/
uv run pyright app/

# All quality checks
uv run black . && uv run isort . && uv run flake8 . && uv run pyright .
```

## Dependency Management with uv
```bash
# Add new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Remove dependency
uv remove package-name

# Update dependencies
uv sync

# Install dependencies
uv sync --dev

# Show dependency tree
uv tree

# Lock dependencies
uv lock
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
- **Project config**: `pyproject.toml` (uv + pytest + coverage configuration)

## uv Installation
```bash
# Install uv (if not already installed)
# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```