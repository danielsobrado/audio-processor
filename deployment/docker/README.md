# Docker Deployment Guide

This directory contains secure, production-ready Docker configurations for the Audio Processor application.

## Security Features

### ✅ Docker Security Improvements

- **Python 3.12**: Latest stable Python version with security updates
- **Non-root user**: Application runs as `appuser` (UID 1000) for security
- **Multi-stage builds**: Optimized image size and reduced attack surface
- **Health checks**: Automated container health monitoring
- **Resource limits**: CPU and memory constraints to prevent resource exhaustion
- **Minimal base images**: Alpine/slim images with only necessary packages
- **No hardcoded secrets**: All sensitive data via environment variables

## Files Overview

- `Dockerfile` - Production-ready container with security best practices
- `Dockerfile.gpu` - GPU-enabled version for accelerated audio processing
- `docker-compose.yml` - Production deployment with security configurations
- `docker-compose.dev.yml` - Development environment with hot reload
- `.env.example` - Template for environment variables
- `.dockerignore` - Excludes sensitive files from Docker context

## Quick Start

### Development Environment

```bash
# Copy environment template
cp .env.example .env.dev

# Edit environment variables
vi .env.dev

# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# Access application
curl http://localhost:8000/api/v1/health
```

### Production Deployment

```bash
# Copy and configure environment
cp .env.example .env
vi .env  # Set secure passwords and secrets

# Start production services
docker-compose up -d --build

# Verify health
docker-compose ps
curl http://localhost:8000/api/v1/health
```

## Environment Configuration

### Required Environment Variables

Create `.env` file from template:

```bash
cp .env.example .env
```

**Critical Settings:**
```bash
# Strong, unique passwords
DB_PASSWORD=your_very_secure_database_password
REDIS_PASSWORD=your_very_secure_redis_password

# Application security
SECRET_KEY=your_32_plus_character_random_secret_key

# Authentication
KEYCLOAK_CLIENT_SECRET=your_keycloak_client_secret
```

### Optional Services

Enable optional services using profiles:

```bash
# Enable monitoring (Flower)
docker-compose --profile monitoring up -d

# Enable admin interface
docker-compose --profile admin up -d

# Production with nginx
docker-compose --profile production up -d
```

## GPU Support

For GPU-accelerated audio processing:

```bash
# Build GPU version
docker build -f Dockerfile.gpu -t audio-processor:gpu .

# Run with GPU support
docker run --gpus all -p 8000:8000 audio-processor:gpu
```

## Security Considerations

### Network Security

- **Internal networks**: Services communicate via isolated Docker networks
- **No exposed ports**: Database and Redis only accessible internally in production
- **Reverse proxy**: Nginx handles SSL termination and request routing

### Data Security

- **No source code mounting**: Production containers don't mount source code
- **Volume permissions**: Proper file ownership and permissions
- **Secrets management**: All secrets via environment variables, never in images

### Container Security

- **Read-only containers**: Application runs with minimal write permissions
- **Resource limits**: Prevents resource exhaustion attacks
- **Health monitoring**: Automatic restart of unhealthy containers

## Monitoring & Logging

### Health Checks

All services have automated health checks:

```bash
# Check service health
docker-compose ps

# View health check logs
docker-compose logs app
```

### Resource Monitoring

```bash
# Monitor resource usage
docker stats

# View container logs
docker-compose logs -f app worker
```

## Development Workflow

### Hot Reload Development

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Code changes auto-reload
# Database accessible at localhost:5432
# Redis accessible at localhost:6379
```

### Testing in Containers

```bash
# Run tests in container
docker-compose -f docker-compose.dev.yml exec app uv run pytest

# Run specific test file
docker-compose -f docker-compose.dev.yml exec app uv run pytest tests/unit/test_audio_processor.py
```

## Production Deployment

### Pre-deployment Checklist

- [ ] Environment variables configured with secure values
- [ ] Database migrations applied
- [ ] SSL certificates configured for nginx
- [ ] Health checks passing
- [ ] Resource limits appropriate for your infrastructure
- [ ] Monitoring and alerting configured

### Deployment Commands

```bash
# 1. Build and start services
docker-compose up -d --build

# 2. Run database migrations
docker-compose exec app uv run alembic upgrade head

# 3. Verify deployment
docker-compose ps
curl -f http://localhost:8000/api/v1/health

# 4. View logs
docker-compose logs -f app worker
```

### Scaling

Scale services based on load:

```bash
# Scale workers
docker-compose up -d --scale worker=3

# Scale with resource limits
docker-compose up -d --scale worker=3 --compatibility
```

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs app

# Check health
docker-compose ps
```

**Permission errors:**
```bash
# Fix volume permissions
docker-compose exec app chown -R appuser:appuser /app/logs /app/temp
```

**Database connection issues:**
```bash
# Check database health
docker-compose exec postgres pg_isready -U audiouser

# Test connection
docker-compose exec app uv run python -c "from app.db.session import AsyncSessionLocal; print('DB OK')"
```

### Security Auditing

```bash
# Scan images for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image audio-processor:latest

# Check container security
docker run --rm --cap-add=SYS_ADMIN \
  --security-opt apparmor:unconfined \
  docker/docker-bench-security
```

## Maintenance

### Updates

```bash
# Update base images
docker-compose pull

# Rebuild with updates
docker-compose up -d --build

# Clean up old images
docker image prune -f
```

### Backups

```bash
# Backup database
docker-compose exec postgres pg_dump -U audiouser audio_processor > backup.sql

# Backup volumes
docker run --rm -v audio_processor_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Performance Tuning

### Resource Optimization

Adjust resource limits based on your workload:

```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G      # Increase for larger audio files
      cpus: '2.0'     # Increase for faster processing
```

### Database Tuning

```bash
# Optimize PostgreSQL settings
docker-compose exec postgres psql -U audiouser -c "
  ALTER SYSTEM SET shared_buffers = '256MB';
  ALTER SYSTEM SET effective_cache_size = '1GB';
  SELECT pg_reload_conf();
"
```

For additional support and advanced configurations, refer to the main project documentation.
