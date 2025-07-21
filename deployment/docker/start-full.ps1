#!/usr/bin/env pwsh
# Start full Docker deployment (all services including app and celery worker)
# Use this for production-like environment or when you want everything in Docker

Write-Host "Starting full Docker deployment (all services)..." -ForegroundColor Green

try {
    docker-compose -f docker-compose.full.yml up -d --build

    Write-Host "`nWaiting for services to be healthy..." -ForegroundColor Blue
    Start-Sleep -Seconds 10

    Write-Host "`nService Status:" -ForegroundColor Green
    docker-compose -f docker-compose.full.yml ps

    Write-Host "`nServices started successfully!" -ForegroundColor Green
    Write-Host "API Server: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "PostgreSQL: localhost:5432" -ForegroundColor Cyan
    Write-Host "Redis: localhost:6379" -ForegroundColor Cyan
    Write-Host "Neo4j Web UI: http://localhost:7474" -ForegroundColor Cyan
    Write-Host "Neo4j Bolt: bolt://localhost:7687" -ForegroundColor Cyan

    Write-Host "`nTo view logs:" -ForegroundColor Yellow
    Write-Host "docker-compose -f docker-compose.full.yml logs -f" -ForegroundColor White

    Write-Host "`nTo stop services:" -ForegroundColor Yellow
    Write-Host "docker-compose -f docker-compose.full.yml down" -ForegroundColor White
}
catch {
    Write-Error "Failed to start services: $_"
    exit 1
}
