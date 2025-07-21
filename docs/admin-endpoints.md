# Admin Endpoints and Enhanced Health Monitoring

This document describes the P1 priority features added to the audio processing API: enhanced health monitoring with Celery worker status and comprehensive admin job management endpoints.

## 🏥 Enhanced Health Check Endpoint

### Overview
The health check endpoint now monitors the complete system stack including Celery workers and broker status.

### Endpoint
```
GET /api/v1/health
```

### Response Format
```json
{
  "status": "ok|warning|error",
  "dependencies": {
    "database": "ok|error",
    "redis": "ok|error",
    "celery_broker": "ok|error",
    "celery_workers": "ok|warning|error",
    "worker_count": 2,
    "active_workers": ["worker@hostname1", "worker@hostname2"]
  }
}
```

### Status Levels
- **ok**: All services operational
- **warning**: Non-critical issues (e.g., no active workers but broker accessible)
- **error**: Critical service failures (503 status code)

### Monitoring Features
- **Database connectivity** - PostgreSQL connection test
- **Redis connectivity** - Cache and session store test
- **Celery broker** - Message broker accessibility
- **Active workers** - Count and identification of running workers
- **Worker health** - Responsive worker detection

### Usage Examples
```bash
# Basic health check
curl http://localhost:8000/api/v1/health

# Monitor in production
curl -f http://localhost:8000/api/v1/health || alert_admin

# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /api/v1/health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

## 🔧 Admin Job Management Endpoints

### Overview
Comprehensive admin-only endpoints for system monitoring, troubleshooting, and operational support.

### Authentication
All admin endpoints require the `admin` role:
```bash
Authorization: Bearer <admin-token>
```

---

## 📋 List All Jobs

### Endpoint
```
GET /api/v1/admin/jobs
```

### Query Parameters
- `status_filter` (optional): Filter by job status (`pending`, `processing`, `completed`, `failed`)
- `limit` (optional): Maximum jobs to return (1-500, default: 50)
- `offset` (optional): Number of jobs to skip (default: 0)

### Response
```json
{
  "jobs": [
    {
      "request_id": "abc-123-def-456",
      "user_id": "user-789",
      "status": "completed",
      "progress": 100.0,
      "created": "2025-07-08T10:30:00Z",
      "updated": "2025-07-08T10:35:00Z",
      "result": { /* transcription result */ },
      "error": null,
      "task_id": "celery-task-123",
      "job_type": "transcription",
      "parameters": { /* job parameters */ }
    }
  ],
  "total_count": 150,
  "limit": 50,
  "offset": 0
}
```

### Usage Examples
```bash
# List all jobs
curl -H "Authorization: Bearer admin-token" \
  http://localhost:8000/api/v1/admin/jobs

# Filter failed jobs
curl -H "Authorization: Bearer admin-token" \
  "http://localhost:8000/api/v1/admin/jobs?status_filter=failed"

# Paginate results
curl -H "Authorization: Bearer admin-token" \
  "http://localhost:8000/api/v1/admin/jobs?limit=25&offset=100"
```

---

## 🔄 Requeue Failed Job

### Endpoint
```
POST /api/v1/admin/jobs/{request_id}/requeue
```

### Request Body
```json
{
  "reason": "Infrastructure failure - retrying after fix"
}
```

### Response
```json
{
  "request_id": "failed-job-123",
  "new_task_id": "celery-task-456",
  "status": "requeued",
  "message": "Job successfully requeued. New task ID: celery-task-456"
}
```

### Requirements
- Job must be in `failed` status
- Original job parameters are preserved
- New Celery task is created

### Usage Examples
```bash
# Requeue a failed job
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Network timeout - infrastructure fixed"}' \
  http://localhost:8000/api/v1/admin/jobs/failed-job-123/requeue
```

### Common Use Cases
- **Infrastructure failures**: Network outages, service downtime
- **Temporary resource limits**: Memory/disk space issues
- **External service outages**: Third-party API failures
- **Configuration errors**: Fixed environment issues

---

## 🔍 Get Job Details

### Endpoint
```
GET /api/v1/admin/jobs/{request_id}
```

### Response
```json
{
  "request_id": "job-456",
  "user_id": "user-123",
  "status": "processing",
  "progress": 65.0,
  "created": "2025-07-08T11:00:00Z",
  "updated": "2025-07-08T11:02:30Z",
  "result": null,
  "error": null,
  "task_id": "active-task-789",
  "job_type": "transcription",
  "parameters": {
    "language": "auto",
    "diarize": true,
    "callback_url": "https://client.com/webhook"
  }
}
```

### Usage Examples
```bash
# Get detailed job information
curl -H "Authorization: Bearer admin-token" \
  http://localhost:8000/api/v1/admin/jobs/job-456

# Troubleshoot stuck job
curl -H "Authorization: Bearer admin-token" \
  http://localhost:8000/api/v1/admin/jobs/stuck-job-789
```

---

## 🗑️ Delete Job

### Endpoint
```
DELETE /api/v1/admin/jobs/{request_id}
```

### Response
```json
{
  "message": "Job job-123 successfully deleted"
}
```

### ⚠️ Warning
This operation is **permanent** and cannot be undone.

### Usage Examples
```bash
# Delete a job permanently
curl -X DELETE \
  -H "Authorization: Bearer admin-token" \
  http://localhost:8000/api/v1/admin/jobs/job-to-delete

