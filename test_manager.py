#!/usr/bin/env python3
"""
Comprehensive test management script.
Replaces the old bash scripts with a unified Python-based approach.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, env=None):
    """Run a command and return the exit code."""
    if cwd is None:
        cwd = Path(__file__).parent

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, env=env)
    return result.returncode


def setup_environment():
    """Set up the test environment."""
    print("Setting up test environment...")

    # Check if required files exist
    env_test = Path(".env.test")
    if not env_test.exists():
        print("❌ .env.test file not found!")
        return False

    # Check Docker services
    docker_check = run_command(["docker", "ps", "--format", "table {{.Names}}"])
    if docker_check != 0:
        print("❌ Docker not running or not accessible!")
        return False

    print("✅ Test environment setup complete")
    return True


def run_unit_tests():
    """Run unit tests."""
    print("Running unit tests...")
    return run_command(
        ["uv", "run", "pytest", "tests/unit/", "-v", "--asyncio-mode=auto", "-m", "not slow"]
    )


def run_integration_tests():
    """Run integration tests."""
    print("Running integration tests...")
    return run_command(["uv", "run", "pytest", "tests/integration/", "-v", "--asyncio-mode=auto"])


def run_e2e_tests():
    """Run end-to-end tests."""
    print("Running end-to-end tests...")

    # Check if services are running
    print("Checking required services...")
    services_ok = True

    try:
        # Check API server
        import asyncio

        import httpx

        async def check_api():
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get("http://localhost:8000/health")
                    return response.status_code == 200
            except Exception:
                return False

        api_ok = asyncio.run(check_api())
        if not api_ok:
            print("❌ API server not responding at http://localhost:8000")
            services_ok = False
        else:
            print("✅ API server is running")
    except ImportError:
        print("⚠️  Cannot check API server (httpx not installed)")

    # Check Docker services
    docker_services = ["neo4j", "redis", "postgres"]
    for service in docker_services:
        result = run_command(
            ["docker", "ps", "--filter", f"name={service}", "--format", "{{.Names}}"]
        )
        if result != 0:
            print(f"❌ {service} service not running")
            services_ok = False
        else:
            print(f"✅ {service} service is running")

    if not services_ok:
        print("\n❌ Some required services are not running!")
        print("Please start all required services before running E2E tests.")
        return 1

    # Run E2E tests
    return run_command(
        [
            "uv",
            "run",
            "pytest",
            "tests/e2e/",
            "-v",
            "--asyncio-mode=auto",
            "-s",  # Show print statements
        ]
    )


def run_e2e_component_test():
    """Run quick E2E component tests without server."""
    print("Running E2E component tests...")
    return run_command(["python", "tests/e2e/quick_component_test.py"])


def run_e2e_full_with_server():
    """Run full E2E tests with real audio and server."""
    print("Running full E2E tests with server and real audio...")
    return run_command(["python", "tests/e2e/run_full_e2e_with_server.py"])


def run_quick_tests():
    """Run quick tests (unit + integration)."""
    print("Running quick tests (unit + integration)...")
    unit_result = run_unit_tests()
    if unit_result != 0:
        return unit_result
    return run_integration_tests()


def run_all_tests():
    """Run all tests."""
    print("Running all tests...")
    unit_result = run_unit_tests()
    integration_result = run_integration_tests()
    e2e_result = run_e2e_tests()

    # Return non-zero if any test failed
    if unit_result != 0 or integration_result != 0 or e2e_result != 0:
        return 1
    return 0


def clean_test_artifacts():
    """Clean up test artifacts."""
    print("Cleaning test artifacts...")

    artifacts = [
        "test.db",
        "test.db-shm",
        "test.db-wal",
        ".pytest_cache",
        "__pycache__",
        "*.pyc",
        ".coverage",
        "htmlcov/",
        ".tox/",
        ".mypy_cache/",
    ]

    for artifact in artifacts:
        if "*" in artifact:
            # Use shell expansion for wildcards
            run_command(["find", ".", "-name", artifact, "-delete"])
        else:
            path = Path(artifact)
            if path.exists():
                if path.is_dir():
                    import shutil

                    shutil.rmtree(path)
                else:
                    path.unlink()
                print(f"Removed: {artifact}")


def main():
    parser = argparse.ArgumentParser(description="Test management script")
    parser.add_argument(
        "command",
        choices=[
            "setup",
            "unit",
            "integration",
            "e2e",
            "e2e-component",
            "e2e-full",
            "quick",
            "all",
            "clean",
        ],
        help="Test command to run",
    )

    args = parser.parse_args()

    if args.command == "setup":
        success = setup_environment()
        sys.exit(0 if success else 1)
    elif args.command == "unit":
        sys.exit(run_unit_tests())
    elif args.command == "integration":
        sys.exit(run_integration_tests())
    elif args.command == "e2e":
        sys.exit(run_e2e_tests())
    elif args.command == "e2e-component":
        sys.exit(run_e2e_component_test())
    elif args.command == "e2e-full":
        sys.exit(run_e2e_full_with_server())
    elif args.command == "quick":
        sys.exit(run_quick_tests())
    elif args.command == "all":
        sys.exit(run_all_tests())
    elif args.command == "clean":
        clean_test_artifacts()
        sys.exit(0)


if __name__ == "__main__":
    main()
