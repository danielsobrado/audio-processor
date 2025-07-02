# Task Completion Workflow

## When a Development Task is Completed

### 1. Code Quality Checks
```bash
# Run tests to ensure nothing is broken
pytest

# Run tests with coverage
pytest --cov=app

# Check for any linting issues (if configured)
flake8 app/ tests/
pylint app/

# Format code (if using formatters)
black app/ tests/
isort app/ tests/
```

### 2. Database Migrations (if models changed)
```bash
# Generate migration if database models were modified
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Verify migration worked
alembic history
```

### 3. Environment Testing
```bash
# Test locally with all services
docker-compose -f deployment/docker/docker-compose.yml up --build -d

# Verify API endpoints work
curl http://localhost:8000/api/v1/health

# Test core functionality
curl -X POST http://localhost:8000/api/v1/transcribe -F "audio=@test_file.wav"

# Check logs for errors
docker-compose logs app
docker-compose logs celery-worker
```

### 4. Documentation Updates
- Update README.md if new features or setup steps
- Update API documentation (FastAPI auto-generates from docstrings)
- Update .env.example if new environment variables
- Update deployment manifests if configuration changed

### 5. Git Workflow
```bash
# Check status and stage changes
git status
git add .

# Commit with descriptive message
git commit -m "feat: Add new audio processing feature"

# Push to feature branch
git push origin feature-branch

# Create pull request for review
```

### 6. Integration Testing
- Test with sample audio files in multiple formats
- Verify async job processing works
- Check Redis and database connections
- Test error handling scenarios
- Verify rate limiting works

### 7. Performance Considerations
- Monitor memory usage during audio processing
- Check Celery task queue performance
- Verify database query performance
- Test file upload limits
- Monitor Redis memory usage

## Pre-Deploy Checklist
- [ ] All tests pass
- [ ] Database migrations applied
- [ ] Environment variables documented
- [ ] Docker images build successfully
- [ ] Configuration files updated
- [ ] Security review completed
- [ ] Performance tested
- [ ] Documentation updated