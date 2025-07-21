# Manual code quality checks script for Windows PowerShell
#
# This script runs comprehensive linting checks that are not included
# in the pre-commit hooks to avoid being too intrusive during development.
#
# Usage:
#     .\scripts\run_linting.ps1 [-Fix] [-All]
#
#     -Fix: Attempt to automatically fix issues where possible
#     -All: Run all checks including mypy and pydocstyle

param(
    [switch]$Fix,
    [switch]$All
)

function Run-Command {
    param(
        [string[]]$Command,
        [string]$Description,
        [bool]$FixMode = $false
    )

    Write-Host "`n🔍 $Description..." -ForegroundColor Cyan

    try {
        if ($FixMode -and $Command -contains "ruff" -and $Command -notcontains "--fix") {
            $Command += "--fix"
        }

        $result = & $Command[0] $Command[1..($Command.Length-1)] 2>&1
        $exitCode = $LASTEXITCODE

        if ($exitCode -eq 0) {
            Write-Host "✅ $Description passed" -ForegroundColor Green
            if ($result) {
                Write-Host $result
            }
            return $true
        } else {
            Write-Host "❌ $Description failed" -ForegroundColor Red
            if ($result) {
                Write-Host $result
            }
            return $false
        }
    } catch {
        Write-Host "❌ Error running $Description`: $_" -ForegroundColor Red
        return $false
    }
}

# Change to project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "🧹 Running code quality checks..." -ForegroundColor Yellow
Write-Host "📁 Working directory: $projectRoot"

$success = $true

# Core checks (always run)
$checks = @(
    @(@("uv", "run", "ruff", "check", "app/", "--exclude", "tests/,scripts/,migrations/"), "Ruff linting (app only)"),
    @(@("uv", "run", "ruff", "format", "--check", "app/", "--exclude", "tests/,scripts/,migrations/"), "Ruff formatting (app only)")
)

# Extended checks (only with -All flag)
if ($All) {
    $checks += @(
        @(@("uv", "run", "mypy", "app/", "--ignore-missing-imports"), "MyPy type checking"),
        @(@("uv", "run", "pydocstyle", "app/", "--convention=google", "--add-ignore=D100,D101,D102,D103,D104,D105,D106,D107"), "Docstring checking")
    )
}

foreach ($check in $checks) {
    $cmd, $description = $check
    if (-not (Run-Command -Command $cmd -Description $description -FixMode $Fix)) {
        $success = $false
    }
}

# Summary
Write-Host "`n$('='*50)"
if ($success) {
    Write-Host "🎉 All checks passed!" -ForegroundColor Green
    if (-not $All) {
        Write-Host "💡 Run with -All for comprehensive checks including mypy and pydocstyle" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Some checks failed" -ForegroundColor Red
    if ($Fix) {
        Write-Host "💡 Some issues may have been automatically fixed. Please review changes." -ForegroundColor Yellow
    } else {
        Write-Host "💡 Run with -Fix to automatically fix some issues" -ForegroundColor Yellow
    }
}

exit $(if ($success) { 0 } else { 1 })
