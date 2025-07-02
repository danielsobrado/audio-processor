# Audio Processor - Test Runner for PowerShell
# Usage: .\run-tests.ps1 [test-type] [options]

param(
    [string]$TestType = "all",
    [string[]]$ExtraArgs = @()
)

# Set test environment
$env:ENVIRONMENT = "testing"
$env:PYTHONPATH = $PWD.Path

Write-Host "=== Audio Processor Test Runner (PowerShell) ===" -ForegroundColor Cyan
Write-Host

# Check if .env.test exists
if (-not (Test-Path ".env.test")) {
    Write-Host "Error: .env.test file not found!" -ForegroundColor Red
    Write-Host "Please ensure .env.test exists before running tests."
    Write-Host "You can copy from .env.example and modify for testing."
    exit 1
}

# Check if poetry is available
$poetryAvailable = $false
try {
    poetry --version | Out-Null
    $poetryAvailable = $true
    Write-Host "Using Poetry environment" -ForegroundColor Green
    $pytestCmd = "poetry run pytest"
} catch {
    Write-Host "Using system Python environment" -ForegroundColor Yellow
    # Check if pytest is available
    try {
        pytest --version | Out-Null
        $pytestCmd = "pytest"
    } catch {
        Write-Host "Error: pytest not found! Please install pytest or use poetry." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Running tests with environment: $($env:ENVIRONMENT)" -ForegroundColor Cyan
Write-Host

# Function to run tests
function Invoke-Tests {
    param([string]$Description, [string[]]$Args)
    
    Write-Host $Description -ForegroundColor Blue
    $command = "$pytestCmd $($Args -join ' ')"
    
    try {
        Invoke-Expression $command
        $exitCode = $LASTEXITCODE
        if ($exitCode -eq 0) {
            Write-Host "✓ Tests completed successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ Tests failed" -ForegroundColor Red
        }
        return $exitCode
    } catch {
        Write-Host "✗ Error running tests: $_" -ForegroundColor Red
        return 1
    }
}

# Execute tests based on type
$exitCode = switch ($TestType.ToLower()) {
    "all" { 
        Invoke-Tests "Running all tests..." @("-v")
    }
    "unit" { 
        Invoke-Tests "Running unit tests..." @("-v", "tests/unit/")
    }
    "integration" { 
        Invoke-Tests "Running integration tests..." @("-v", "tests/integration/")
    }
    "coverage" { 
        $result = Invoke-Tests "Running tests with coverage..." @("--cov=app", "--cov-report=html", "--cov-report=term-missing", "-v")
        # Open coverage report if it exists
        if (Test-Path "htmlcov/index.html") {
            Write-Host "Opening coverage report..." -ForegroundColor Cyan
            Start-Process "htmlcov/index.html"
        }
        $result
    }
    "fast" { 
        Invoke-Tests "Running fast tests only..." @("-v", "-m", "`"not slow`"")
    }
    "env" { 
        Invoke-Tests "Running environment tests..." @("-v", "tests/unit/test_environment.py")
    }
    "watch" { 
        Write-Host "Running tests in watch mode..." -ForegroundColor Blue
        Invoke-Expression "$pytestCmd -f"
        $LASTEXITCODE
    }
    "debug" { 
        Invoke-Tests "Running tests with debug output..." @("-v", "-s", "--tb=long")
    }
    "help" {
        Write-Host "Audio Processor Test Runner" -ForegroundColor Cyan
        Write-Host
        Write-Host "Usage: .\run-tests.ps1 [test-type] [options]"
        Write-Host
        Write-Host "Test types:"
        Write-Host "  all          Run all tests (default)"
        Write-Host "  unit         Run unit tests only"
        Write-Host "  integration  Run integration tests only"
        Write-Host "  coverage     Run tests with coverage report"
        Write-Host "  fast         Run tests excluding slow ones"
        Write-Host "  env          Run environment configuration tests"
        Write-Host "  watch        Run tests in watch mode"
        Write-Host "  debug        Run tests with verbose debug output"
        Write-Host "  help         Show this help message"
        Write-Host
        Write-Host "Examples:"
        Write-Host "  .\run-tests.ps1                    # Run all tests"
        Write-Host "  .\run-tests.ps1 unit               # Run unit tests"
        Write-Host "  .\run-tests.ps1 coverage           # Run with coverage"
        return 0
    }
    default { 
        Write-Host "Running custom test: $TestType $($ExtraArgs -join ' ')" -ForegroundColor Yellow
        $allArgs = @($TestType) + $ExtraArgs
        Invoke-Expression "$pytestCmd $($allArgs -join ' ')"
        $LASTEXITCODE
    }
}

Write-Host
if ($exitCode -eq 0) {
    Write-Host "=== All tests passed! ===" -ForegroundColor Green
} else {
    Write-Host "=== Some tests failed! ===" -ForegroundColor Red
}

exit $exitCode