# Clean up test jobs
for job in test-job-1 test-job-2; do
  curl -X DELETE \
    -H "Authorization: Bearer admin-token" \
    http://localhost:8000/api/v1/admin/jobs/$job
done
```

### Use Cases
- **Test cleanup**: Remove development/testing jobs
- **Data compliance**: GDPR deletion requests
- **Corrupted data**: Remove malformed job records
- **Storage management**: Clean up old completed jobs

---

## 📊 System Statistics

### Endpoint
```
GET /api/v1/admin/stats
```

### Response
```json
{
  "total_jobs": 1250,
  "recent_jobs_24h": 45,
  "status_breakdown": {
    "completed": 1100,
    "failed": 85,
    "processing": 5,
    "pending": 60
  },
  "timestamp": "2025-07-08T12:00:00Z"
}
```

### Usage Examples
```bash
# Get system statistics
curl -H "Authorization: Bearer admin-token" \
  http://localhost:8000/api/v1/admin/stats

# Monitor system health
watch -n 30 'curl -s -H "Authorization: Bearer admin-token" \
  http://localhost:8000/api/v1/admin/stats | jq .'
```

### Monitoring Use Cases
- **Capacity planning**: Track job volume trends
- **Performance monitoring**: Success/failure rates
- **Resource allocation**: Processing queue depth
- **SLA monitoring**: Job completion rates

---

## 🚀 Operational Workflows

### 1. Investigating Failed Jobs
```bash
# 1. List recent failed jobs
curl -H "Authorization: Bearer admin-token" \
  "http://localhost:8000/api/v1/admin/jobs?status_filter=failed&limit=10"

# 2. Get details of specific failure
curl -H "Authorization: Bearer admin-token" \
  http://localhost:8000/api/v1/admin/jobs/failed-job-123

# 3. Requeue after fixing underlying issue
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Fixed audio processing service"}' \
  http://localhost:8000/api/v1/admin/jobs/failed-job-123/requeue
```

### 2. System Health Monitoring
```bash
# 1. Check overall system health
curl http://localhost:8000/api/v1/health

# 2. Get system statistics
curl -H "Authorization: Bearer admin-token" \
  http://localhost:8000/api/v1/admin/stats

# 3. Monitor processing queue
curl -H "Authorization: Bearer admin-token" \
  "http://localhost:8000/api/v1/admin/jobs?status_filter=processing"
```

### 3. Bulk Operations
```bash
# Find and requeue all jobs failed due to specific error
curl -H "Authorization: Bearer admin-token" \
  "http://localhost:8000/api/v1/admin/jobs?status_filter=failed" | \
  jq -r '.jobs[] | select(.error | contains("Network timeout")) | .request_id' | \
  while read job_id; do
    curl -X POST \
      -H "Authorization: Bearer admin-token" \
      -H "Content-Type: application/json" \
      -d '{"reason": "Network infrastructure fixed"}' \
      "http://localhost:8000/api/v1/admin/jobs/$job_id/requeue"
  done
```

## 🔒 Security Considerations

### Role-Based Access Control
- All admin endpoints require `admin` role
- JWT token validation enforced
- Audit logging for all admin operations

### Rate Limiting
Consider implementing rate limits for admin endpoints:
```python
# Example rate limiting configuration
admin_rate_limit = "100/hour"  # 100 requests per hour per admin
```

### Audit Trail
Admin operations are logged for security auditing:
```
INFO Admin user:admin-123 requeued job:failed-job-456 reason:"Infrastructure failure"
WARNING Admin user:admin-123 deleted job:test-job-789
```

## 📈 Monitoring and Alerting

### Health Check Monitoring
```yaml
# Prometheus/Grafana monitoring
- alert: APIHealthCheckFailed
  expr: up{job="audio-processor"} == 0
  for: 2m
  annotations:
    summary: "Audio processor health check failing"

- alert: CeleryWorkersDown
  expr: celery_workers_count == 0
  for: 5m
  annotations:
    summary: "No Celery workers active"
```

### Job Statistics Monitoring
```yaml
- alert: HighFailureRate
  expr: (failed_jobs_24h / total_jobs_24h) > 0.1
  for: 10m
  annotations:
    summary: "Job failure rate above 10%"
```

## 🛠️ Troubleshooting

### Common Issues

**1. No Active Workers (Warning Status)**
```bash
# Check worker status
curl http://localhost:8000/api/v1/health

# Start workers
celery -A app.workers.celery_app worker --loglevel=info
```

**2. Failed Job Requeue Not Working**
- Verify job is in `failed` status
- Check Celery broker connectivity
- Ensure original job parameters are valid

**3. Admin Authentication Failures**
- Verify JWT token has `admin` role
- Check token expiration
- Validate authorization header format

**4. High Memory Usage**
- Monitor job queue depth
- Check for stuck processing jobs
- Review worker resource allocation

This comprehensive admin system provides full operational control over the audio processing pipeline while maintaining security and auditability.
