#!/usr/bin/env pwsh
# Start infrastructure-only services (PostgreSQL, Redis, Neo4j)
# Use this when you want to run the app locally but need the databases

Write-Host "Starting infrastructure services (PostgreSQL, Redis, Neo4j)..." -ForegroundColor Green
Write-Host "App will run locally - use 'uvicorn app.main:app --reload' to start it" -ForegroundColor Yellow

try {
    docker-compose -f docker-compose.infra.yml up -d

    Write-Host "`nWaiting for services to be healthy..." -ForegroundColor Blue
    Start-Sleep -Seconds 5

    Write-Host "`nService Status:" -ForegroundColor Green
    docker-compose -f docker-compose.infra.yml ps

    Write-Host "`nServices started successfully!" -ForegroundColor Green
    Write-Host "PostgreSQL: localhost:5432" -ForegroundColor Cyan
    Write-Host "Redis: localhost:6379" -ForegroundColor Cyan
    Write-Host "Neo4j Web UI: http://localhost:7474" -ForegroundColor Cyan
    Write-Host "Neo4j Bolt: bolt://localhost:7687" -ForegroundColor Cyan

    Write-Host "`nTo start the app locally:" -ForegroundColor Yellow
    Write-Host "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White

    Write-Host "`nTo stop services:" -ForegroundColor Yellow
    Write-Host "docker-compose -f docker-compose.infra.yml down" -ForegroundColor White
}
catch {
    Write-Error "Failed to start services: $_"
    exit 1
}
