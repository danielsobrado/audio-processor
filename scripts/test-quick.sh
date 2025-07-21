#!/bin/bash

# Quick Test Runner for WSL/Linux - Runs fast tests only
# Usage: ./test-quick.sh

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;96m'
NC='\033[0m'

export ENVIRONMENT=testing
export PYTHONPATH="$(pwd)"

echo -e "${CYAN}=== Quick Test Runner (WSL/Linux) ===${NC}"
echo -e "${YELLOW}Running unit tests and fast integration tests...${NC}"
echo

# Check for uv
if command -v uv &> /dev/null; then
    uv run pytest -v -m "not slow" --tb=short
else
    pytest -v -m "not slow" --tb=short
fi

if [[ $? -eq 0 ]]; then
    echo
    echo -e "${GREEN}✓ Quick tests passed!${NC}"
else
    echo
    echo -e "${RED}✗ Some quick tests failed!${NC}"
    exit 1
fi
