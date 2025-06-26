# Audio Processor

An advanced audio processing application focused on transcription, diarization, summarization, and translation, with robust support for both English and Arabic languages. This project provides a scalable and efficient solution for handling various audio processing tasks.

## Features

*   **Multilingual Transcription**: Accurately transcribes audio in both English and Arabic.
*   **Speaker Diarization**: Identifies and separates different speakers in an audio recording.
*   **Audio Summarization**: Generates concise summaries from transcribed audio content.
*   **Translation**: Translates transcribed content.
*   **Asynchronous Processing**: Utilizes a job queue (Celery) for efficient handling of long-running audio processing tasks.
*   **RESTful API**: Provides a clean and well-documented API for interacting with the service.
*   **Containerized Deployment**: Docker and Kubernetes support for easy deployment and scaling.
*   **Database Integration**: Stores job results and metadata.

## Technologies Used

*   **Backend**: Python, FastAPI
*   **Audio Processing**: Deepgram API (for transcription, diarization, summarization)
*   **Task Queue**: Celery, Redis (as broker and backend)
*   **Database**: PostgreSQL (via SQLAlchemy)
*   **Migrations**: Alembic
*   **Containerization**: Docker
*   **Orchestration**: Kubernetes
*   **Testing**: Pytest

## Setup and Installation

Follow these steps to set up the project locally.

### Prerequisites

*   Python 3.9+
*   Poetry (recommended for dependency management, install with `pip install poetry`)
*   Docker (for running services like Redis and PostgreSQL)
*   Deepgram API Key (get one from [Deepgram](https://deepgram.com/))

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

Using Poetry:

```bash
poetry install
```

If you prefer pip:

```bash
pip install -r requirements.txt
```

### 4. Database Setup

Ensure Docker is running. Then, start the PostgreSQL and Redis containers using Docker Compose:

```bash
docker-compose -f deployment/docker/docker-compose.yml up -d db redis
```

Run database migrations:

```bash
poetry run alembic upgrade head
```

If you're not using Poetry:

```bash
alembic upgrade head
```

## Running the Application

### Locally (Development)

1.  **Start Services**: Ensure PostgreSQL and Redis are running (e.g., via `docker-compose up -d db redis`).
2.  **Run FastAPI Application**:
    ```bash
    poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    If you're not using Poetry:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    The API will be available at `http://localhost:8000`.

3.  **Run Celery Worker**: Open a new terminal and run:
    ```bash
    poetry run celery -A app.workers.celery_app worker -l info
    ```
    If you're not using Poetry:
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

## API Endpoints

You can access the API documentation at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc) when the application is running.

Key endpoints include:

*   `POST /api/v1/transcribe`: Submits an audio file for transcription, diarization, summarization, and/or translation.
*   `GET /api/v1/status/{job_id}`: Checks the status of a submitted job.
*   `GET /api/v1/results/{job_id}`: Retrieves the results of a completed job.
*   `GET /api/v1/health`: Health check endpoint.

## Configuration

Configuration settings are managed through environment variables and YAML files located in the `config/` directory.

*   `.env`: Local environment variables (sensitive data like API keys).
*   `config/`: Contains environment-specific configurations (e.g., `development.yaml`, `production.yaml`).

## Testing

To run the tests:

```bash
poetry run pytest
```

If you're not using Poetry:

```bash
pytest
```

## Contributing

Contributions are welcome! Please follow standard GitHub practices: fork the repository, create a new branch, commit your changes, and open a pull request.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
