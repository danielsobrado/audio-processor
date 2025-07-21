@echo off
REM Test Environment Setup for Windows
REM Usage: setup-tests.bat

setlocal EnableDelayedExpansion

echo [96m=== Audio Processor Test Environment Setup (Windows) ===[0m
echo.

REM Check if .env.test exists, if not create from example
if not exist ".env.test" (
    if exist ".env.example" (
        echo [93mCreating .env.test from .env.example...[0m
        copy ".env.example" ".env.test" >nul
        echo [92m✓ .env.test created[0m
    ) else (
        echo [91mError: .env.example not found![0m
        exit /b 1
    )
) else (
    echo [92m✓ .env.test already exists[0m
)

REM Check for uv
echo [94mChecking for uv...[0m
uv --version >nul 2>&1
if %errorlevel%==0 (
    echo [92m✓ uv found[0m
    echo [94mSyncing dependencies with uv...[0m
    uv sync --dev
    if !errorlevel!==0 (
        echo [92m✓ Dependencies installed[0m
    ) else (
        echo [91m✗ Failed to install dependencies[0m
        exit /b 1
    )
) else (
    echo [93muv not found, checking pip...[0m
    pip --version >nul 2>&1
    if !errorlevel!==0 (
        echo [92m✓ pip found[0m
        echo [94mInstalling test dependencies...[0m
        pip install pytest pytest-asyncio pytest-cov httpx
        pip install -r requirements.txt
        if !errorlevel!==0 (
            echo [92m✓ Dependencies installed[0m
        ) else (
            echo [91m✗ Failed to install dependencies[0m
            exit /b 1
        )
    ) else (
        echo [91mError: Neither uv nor pip found![0m
        echo [93mInstall uv: https://docs.astral.sh/uv/[0m
        exit /b 1
    )
)

REM Test the setup
echo.
echo [94mTesting environment setup...[0m
set ENVIRONMENT=testing

if exist "scripts\run-tests.bat" (
    echo [94mRunning environment tests...[0m
    call scripts\run-tests.bat env
    if !errorlevel!==0 (
        echo.
        echo [92m=== Test environment setup complete! ===[0m
        echo.
        echo [96mYou can now run tests with:[0m
        echo [97m  scripts\run-tests.bat           [0m[90m# Run all tests[0m
        echo [97m  scripts\run-tests.bat unit      [0m[90m# Run unit tests[0m
        echo [97m  scripts\run-tests.bat coverage  [0m[90m# Run with coverage[0m
        echo [97m  scripts\test-quick.bat          [0m[90m# Run fast tests only[0m
    ) else (
        echo [91m✗ Environment test failed![0m
        exit /b 1
    )
) else (
    echo [91mError: scripts\run-tests.bat not found![0m
    exit /b 1
)
