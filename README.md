# Audio Processor

An advanced audio processing application focused on transcription, diarization, summarization, and translation, with robust support for both English and Arabic languages. This project provides a scalable and efficient solution for handling various audio processing tasks.

## Features

*   **Multilingual Transcription**: Accurately transcribes audio in both English and Arabic.
*   **Speaker Diarization**: Identifies and separates different speakers in an audio recording.
*   **Audio Summarization**: Generates concise summaries from transcribed audio content.
*   **Translation**: Translates transcribed content.
*   **Graph Database Integration**: Neo4j-powered conversation analysis with speaker networks and topic flows.
*   **Speaker Network Analysis**: Analyze interaction patterns, speaking time, and turn-taking behaviors.
*   **Topic Flow Tracking**: Track conversation transitions and keyword-based topic extraction.
*   **Entity Extraction**: Identify and link structured data (emails, phones, dates, URLs, mentions).
*   **Asynchronous Processing**: Utilizes a job queue (Celery) for efficient handling of long-running audio processing tasks.
*   **RESTful API**: Provides a clean and well-documented API for interacting with the service.
*   **Containerized Deployment**: Docker and Kubernetes support for easy deployment and scaling.
*   **Database Integration**: Stores job results and metadata.

## Technologies Used

*   **Backend**: Python 3.12+, FastAPI
*   **Audio Processing**: WhisperX use Deepgram API compatible responses
*   **Task Queue**: Celery, Redis (as broker and backend)
*   **Database**: PostgreSQL (via SQLAlchemy)
*   **Graph Database**: Neo4j (for conversation analysis)
*   **Migrations**: Alembic
*   **Containerization**: Docker
*   **Orchestration**: Kubernetes
*   **Dependency Management**: uv (fast Python package manager)
*   **Testing**: Pytest with comprehensive test infrastructure

## Setup and Installation

Follow these steps to set up the project locally.

### Prerequisites

