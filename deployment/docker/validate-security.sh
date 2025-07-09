#!/bin/bash

# Docker Security Validation Script
# Validates that the Docker security improvements are properly implemented

set -e

echo "🔒 Docker Security Validation Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print error
error() {
    echo -e "${RED}❌ $1${NC}"
}

echo ""
echo "1. Checking Python Version..."
PYTHON_VERSION=$(docker run --rm audio-processor:latest python --version 2>&1 | grep -oP '\d+\.\d+')
if [[ "$PYTHON_VERSION" == "3.12" ]]; then
    success "Python 3.12 detected"
else
    error "Expected Python 3.12, found: $PYTHON_VERSION"
fi

echo ""
echo "2. Checking Non-Root User..."
USER_CHECK=$(docker run --rm audio-processor:latest whoami 2>/dev/null || echo "root")
if [[ "$USER_CHECK" == "appuser" ]]; then
    success "Running as non-root user: $USER_CHECK"
else
    error "Container running as root user: $USER_CHECK"
fi

echo ""
echo "3. Checking User ID..."
UID_CHECK=$(docker run --rm audio-processor:latest id -u 2>/dev/null || echo "0")
if [[ "$UID_CHECK" == "1000" ]]; then
    success "Non-root UID confirmed: $UID_CHECK"
else
    error "Expected UID 1000, found: $UID_CHECK"
fi

echo ""
echo "4. Checking Health Check Configuration..."
HEALTH_CHECK=$(docker inspect audio-processor:latest | jq -r '.[0].Config.Healthcheck.Test[0]' 2>/dev/null || echo "null")
if [[ "$HEALTH_CHECK" == "CMD-SHELL" ]] || [[ "$HEALTH_CHECK" == "CMD" ]]; then
    success "Health check configured"
else
    warning "No health check found in image"
fi

echo ""
echo "5. Checking for Installed Security Tools..."
CURL_CHECK=$(docker run --rm audio-processor:latest which curl 2>/dev/null || echo "not found")
if [[ "$CURL_CHECK" != "not found" ]]; then
    success "curl installed for health checks"
else
    warning "curl not found - health checks may fail"
fi

echo ""
echo "6. Checking File Permissions..."
LOG_PERMS=$(docker run --rm audio-processor:latest ls -ld /app/logs 2>/dev/null | awk '{print $3":"$4}' || echo "error")
if [[ "$LOG_PERMS" == "appuser:appuser" ]]; then
    success "Correct file ownership on /app/logs"
else
    warning "File ownership issue on /app/logs: $LOG_PERMS"
fi

echo ""
echo "7. Checking Environment Configuration..."
if [[ -f "deployment/docker/.env.example" ]]; then
    success "Environment template found"
else
    error "Missing .env.example file"
fi

echo ""
echo "8. Checking Docker Compose Security..."
if grep -q "restart: unless-stopped" deployment/docker/docker-compose.yml; then
    success "Restart policy configured"
else
    warning "No restart policy found"
fi

if grep -q "resources:" deployment/docker/docker-compose.yml; then
    success "Resource limits configured"
else
    warning "No resource limits found"
fi

if grep -q "networks:" deployment/docker/docker-compose.yml; then
    success "Custom networks configured"
else
    warning "No custom networks found"
fi

echo ""
echo "9. Checking for Hardcoded Secrets..."
SECRETS_FOUND=0

# Check for common hardcoded patterns
if grep -r "password.*=" deployment/docker/docker-compose.yml | grep -v "\${" | grep -v "example"; then
    error "Potential hardcoded passwords found"
    SECRETS_FOUND=1
fi

if grep -r "secret.*=" deployment/docker/docker-compose.yml | grep -v "\${" | grep -v "example"; then
    error "Potential hardcoded secrets found"  
    SECRETS_FOUND=1
fi

if [[ $SECRETS_FOUND -eq 0 ]]; then
    success "No hardcoded secrets detected"
fi

echo ""
echo "10. Checking .dockerignore..."
if [[ -f "deployment/docker/.dockerignore" ]]; then
    if grep -q ".env" deployment/docker/.dockerignore; then
        success ".dockerignore excludes sensitive files"
    else
        warning ".dockerignore missing sensitive file exclusions"
    fi
else
    error "Missing .dockerignore file"
fi

echo ""
echo "=================================="
echo "🔒 Security Validation Complete"
echo ""

# Summary
echo "RECOMMENDATIONS:"
echo "• Test the complete deployment with: docker-compose up -d"
echo "• Verify health checks with: docker-compose ps"
echo "• Check logs with: docker-compose logs app"
echo "• Run security scan with: docker run --rm aquasec/trivy image audio-processor:latest"
echo "• Review .env file and set strong passwords"
echo ""
echo "For production deployment, ensure:"
echo "• SSL/TLS certificates are configured"
echo "• Database passwords are cryptographically secure"
echo "• Network access is properly restricted"
echo "• Monitoring and alerting are configured"
