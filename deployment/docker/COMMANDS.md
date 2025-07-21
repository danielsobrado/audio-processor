# Quick Command Reference

## New Workflow Commands

### Development (from project root)
```bash
# Start all services (development mode with auto-reload)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build -d

# Check status
docker-compose ps
```

### Using the PowerShell Helper (Windows)
```powershell
# From deployment/docker directory
.\docker-dev.ps1 start    # Start development services
.\docker-dev.ps1 logs     # View logs
.\docker-dev.ps1 stop     # Stop services
.\docker-dev.ps1 build    # Rebuild and start
.\docker-dev.ps1 status   # Check status
.\docker-dev.ps1 clean    # Clean up everything
.\docker-dev.ps1 prod     # Production mode
```

### Production Mode
```bash
# Use only base file (ignoring overrides)
docker-compose -f docker-compose.yml up -d

# Or disable override file
mv docker-compose.override.yml docker-compose.override.yml.disabled
docker-compose up -d
```

## Service URLs
- **Application**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Neo4j Web UI**: http://localhost:7474
- **Neo4j Bolt**: bolt://localhost:7687

## Migration from Old Setup
- ✅ `docker-compose.dev.yml` backed up as `docker-compose.dev.yml.backup`
- ✅ No more `-f` flags needed for development
- ✅ All services now in unified configuration
- ✅ Neo4j added to base configuration
