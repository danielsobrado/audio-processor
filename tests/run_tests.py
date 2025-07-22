#!/usr/bin/env python3
"""
Test runner script for running all tests with pytest.
This script replaces the legacy test execution methods.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_pytest(test_path: str = "", verbose: bool = True, markers: str = ""):
    """
    Run pytest with the specified parameters.

    Args:
        test_path: Specific test path to run (default: all tests)
        verbose: Enable verbose output
        markers: Pytest markers to filter tests
    """
    cmd = ["uv", "run", "pytest"]

    if verbose:
        cmd.append("-v")

    if markers:
        cmd.extend(["-m", markers])

    if test_path:
        cmd.append(test_path)
    else:
        cmd.append("tests/")

    # Add pytest-asyncio support
    cmd.append("--asyncio-mode=auto")

    # Show local variables in tracebacks
    cmd.append("--tb=short")

    # Capture stdout
    cmd.append("-s")

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


def main():
    """Main function to handle command line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Run tests with pytest")
    parser.add_argument("test_path", nargs="?", default="", help="Specific test path to run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-m", "--markers", help="Pytest markers to filter tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run only end-to-end tests")
    parser.add_argument("--quick", action="store_true", help="Run quick tests (unit + integration)")

    args = parser.parse_args()

    # Determine test path based on arguments
    test_path = args.test_path

    if args.unit:
        test_path = "tests/unit/"
    elif args.integration:
        test_path = "tests/integration/"
    elif args.e2e:
        test_path = "tests/e2e/"
    elif args.quick:
        test_path = "tests/unit/ tests/integration/"

    # Run the tests
    exit_code = run_pytest(
        test_path=test_path,
        verbose=args.verbose,
        markers=args.markers
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
