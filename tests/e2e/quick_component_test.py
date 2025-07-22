#!/usr/bin/env python3
"""
Quick E2E Component Test

This script tests individual components to make sure they work before running the full suite.
"""

import sys
from pathlib import Path

# Setup paths
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

import pytest


def main():
    """Run quick component tests."""
    print("🔍 Running quick E2E component tests...")

    # Test the environment setup
    print("\n1. Testing environment configuration...")
    exit_code = pytest.main([
        "tests/unit/test_environment.py",
        "-v", "--tb=short"
    ])

    if exit_code != 0:
        print("❌ Environment tests failed")
        return False

    print("✅ Environment tests passed")

    # Test the E2E configuration tests (that don't require server)
    print("\n2. Testing E2E configuration...")
    exit_code = pytest.main([
        "tests/e2e/test_e2e_real_audio.py::test_openrouter_config",
        "-v", "--tb=short"
    ])

    if exit_code != 0:
        print("❌ E2E configuration tests failed")
        return False

    print("✅ E2E configuration tests passed")

    # Check audio files
    print("\n3. Checking test audio files...")
    audio_dir = project_root / "tests" / "data" / "audio"

    if not audio_dir.exists():
        print(f"❌ Audio directory not found: {audio_dir}")
        return False

    audio_files = list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.mp3"))

    if not audio_files:
        print(f"❌ No audio files found in {audio_dir}")
        return False

    print(f"✅ Found {len(audio_files)} audio files:")
    for file in audio_files:
        print(f"   - {file.name} ({file.stat().st_size} bytes)")

    print("\n🎉 All component tests passed! Ready for full E2E testing.")
    return True

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
