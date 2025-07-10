# Test Scripts Documentation

This directory contains comprehensive test runner scripts for both Windows and WSL/Linux environments.

## Quick Start

### Windows (Command Prompt)
```cmd
# Setup test environment (first time only)
scripts\setup-tests.bat

# Run all tests
scripts\run-tests.bat

# Run quick tests
scripts\test-quick.bat
```

### Windows (PowerShell)
```powershell
# Setup test environment (first time only)
.\scripts\setup-tests.bat

# Run all tests
.\scripts\run-tests.ps1

# Run with coverage
.\scripts\run-tests.ps1 coverage
```

### WSL/Linux
```bash
# Setup test environment (first time only)
./scripts/setup-tests.sh

# Run all tests
./scripts/run-tests.sh

# Run quick tests
./scripts/test-quick.sh
```

## Available Scripts

### Setup Scripts
- **`scripts/setup-tests.bat`** / **`scripts/setup-tests.sh`** - First-time environment setup
  - Creates `.env.test` from `.env.example`
  - Installs dependencies (Poetry or pip)
  - Makes scripts executable (Linux/WSL)
  - Runs environment validation tests

### Main Test Runners
- **`scripts/run-tests.bat`** - Windows Command Prompt test runner
- **`scripts/run-tests.sh`** - WSL/Linux bash test runner  
- **`scripts/run-tests.ps1`** - Windows PowerShell test runner

### Quick Test Scripts
- **`scripts/test-quick.bat`** / **`scripts/test-quick.sh`** - Fast tests only (excludes slow tests)

## Test Types

All main test runners support these test types:

| Type | Description |
|------|-------------|
| `all` | Run all tests (default) |
| `unit` | Run unit tests only |
| `integration` | Run integration tests only |
| `coverage` | Run tests with coverage report |
| `fast` | Run tests excluding slow ones |
| `env` | Run environment configuration tests |
| `watch` | Run tests in watch mode |
| `debug` | Run tests with verbose debug output |
| `help` | Show help message |

## Examples

### Windows Command Prompt
```cmd
scripts\run-tests.bat                    # All tests
scripts\run-tests.bat unit               # Unit tests only
scripts\run-tests.bat coverage           # With coverage report
scripts\run-tests.bat fast               # Fast tests only
scripts\run-tests.bat debug              # Debug mode
scripts\run-tests.bat -v tests/unit/     # Custom pytest options
```

### PowerShell
```powershell
.\scripts\run-tests.ps1                  # All tests
.\scripts\run-tests.ps1 unit             # Unit tests only
.\scripts\run-tests.ps1 coverage         # With coverage report
.\scripts\run-tests.ps1 help             # Show help
```

### WSL/Linux
```bash
./scripts/run-tests.sh                   # All tests
./scripts/run-tests.sh unit              # Unit tests only
./scripts/run-tests.sh coverage          # With coverage report
./scripts/run-tests.sh fast              # Fast tests only
./scripts/run-tests.sh watch             # Watch mode
./scripts/run-tests.sh help              # Show help
```

## Environment Setup

### Automatic Setup
Run the setup script for your platform:
```bash
# Windows
scripts\setup-tests.bat

# WSL/Linux  
./scripts/setup-tests.sh
```

### Manual Setup
1. **Copy environment file:**
   ```bash
   cp .env.example .env.test
   ```

2. **Install dependencies:**
   ```bash
   # With Poetry (recommended)
   poetry install
   
   # With pip
   pip install pytest pytest-asyncio pytest-cov httpx
   pip install -r requirements.txt
   ```

3. **Make scripts executable (WSL/Linux only):**
   ```bash
   chmod +x scripts/*.sh
   ```

## Test Configuration

### Environment Variables
Tests automatically use the `testing` environment with these settings:
- **Database**: SQLite in-memory for isolation
- **Redis**: Separate database (DB 15)
- **Celery**: In-memory broker for speed
- **External APIs**: Mocked/disabled
- **Models**: Smallest/fastest configurations
- **Authentication**: JWT signature verification disabled

#### Test Dependencies
End-to-end tests require these services to be running:
- **Redis** (localhost:6379) - For caching and Celery
- **Neo4j** (localhost:7687) - For graph storage
  - Username: `neo4j`
  - Password: `devpassword` (as configured in `.env.test`)