*   Python 3.12+
*   uv (recommended for dependency management, install from [astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/))
*   Docker (for running services like Redis and PostgreSQL)
*   Deepgram API Key (get one from [Deepgram](https://deepgram.com/))

> **Note**: This project has migrated from Poetry to uv for faster dependency management. If you have an existing setup with Poetry, you can migrate by running `uv sync --dev` after installing uv.

### 1. Clone the repository

```bash
git clone https://github.com/xxxx/audio-processor.git
cd audio-processor
```

### 2. Set up Environment Variables

Copy the example environment file and update it with your Deepgram API key and other configurations.

```bash
cp .env.example .env
```

Edit the `.env` file and fill in your `DEEPGRAM_API_KEY`. You might also want to adjust database or Redis connection settings if you're not using the default Docker setup.

### 3. Install Dependencies

Using uv (recommended):

```bash
uv sync --dev
```

If you prefer pip:

```bash
pip install -r requirements.txt
```

### 4. Install uv (if not already installed)

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Verify installation:**
```bash
uv --version
```

### 5. Database Setup

Ensure Docker is running. Then, start the PostgreSQL and Redis containers using Docker Compose:

```bash
docker-compose -f deployment/docker/docker-compose.yml up -d db redis
```

Run database migrations:

```bash
uv run alembic upgrade head
```

If you're not using uv:

```bash
alembic upgrade head
```

### 6. Graph Database Setup (Optional)

The application includes optional Neo4j integration for conversation analysis. To enable graph functionality:

**Start Neo4j with Docker:**
```bash
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15-community
```

**Enable in configuration:**
Edit your environment-specific YAML config file (e.g., `config/development.yaml`):
```yaml
graph:
  enabled: true
  neo4j:
    url: "bolt://localhost:7687"
    username: "neo4j"
    password: "password"
```

**Access Neo4j Browser:**
- URL: http://localhost:7474
- Username: neo4j
- Password: password

The graph functionality is completely optional and the application will work normally with `graph.enabled: false`.

**Graph Visualization:**
The Neo4j Browser provides built-in graph visualization capabilities. For custom visualizations, you can use the graph API endpoints to export data for tools like:
- D3.js for web-based visualizations
- Cytoscape.js for network analysis
- Gephi for advanced graph analytics

## Running the Application

### Locally (Development)

1.  **Start Services**: Ensure PostgreSQL and Redis are running (e.g., via `docker-compose up -d db redis`).
2.  **Run FastAPI Application**:
    ```bash
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    If you're not using uv:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    The API will be available at `http://localhost:8000`.

3.  **Run Celery Worker**: Open a new terminal and run:
    ```bash
    uv run celery -A app.workers.celery_app worker -l info
    ```
    If you're not using uv:
    ```bash
    celery -A app.workers.celery_app worker -l info
    ```
    This worker will process the audio tasks.

### Using Docker Compose

For a full local deployment including the FastAPI app, Celery worker, Redis, and PostgreSQL:

```bash
docker-compose -f deployment/docker/docker-compose.yml up --build -d
```

This will build the Docker images and start all necessary services. The API will be available at `http://localhost:8000`.

### Deployment on Kubernetes

The `deployment/kubernetes` directory contains YAML files for deploying the application to a Kubernetes cluster.

1.  **Build and Push Docker Images**:
    You'll need to build your Docker image and push it to a container registry accessible by your Kubernetes cluster.
    ```bash
    docker build -t your-registry/audio-processor:latest -f deployment/docker/Dockerfile .
    docker push your-registry/audio-processor:latest
    ```
    Remember to update the `image` field in `deployment/kubernetes/deployment.yaml` to point to your image.

2.  **Apply Kubernetes Manifests**:
    ```bash
    kubectl apply -f deployment/kubernetes/namespace.yaml
    kubectl apply -f deployment/kubernetes/configmap.yaml
    kubectl apply -f deployment/kubernetes/secrets.yaml # Ensure secrets are properly managed
    kubectl apply -f deployment/kubernetes/pvc.yaml
    kubectl apply -f deployment/kubernetes/deployment.yaml
    kubectl apply -f deployment/kubernetes/service.yaml
    kubectl apply -f deployment/kubernetes/ingress.yaml # If you have an Ingress controller
    kubectl apply -f deployment/kubernetes/hpa.yaml # For Horizontal Pod Autoscaling
    ```

## Dependency Management

This project uses [uv](https://docs.astral.sh/uv/) for fast and reliable dependency management.

### Adding Dependencies

```bash
# Add a production dependency
uv add package-name

# Add a development dependency  
uv add --dev package-name

# Add specific version
uv add "package-name>=1.0.0,<2.0.0"
```

### Managing Dependencies

```bash
# Install all dependencies (including dev)
uv sync --dev

# Install only production dependencies
uv sync --no-dev

# Update dependencies
uv sync

# Remove a dependency
uv remove package-name

# Show dependency tree
uv tree
```

### Why uv?

- **10-100x faster** than pip and poetry
- **Better caching** and dependency resolution
- **Single tool** for dependency management, virtual environments, and package building
- **Drop-in replacement** with familiar commands
- **Cross-platform consistency**

## Development Commands

### Quick Reference

```bash
# Setup project
uv sync --dev

# Start development server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Code formatting and linting
uv run black .
uv run isort .
uv run flake8 .
uv run mypy .

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"

# Start Celery worker
uv run celery -A app.workers.celery_app worker -l info
```

## API Endpoints

You can access the API documentation at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc) when the application is running.

Key endpoints include:

*   `POST /api/v1/transcribe`: Submits an audio file for transcription, diarization, summarization, and/or translation.
*   `GET /api/v1/status/{job_id}`: Checks the status of a submitted job.
*   `GET /api/v1/results/{job_id}`: Retrieves the results of a completed job.
*   `GET /api/v1/health`: Health check endpoint.

**Graph API Endpoints (when enabled):**
*   `GET /api/v1/graph/stats`: Graph database statistics and connection status.
*   `GET /api/v1/graph/speakers`: List all speakers and their interaction patterns.
*   `GET /api/v1/graph/topics`: List all topics and their relationships.
*   `GET /api/v1/graph/conversations/{conversation_id}`: Get complete conversation graph.
*   `GET /api/v1/graph/speakers/{speaker_id}/network`: Get speaker's interaction network.
*   `GET /api/v1/graph/topics/{topic_id}/flow`: Get topic flow and transitions.

## Configuration

Configuration settings are managed through environment variables and YAML files located in the `config/` directory.

*   `.env`: Local environment variables (sensitive data like API keys).
*   `config/`: Contains environment-specific configurations (e.g., `development.yaml`, `production.yaml`).

## Testing

### Using Test Scripts (Recommended)

**Windows:**
```cmd
# First time setup
scripts\setup-tests.bat

# Run all tests
scripts\run-tests.bat

# Run with coverage
scripts\run-tests.bat coverage

# Quick tests only
scripts\test-quick.bat
```

**Linux/WSL:**
```bash
# First time setup
./scripts/setup-tests.sh

# Run all tests
./scripts/run-tests.sh

# Run with coverage
./scripts/run-tests.sh coverage

# Quick tests only
./scripts/test-quick.sh
```

**PowerShell:**
```powershell
# Run all tests
.\scripts\run-tests.ps1

# Run with coverage
.\scripts\run-tests.ps1 coverage
```

### Direct Commands

Using uv:
```bash
uv run pytest
```

With coverage:
```bash
uv run pytest --cov=app --cov-report=html
```

If you're not using uv:
```bash
pytest
```

### Test Documentation

See `tests/TESTING.md` for comprehensive testing documentation including:
- Test environment setup
- Available test types (unit, integration, coverage)
- Troubleshooting guide
- Cross-platform compatibility

## Troubleshooting

### Common Issues

1. **uv not found**: Install uv from [astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/)

2. **Permission denied (Linux/WSL)**: Make scripts executable:
   ```bash
   chmod +x scripts/*.sh
   ```

3. **Tests failing**: Ensure environment variables are set:
   ```bash
   cp .env.example .env.test
   # Edit .env.test with test-specific values
   ```

4. **Dependencies not installing**: Try clearing cache and reinstalling:
   ```bash
   uv clean
   uv sync --dev
   ```

5. **Port already in use**: Change the port in your .env file or kill the process:
   ```bash
   # Find process using port 8000
   lsof -i :8000  # macOS/Linux
   netstat -ano | findstr :8000  # Windows
   ```

### Performance Tips

- Use `uv run` for consistent dependency management
- Keep `.env.test` for isolated test environments
- Use Docker for external services (Redis, PostgreSQL)
- Monitor Celery worker logs for task processing issues

### Getting Help

- Check logs: `docker-compose logs` for containerized services
- Verify environment: Run environment tests with `scripts/run-tests.sh env`
- Review documentation: See `tests/TESTING.md` for testing details

## Contributing

Contributions are welcome! Please follow standard GitHub practices: fork the repository, create a new branch, commit your changes, and open a pull request.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
