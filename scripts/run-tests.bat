@echo off
REM Audio Processor - Test Runner for Windows
REM Usage: run-tests.bat [test-type] [options]

setlocal EnableDelayedExpansion

REM Set test environment
set ENVIRONMENT=testing
set PYTHONPATH=%CD%

REM Colors for output (if supported)
echo [96m=== Audio Processor Test Runner (Windows) ===[0m
echo.

REM Check if .env.test exists
if not exist ".env.test" (
    echo [91mError: .env.test file not found![0m
    echo Please ensure .env.test exists before running tests.
    echo You can copy from .env.example and modify for testing.
    exit /b 1
)

REM Determine test command based on first argument
set TEST_TYPE=%1
if "%TEST_TYPE%"=="" set TEST_TYPE=all

REM Base pytest command
set PYTEST_CMD=pytest

REM Check if uv is available
uv --version >nul 2>&1
if %errorlevel%==0 (
    echo [92mUsing uv environment[0m
    set PYTEST_CMD=uv run pytest
) else (
    echo [93mFalling back to system Python environment[0m
    REM Check if pytest is available
    pytest --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo [91mError: pytest not found! Please install uv or pytest.[0m
        echo [93mInstall uv: https://docs.astral.sh/uv/[0m
        exit /b 1
    )
    set PYTEST_CMD=pytest
)

echo [96mRunning tests with environment: %ENVIRONMENT%[0m
echo.

REM Execute tests based on type
if "%TEST_TYPE%"=="all" (
    echo [94mRunning all tests...[0m
    %PYTEST_CMD% -v
) else if "%TEST_TYPE%"=="unit" (
    echo [94mRunning unit tests...[0m
    %PYTEST_CMD% -v tests/unit/
) else if "%TEST_TYPE%"=="integration" (
    echo [94mRunning integration tests...[0m
    %PYTEST_CMD% -v tests/integration/
) else if "%TEST_TYPE%"=="coverage" (
    echo [94mRunning tests with coverage...[0m
    %PYTEST_CMD% --cov=app --cov-report=html --cov-report=term-missing -v
) else if "%TEST_TYPE%"=="fast" (
    echo [94mRunning fast tests only...[0m
    %PYTEST_CMD% -v -m "not slow"
) else if "%TEST_TYPE%"=="env" (
    echo [94mRunning environment tests...[0m
    %PYTEST_CMD% -v tests/unit/test_environment.py
) else if "%TEST_TYPE%"=="watch" (
    echo [94mRunning tests in watch mode...[0m
    %PYTEST_CMD% -f
) else if "%TEST_TYPE%"=="debug" (
    echo [94mRunning tests with debug output...[0m
    %PYTEST_CMD% -v -s --tb=long
) else (
    echo [93mRunning custom test: %*[0m
    %PYTEST_CMD% %*
)

set TEST_EXIT_CODE=%errorlevel%

echo.
if %TEST_EXIT_CODE%==0 (
    echo [92m=== All tests passed! ===[0m
) else (
    echo [91m=== Some tests failed! ===[0m
)

REM Open coverage report if it was generated
if "%TEST_TYPE%"=="coverage" (
    if exist "htmlcov\index.html" (
        echo [96mOpening coverage report...[0m
        start htmlcov\index.html
    )
)

exit /b %TEST_EXIT_CODE%