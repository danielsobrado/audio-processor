# Updated Testing Commands and Environment Setup

## Environment Setup for Tests
```bash
# Create test environment file (already created)
cp .env.example .env.test

# Install pytest and testing dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Or with poetry
poetry add --group dev pytest pytest-asyncio pytest-cov httpx
```

## Running Tests with Proper Environment
```bash
# Run all tests with test environment
ENVIRONMENT=testing pytest

# Run tests with coverage
ENVIRONMENT=testing pytest --cov=app --cov-report=html

# Run specific test categories
ENVIRONMENT=testing pytest -m unit          # Unit tests only
ENVIRONMENT=testing pytest -m integration   # Integration tests only
ENVIRONMENT=testing pytest -m "not slow"    # Skip slow tests

# Run with verbose output
ENVIRONMENT=testing pytest -v

# Run specific test file
ENVIRONMENT=testing pytest tests/unit/test_environment.py

# Run and stop on first failure
ENVIRONMENT=testing pytest -x
```

## Test Environment Features
- **Isolated test database** (SQLite in-memory)
- **Separate Redis database** (DB 15)
- **Mocked external services** (Celery, Deepgram)
- **Fast model settings** (tiny WhisperX model)
- **Debug logging** enabled
- **Disabled external APIs** for faster tests

## Test Configuration Files
- **`.env.test`** - Test environment variables
- **`pyproject.toml`** - Pytest configuration
- **`tests/conftest.py`** - Shared fixtures and setup
- **`tests/unit/test_environment.py`** - Environment testing

## Key Testing Improvements
1. **Settings cache clearing** between tests
2. **Dynamic environment file** selection (.env vs .env.test)
3. **Test-specific settings** function without caching
4. **Comprehensive fixtures** for mocking services
5. **Proper async test** support

## Environment Variable Loading Order
1. OS environment variables (highest priority)
2. `.env.test` file (in test environment)
3. `.env` file (in development/production)
4. YAML configuration files
5. Default values (lowest priority)

## Debugging Test Environment Issues
```bash
# Verify environment loading
ENVIRONMENT=testing python -c "from app.config.settings import get_settings; print(get_settings().environment)"

# Check which env file is loaded
ENVIRONMENT=testing python -c "import os; print('Test env:', os.getenv('ENVIRONMENT'))"

# Test settings without cache
ENVIRONMENT=testing python -c "from app.config.settings import get_test_settings; print(get_test_settings().debug)"
```
