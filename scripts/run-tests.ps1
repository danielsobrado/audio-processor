# Audio Processor - Test Runner for PowerShell (pytest version)
# Usage: .\run-tests.ps1 [test-type] [options]

param(
    [string]$TestType = "all",
    [string[]]$ExtraArgs = @()
)

# Set test environment
$env:ENVIRONMENT = "testing"
$env:PYTHONPATH = $PWD.Path

Write-Host "=== Audio Processor Test Runner (PowerShell - pytest) ===" -ForegroundColor Cyan
Write-Host

# Check if .env.test exists
if (-not (Test-Path ".env.test")) {
    Write-Host "Error: .env.test file not found!" -ForegroundColor Red
    Write-Host "Please ensure .env.test exists before running tests."
    Write-Host "You can copy from .env.example and modify for testing."
    exit 1
}

# Function to run pytest with common options
function Run-Pytest {
    param(
        [string]$TestPath = "tests/",
        [string[]]$AdditionalArgs = @()
    )

    $pytestArgs = @(
        "run",
        "pytest",
        $TestPath,
        "-v",
        "--asyncio-mode=auto",
        "--tb=short",
        "-s"
    )

    # Add additional arguments
    $pytestArgs += $AdditionalArgs
    $pytestArgs += $ExtraArgs

    Write-Host "Running: uv $($pytestArgs -join ' ')" -ForegroundColor Yellow
    & uv $pytestArgs
    return $LASTEXITCODE
}

# Function to check if Docker services are running
function Test-DockerServices {
    Write-Host "Checking Docker services..." -ForegroundColor Yellow

    $services = @("neo4j", "redis", "postgres")
    $allRunning = $true

    foreach ($service in $services) {
        try {
            $result = docker ps --filter "name=$service" --format "{{.Names}}" 2>$null
            if ($result -match $service) {
                Write-Host "✅ $service service is running" -ForegroundColor Green
            } else {
                Write-Host "❌ $service service is not running" -ForegroundColor Red
                $allRunning = $false
            }
        } catch {
            Write-Host "❌ Failed to check $service service" -ForegroundColor Red
            $allRunning = $false
        }
    }

    return $allRunning
}

# Function to check if API server is running
function Test-ApiServer {
    Write-Host "Checking API server..." -ForegroundColor Yellow

    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
        if ($response.status -eq "healthy") {
            Write-Host "✅ API server is running and healthy" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ API server is not healthy" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ API server is not responding" -ForegroundColor Red
        return $false
    }
}

# Main test execution
Write-Host "Test Type: $TestType" -ForegroundColor Cyan
Write-Host

$exitCode = 0

switch ($TestType.ToLower()) {
    "unit" {
        Write-Host "Running unit tests..." -ForegroundColor Green
        $exitCode = Run-Pytest -TestPath "tests/unit/" -AdditionalArgs @("-m", "not slow")
    }

    "integration" {
        Write-Host "Running integration tests..." -ForegroundColor Green
        $exitCode = Run-Pytest -TestPath "tests/integration/"
    }

    "e2e" {
        Write-Host "Running end-to-end tests..." -ForegroundColor Green

        # Check prerequisites
        $servicesOk = Test-DockerServices
        $apiOk = Test-ApiServer

        if (-not $servicesOk -or -not $apiOk) {
            Write-Host "❌ Prerequisites not met for E2E tests" -ForegroundColor Red
            Write-Host "Please ensure all services are running before running E2E tests." -ForegroundColor Red
            $exitCode = 1
        } else {
            $exitCode = Run-Pytest -TestPath "tests/e2e/"
        }
    }

    "quick" {
        Write-Host "Running quick tests (unit + integration)..." -ForegroundColor Green
        $exitCode = Run-Pytest -TestPath "tests/unit/ tests/integration/" -AdditionalArgs @("-m", "not slow")
    }

    "all" {
        Write-Host "Running all tests..." -ForegroundColor Green

        # Run unit tests
        Write-Host "`nRunning unit tests..." -ForegroundColor Yellow
        $unitResult = Run-Pytest -TestPath "tests/unit/" -AdditionalArgs @("-m", "not slow")

        # Run integration tests
        Write-Host "`nRunning integration tests..." -ForegroundColor Yellow
        $integrationResult = Run-Pytest -TestPath "tests/integration/"

        # Run E2E tests if prerequisites are met
        Write-Host "`nRunning end-to-end tests..." -ForegroundColor Yellow
        $servicesOk = Test-DockerServices
        $apiOk = Test-ApiServer

        if ($servicesOk -and $apiOk) {
            $e2eResult = Run-Pytest -TestPath "tests/e2e/"
        } else {
            Write-Host "⚠️  Skipping E2E tests (prerequisites not met)" -ForegroundColor Yellow
            $e2eResult = 0
        }

        # Set exit code based on results
        if ($unitResult -ne 0 -or $integrationResult -ne 0 -or $e2eResult -ne 0) {
            $exitCode = 1
        }
    }

    default {
        Write-Host "Unknown test type: $TestType" -ForegroundColor Red
        Write-Host "Available types: unit, integration, e2e, quick, all" -ForegroundColor Yellow
        $exitCode = 1
}

# Final output
Write-Host
if ($exitCode -eq 0) {
    Write-Host "=== All tests passed! ===" -ForegroundColor Green
} else {
    Write-Host "=== Some tests failed! ===" -ForegroundColor Red
}

exit $exitCode
