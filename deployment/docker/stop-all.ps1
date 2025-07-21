#!/usr/bin/env pwsh
# Stop all Docker services and clean up
param(
    [switch]$RemoveVolumes,
    [switch]$RemoveImages
)

Write-Host "Stopping all Docker services..." -ForegroundColor Yellow

# Stop infrastructure services
if (Test-Path "docker-compose.infra.yml") {
    Write-Host "Stopping infrastructure services..." -ForegroundColor Blue
    docker-compose -f docker-compose.infra.yml down
}

# Stop full deployment services
if (Test-Path "docker-compose.full.yml") {
    Write-Host "Stopping full deployment services..." -ForegroundColor Blue
    docker-compose -f docker-compose.full.yml down
}

# Stop any services from the main docker-compose.yml
if (Test-Path "docker-compose.yml") {
    Write-Host "Stopping main docker-compose services..." -ForegroundColor Blue
    docker-compose down
}

if ($RemoveVolumes) {
    Write-Host "Removing volumes..." -ForegroundColor Red
    docker volume rm audio_postgres_data audio_redis_data audio_neo4j_data 2>$null
}

if ($RemoveImages) {
    Write-Host "Removing built images..." -ForegroundColor Red
    docker images --filter "reference=*audio*" -q | ForEach-Object { docker rmi $_ 2>$null }
}

# Clean up orphaned containers
Write-Host "Cleaning up orphaned containers..." -ForegroundColor Blue
docker-compose down --remove-orphans 2>$null

Write-Host "All services stopped successfully!" -ForegroundColor Green

Write-Host "`nUsage examples:" -ForegroundColor Yellow
Write-Host "  .\stop-all.ps1                    # Stop all services"
Write-Host "  .\stop-all.ps1 -RemoveVolumes     # Stop services and remove data volumes"
Write-Host "  .\stop-all.ps1 -RemoveImages      # Stop services and remove built images"
Write-Host "  .\stop-all.ps1 -RemoveVolumes -RemoveImages  # Complete cleanup"
