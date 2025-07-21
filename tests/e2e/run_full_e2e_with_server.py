#!/usr/bin/env python3
"""
Full E2E Test Runner with Real Audio Processing

This script:
1. Starts the FastAPI server in test mode
2. Waits for the server to be ready
3. Runs comprehensive E2E tests with real audio files
4. Cleans up and reports results

Usage:
    python tests/e2e/run_full_e2e_with_server.py
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

# Setup paths
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

# Load test environment
load_dotenv(project_root / ".env.test")

# Set test environment variables
os.environ.update({
    "ENVIRONMENT": "testing",
    "DEBUG": "True",
    "SECRET_KEY": "test-secret-key-for-testing-only",
    "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
    "REDIS_URL": "redis://localhost:6379/15",
    "CELERY_BROKER_URL": "memory://localhost/",
    "CELERY_RESULT_BACKEND": "cache+memory://",
    "CELERY_ACCEPT_CONTENT": '["json"]',
    "LOG_LEVEL": "INFO",
    "WHISPERX_MODEL_SIZE": "tiny",
    "ENABLE_AUDIO_UPLOAD": "True",
    "ENABLE_URL_PROCESSING": "True",
    "ENABLE_TRANSLATION": "False",
    "ENABLE_SUMMARIZATION": "False",
    "GRAPH_ENABLED": "True",
    "GRAPH_DATABASE_URL": "bolt://localhost:7687",
    "GRAPH_DATABASE_USERNAME": "neo4j",
    "GRAPH_DATABASE_PASSWORD": "devpassword",
    "JWT_VERIFY_SIGNATURE": "False",
    "JWT_VERIFY_AUDIENCE": "False",
    "DIARIZATION_ENABLED": "false",
})

# Configuration
API_BASE_URL = "http://localhost:8000"
SERVER_START_TIMEOUT = 60  # seconds
HEALTH_CHECK_INTERVAL = 2  # seconds
TEST_AUDIO_DIR = project_root / "tests" / "data" / "audio"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class E2ETestRunner:
    """Manages the full E2E test process with server lifecycle."""

    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self.celery_process: Optional[subprocess.Popen] = None

    async def wait_for_server(self, timeout: int = SERVER_START_TIMEOUT) -> bool:
        """Wait for the API server to be ready."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{API_BASE_URL}/health")
                    if response.status_code == 200:
                        logger.info("API server is ready!")
                        return True
            except Exception as e:
                logger.debug(f"Server not ready yet: {e}")

            await asyncio.sleep(HEALTH_CHECK_INTERVAL)

        return False

    def start_server(self) -> bool:
        """Start the FastAPI server in test mode."""
        try:
            logger.info("Starting FastAPI server...")

            # Start the server using uvicorn
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--log-level", "info"
            ]

            self.server_process = subprocess.Popen(
                cmd,
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy()
            )

            logger.info(f"Server started with PID: {self.server_process.pid}")
            return True

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False

    def start_celery_worker(self) -> bool:
        """Start Celery worker for background task processing."""
        try:
            logger.info("Starting Celery worker...")

            cmd = [
                sys.executable, "-m", "celery",
                "worker",
                "-A", "app.workers.celery_app",
                "--loglevel=info",
                "--pool=solo"  # Use solo pool for Windows compatibility
            ]

            self.celery_process = subprocess.Popen(
                cmd,
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy()
            )

            logger.info(f"Celery worker started with PID: {self.celery_process.pid}")
            return True

        except Exception as e:
            logger.error(f"Failed to start Celery worker: {e}")
            return False

    def stop_processes(self):
        """Stop the server and Celery worker."""
        if self.server_process:
            logger.info("Stopping API server...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            except Exception as e:
                logger.error(f"Error stopping server: {e}")

        if self.celery_process:
            logger.info("Stopping Celery worker...")
            try:
                self.celery_process.terminate()
                self.celery_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.celery_process.kill()
            except Exception as e:
                logger.error(f"Error stopping Celery worker: {e}")

    async def run_e2e_tests(self) -> bool:
        """Run the E2E tests with real audio files."""
        try:
            logger.info("Running E2E tests...")

            # Run the comprehensive E2E test
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/e2e/test_e2e_real_audio.py::test_comprehensive_audio_processing",
                "-v", "--tb=short"
            ]

            process = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                env=os.environ.copy()
            )

            logger.info(f"Test exit code: {process.returncode}")
            if process.stdout:
                logger.info(f"Test output:\n{process.stdout}")
            if process.stderr:
                logger.error(f"Test errors:\n{process.stderr}")

            return process.returncode == 0

        except Exception as e:
            logger.error(f"Failed to run E2E tests: {e}")
            return False

    async def run_health_checks(self) -> bool:
        """Run basic health checks."""
        try:
            logger.info("Running health checks...")

            cmd = [
                sys.executable, "-m", "pytest",
                "tests/e2e/test_e2e_real_audio.py::test_api_health",
                "tests/e2e/test_e2e_real_audio.py::test_openrouter_config",
                "tests/e2e/test_e2e_real_audio.py::test_neo4j_connection",
                "-v"
            ]

            process = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                env=os.environ.copy()
            )

            logger.info(f"Health check exit code: {process.returncode}")
            if process.stdout:
                logger.info(f"Health check output:\n{process.stdout}")

            return process.returncode == 0

        except Exception as e:
            logger.error(f"Failed to run health checks: {e}")
            return False

    def check_audio_files(self) -> bool:
        """Check if test audio files are available."""
        if not TEST_AUDIO_DIR.exists():
            logger.error(f"Audio directory not found: {TEST_AUDIO_DIR}")
            return False

        audio_files = list(TEST_AUDIO_DIR.glob("*.wav")) + list(TEST_AUDIO_DIR.glob("*.mp3"))

        if not audio_files:
            logger.error(f"No audio files found in {TEST_AUDIO_DIR}")
            return False

        logger.info(f"Found {len(audio_files)} audio files:")
        for file in audio_files:
            logger.info(f"  - {file.name} ({file.stat().st_size} bytes)")

        return True

    async def run_full_test_suite(self) -> bool:
        """Run the complete E2E test suite."""
        try:
            # Check prerequisites
            logger.info("=== Starting Full E2E Test Suite ===")

            if not self.check_audio_files():
                return False

            # Start services
            if not self.start_server():
                return False

            if not self.start_celery_worker():
                return False

            # Wait for server to be ready
            logger.info("Waiting for API server to be ready...")
            if not await self.wait_for_server():
                logger.error("Server failed to start within timeout")
                return False

            # Run health checks first
            logger.info("=== Running Health Checks ===")
            health_ok = await self.run_health_checks()
            if not health_ok:
                logger.warning("Some health checks failed, but continuing with tests...")

            # Run comprehensive E2E tests
            logger.info("=== Running Real Audio E2E Tests ===")
            tests_ok = await self.run_e2e_tests()

            if tests_ok:
                logger.info("🎉 All E2E tests passed!")
            else:
                logger.error("❌ Some E2E tests failed")

            return tests_ok

        except Exception as e:
            logger.error(f"Error running test suite: {e}")
            return False
        finally:
            self.stop_processes()


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    logger.info("Received interrupt signal, shutting down...")
    sys.exit(0)


async def main():
    """Main entry point."""
    signal.signal(signal.SIGINT, signal_handler)

    runner = E2ETestRunner()

    try:
        success = await runner.run_full_test_suite()

        if success:
            logger.info("✅ Full E2E test suite completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ E2E test suite failed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Test suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        runner.stop_processes()


if __name__ == "__main__":
    asyncio.run(main())
