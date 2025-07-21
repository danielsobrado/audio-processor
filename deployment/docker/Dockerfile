# Multi-stage build for optimal security and size
FROM python:3.12-slim as base

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Development stage (includes dev dependencies)
FROM base as builder

# Copy application code for building
COPY . .

# Clean any existing .venv that might have been copied
RUN rm -rf .venv

# Install all dependencies including dev and the project itself
RUN uv sync --frozen

# Production dependencies only
FROM base as prod-deps

# Copy application code for production dependencies
COPY . .

# Install only production dependencies and the project
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.12-slim as production

# Install system dependencies and security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for audio processing
    ffmpeg \
    # Required for health checks
    curl \
    # Security updates
    && apt-get upgrade -y \
    # Clean up to reduce image size
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get autoclean

# Create non-root user with specific UID for security
RUN groupadd -r appuser --gid=1000 && \
    useradd -r -g appuser --uid=1000 --home=/app --shell=/bin/bash appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=prod-deps --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser . .

# Ensure virtual environment is in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/temp && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Use exec form for proper signal handling
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# Development stage (for development docker-compose)
FROM python:3.12-slim as development

# Install system dependencies (same as production)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    # Additional dev tools
    git \
    vim \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get autoclean

# Create non-root user
RUN groupadd -r appuser --gid=1000 && \
    useradd -r -g appuser --uid=1000 --home=/app --shell=/bin/bash appuser

WORKDIR /app

# Copy virtual environment with dev dependencies
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser . .

# Ensure virtual environment is in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create directories
RUN mkdir -p /app/logs /app/temp && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Development command with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