Start services with Docker:
```bash
# Redis
docker run -d --name redis-test -p 6379:6379 redis:latest

# Neo4j
docker run -d --name neo4j-test \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/devpassword \
  neo4j:latest
```

### Pytest Configuration
Settings are in `pyproject.toml`:
- **Test discovery**: `test_*.py` files in `tests/` directory
- **Async support**: Automatic async test detection
- **Markers**: `slow`, `integration`, `unit`
- **Coverage**: Source code analysis with exclusions

## Coverage Reports

When running with coverage, reports are generated in:
- **Terminal**: Summary during test run
- **HTML**: `htmlcov/index.html` (auto-opens on Windows)

Coverage includes:
- **Line coverage** of all app code
- **Missing lines** highlighted
- **Exclusions** for test files and migration scripts

### Troubleshooting

### Common Issues

1. **".env.test not found"**
   ```bash
   cp .env.example .env.test
   ```

2. **"pytest not found"**
   ```bash
   pip install pytest pytest-asyncio pytest-cov httpx
   ```

3. **"Permission denied" (WSL/Linux)**
   ```bash
   chmod +x scripts/*.sh
   ```

4. **PowerShell execution policy**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

5. **Diarization model errors when using Celery**
   If you see errors like "Could not download 'pyannote/segmentation' model" when running Celery commands, you're likely not using the test environment:
   
   ```powershell
   # ❌ Wrong - uses default environment (tries to load diarization)
   celery -A app.workers.celery_app inspect active
   
   # ✅ Correct - uses test environment (diarization disabled)
   uv run --env-file .env.test celery -A app.workers.celery_app inspect active
   ```
   
   Always use `--env-file .env.test` with Celery commands during testing.

6. **Celery "No nodes replied within time constraint" error**
   This error when running `celery inspect active` is common with in-memory brokers and doesn't indicate a problem:
   
   ```powershell
   # This may show "No nodes replied" but is normal with memory:// broker
   uv run --env-file .env.test celery -A app.workers.celery_app inspect active
   ```
   
   The worker is still functional if you see "celery@HOSTNAME ready" in the worker logs.

7. **Jobs stuck in "pending" status**
   If end-to-end tests show jobs stuck in pending status, this usually means the Celery worker is not running. Follow these steps:
   
   **Step 1: Check if worker is running**
   ```powershell
   uv run --env-file .env.test celery -A app.workers.celery_app inspect active
   ```
   If you see "Error: No nodes replied within time constraint", the worker is not running.
   
   **Step 2: Start the Celery worker (Windows)**
   ```powershell
   # Start worker with Windows-compatible settings
   uv run --env-file .env.test celery -A app.workers.celery_app worker --loglevel=info --concurrency=1 --pool=solo
   ```
   
   **Step 3: Verify worker is ready**
   Look for this message in the worker logs:
   ```
   [2025-01-01 12:00:00,000: INFO/MainProcess] celery@HOSTNAME ready.
   ```
   
   **Step 4: Run your E2E test in a separate terminal**
   ```powershell
   uv run --env-file .env.test python test_e2e_complete.py
   ```
   
   **Additional checks:**
   - Server and worker use the same broker configuration (both should use `memory://localhost//`)
   - Both server and worker use the same environment file (`.env.test`)
   - Try the manual processing test if worker issues persist: `uv run --env-file .env.test python test_e2e_real_audio.py` (has fallback processing)

8. **Windows Celery permission errors**
   On Windows, you may see permission errors like "PermissionError: [WinError 5] Access is denied" when using the default `prefork` concurrency model:
   
   ```
   [ERROR/SpawnPoolWorker-1] Pool process error: PermissionError(13, 'Access is denied', None, 5, None)
   BrokenPipeError: [WinError 109] The pipe has been ended
   OSError: [WinError 6] The handle is invalid
   ```
   
   **Solution**: Use the `solo` concurrency model which works better on Windows:
   
   ```powershell
   # ❌ Default (may fail on Windows)
   uv run --env-file .env.test celery -A app.workers.celery_app worker --loglevel=info
   
   # ✅ Windows-compatible
   uv run --env-file .env.test celery -A app.workers.celery_app worker --loglevel=info --concurrency=1 --pool=solo
   ```
   
   The `solo` pool runs tasks in the main process rather than spawning separate worker processes, avoiding Windows-specific permission issues.
```