#!/usr/bin/env powershell

# Docker Compose Development Helper Script

param(
    [Parameter(Mandatory=$false)]
    [string]$Action = "help"
)

function Show-Help {
    Write-Host "Docker Compose Development Helper" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\docker-dev.ps1 [action]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor White
    Write-Host "  start     - Start all services with development overrides"
    Write-Host "  stop      - Stop all services"
    Write-Host "  restart   - Restart all services"
    Write-Host "  build     - Rebuild and start services"
    Write-Host "  logs      - Show logs from all services"
    Write-Host "  status    - Show status of all services"
    Write-Host "  clean     - Stop and remove containers, networks, and volumes"
    Write-Host "  prod      - Start in production mode (no overrides)"
    Write-Host "  help      - Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\docker-dev.ps1 start"
    Write-Host "  .\docker-dev.ps1 logs"
    Write-Host "  .\docker-dev.ps1 build"
}

function Start-Development {
    Write-Host "Starting services in development mode..." -ForegroundColor Green
    docker-compose up -d
}

function Stop-Services {
    Write-Host "Stopping all services..." -ForegroundColor Yellow
    docker-compose down
}

function Restart-Services {
    Write-Host "Restarting all services..." -ForegroundColor Yellow
    docker-compose down
    docker-compose up -d
}

function Build-Services {
    Write-Host "Rebuilding and starting services..." -ForegroundColor Green
    docker-compose up --build -d
}

function Show-Logs {
    Write-Host "Showing logs from all services..." -ForegroundColor Cyan
    docker-compose logs -f
}

function Show-Status {
    Write-Host "Service status:" -ForegroundColor Cyan
    docker-compose ps
}

function Clean-Environment {
    Write-Host "Cleaning up containers, networks, and volumes..." -ForegroundColor Red
    docker-compose down -v --remove-orphans
    docker system prune -f
}

function Start-Production {
    Write-Host "Starting in production mode (no development overrides)..." -ForegroundColor Magenta
    docker-compose -f docker-compose.yml up -d
}

# Main script logic
Set-Location $PSScriptRoot

switch ($Action.ToLower()) {
    "start" { Start-Development }
    "stop" { Stop-Services }
    "restart" { Restart-Services }
    "build" { Build-Services }
    "logs" { Show-Logs }
    "status" { Show-Status }
    "clean" { Clean-Environment }
    "prod" { Start-Production }
    "help" { Show-Help }
    default {
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Write-Host ""
        Show-Help
    }
}
