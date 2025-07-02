@echo off
REM Quick Test Runner for Windows - Runs fast tests only
REM Usage: test-quick.bat

setlocal

set ENVIRONMENT=testing
set PYTHONPATH=%CD%

echo [96m=== Quick Test Runner (Windows) ===[0m
echo [93mRunning unit tests and fast integration tests...[0m
echo.

REM Check for uv
uv --version >nul 2>&1
if %errorlevel%==0 (
    uv run pytest -v -m "not slow" --tb=short
) else (
    pytest -v -m "not slow" --tb=short
)

if %errorlevel%==0 (
    echo.
    echo [92m✓ Quick tests passed![0m
) else (
    echo.
    echo [91m✗ Some quick tests failed![0m
)

exit /b %errorlevel%