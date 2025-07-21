# Docker Deployment Options

This directory contains multiple deployment configurations for different development and production scenarios.

## Deployment Options

### 1. Infrastructure-Only (Recommended for Development)

**Use Case**: Run the audio processor app locally with hot reloading while using Docker for databases.

**Services**: PostgreSQL, Redis, Neo4j (in Docker) + App (local)

```powershell
# Start infrastructure services
.\start-infra.ps1

# In another terminal, start the app locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Benefits**:
- Fast development with hot reloading
- Easy debugging and code changes
- Full access to local development tools
- Isolated database services

### 2. Full Docker Deployment

**Use Case**: Production-like environment or when you want everything containerized.

**Services**: PostgreSQL, Redis, Neo4j, App, Celery Worker (all in Docker)

```powershell
# Start all services in Docker
.\start-full.ps1
```

**Benefits**:
- Production-like environment
- Isolated and reproducible
- Easy deployment
- Scalable with load balancers

## Quick Commands

```powershell
# Infrastructure only (app runs locally)
.\start-infra.ps1

# Full Docker deployment
.\start-full.ps1

# Stop everything
.\stop-all.ps1

# Stop everything and remove data
.\stop-all.ps1 -RemoveVolumes

# Complete cleanup (stop, remove volumes and images)
.\stop-all.ps1 -RemoveVolumes -RemoveImages
```

## Service URLs

When services are running, they're available at:

- **API Server**: http://localhost:8000 (if running locally or in full Docker)
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Neo4j Web UI**: http://localhost:7474
- **Neo4j Bolt Protocol**: bolt://localhost:7687

## Configuration Files

- `docker-compose.infra.yml` - Infrastructure services only
- `docker-compose.full.yml` - Complete Docker deployment
- `docker-compose.yml` - Base configuration (legacy, kept for compatibility)
- `docker-compose.override.yml` - Development overrides (legacy)

## Environment Variables

Make sure you have a `.env` file in the project root with:

```env
# Database
POSTGRES_DB=audio_processor
POSTGRES_USER=user
POSTGRES_PASSWORD=password
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/audio_processor

# Redis
REDIS_URL=redis://localhost:6379/0

# Neo4j
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_URL=bolt://localhost:7687

# Other configurations...
```

## Troubleshooting

### Services won't start
```powershell
# Check if ports are in use
netstat -an | findstr ":5432"
netstat -an | findstr ":6379"
netstat -an | findstr ":7474"

# Stop all services and try again
.\stop-all.ps1
.\start-infra.ps1  # or .\start-full.ps1
```

### Reset everything
```powershell
# Complete reset (removes all data!)
.\stop-all.ps1 -RemoveVolumes -RemoveImages
.\start-infra.ps1  # or .\start-full.ps1
```

### Check service health
```powershell
# For infrastructure services
docker-compose -f docker-compose.infra.yml ps

# For full deployment
docker-compose -f docker-compose.full.yml ps

# View logs
docker-compose -f docker-compose.infra.yml logs -f
docker-compose -f docker-compose.full.yml logs -f
```
