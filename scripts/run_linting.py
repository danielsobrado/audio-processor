#!/usr/bin/env python3
"""
Manual code quality checks script.

This script runs more comprehensive linting checks that are not included
in the pre-commit hooks to avoid being too intrusive during development.

Usage:
    python scripts/run_linting.py [--fix] [--all]

    --fix: Attempt to automatically fix issues where possible
    --all: Run all checks including mypy and pydocstyle
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str, fix_mode: bool = False) -> bool:
    """Run a command and return True if successful."""
    print(f"\n🔍 {description}...")
    try:
        if fix_mode:
            # Add fix flag for tools that support it
            if "ruff" in cmd and "check" in cmd:
                cmd = cmd + ["--fix"]
            elif "ruff" in cmd and "format" in cmd and "--check" in cmd:
                # For format, remove --check when fixing
                cmd = [c for c in cmd if c != "--check"]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ {description} passed")
            if result.stdout.strip():
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} failed")
            if result.stdout.strip():
                print("STDOUT:", result.stdout)
            if result.stderr.strip():
                print("STDERR:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run comprehensive code quality checks")
    parser.add_argument("--fix", action="store_true", help="Attempt to automatically fix issues")
    parser.add_argument("--all", action="store_true", help="Run all checks including mypy and pydocstyle")
    args = parser.parse_args()

    # Change to project root
    project_root = Path(__file__).parent.parent
    import os
    os.chdir(project_root)

    print("🧹 Running code quality checks...")
    print(f"📁 Working directory: {project_root}")

    success = True

    # Core checks (always run)
    checks = [
        (["uv", "run", "ruff", "check", "app/"], "Ruff linting (app only)"),
        (["uv", "run", "ruff", "format", "--check", "app/"], "Ruff formatting (app only)"),
    ]

    # Extended checks (only with --all flag)
    if args.all:
        checks.extend([
            (["uv", "run", "mypy", "app/", "--ignore-missing-imports"], "MyPy type checking"),
            (["uv", "run", "pydocstyle", "app/", "--convention=google", "--add-ignore=D100,D101,D102,D103,D104,D105,D106,D107"], "Docstring checking"),
        ])

    for cmd, description in checks:
        if not run_command(cmd, description, args.fix):
            success = False

    # Summary
    print("\n" + "="*50)
    if success:
        print("🎉 All checks passed!")
        if not args.all:
            print("💡 Run with --all for comprehensive checks including mypy and pydocstyle")
    else:
        print("❌ Some checks failed")
        if args.fix:
            print("💡 Some issues may have been automatically fixed. Please review changes.")
        else:
            print("💡 Run with --fix to automatically fix some issues")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
