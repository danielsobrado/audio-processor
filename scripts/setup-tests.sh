#!/bin/bash

# Test Environment Setup for WSL/Linux
# Usage: ./setup-tests.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;96m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m'

echo -e "${CYAN}=== Audio Processor Test Environment Setup (WSL/Linux) ===${NC}"
echo

# Check if .env.test exists, if not create from example
if [[ ! -f ".env.test" ]]; then
    if [[ -f ".env.example" ]]; then
        echo -e "${YELLOW}Creating .env.test from .env.example...${NC}"
        cp ".env.example" ".env.test"
        echo -e "${GREEN}✓ .env.test created${NC}"
    else
        echo -e "${RED}Error: .env.example not found!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env.test already exists${NC}"
fi

# Make scripts executable
echo -e "${BLUE}Making scripts executable...${NC}"
chmod +x scripts/*.sh 2>/dev/null || true
echo -e "${GREEN}✓ Scripts made executable${NC}"

# Check for Poetry
echo -e "${BLUE}Checking for Poetry...${NC}"
if command -v poetry &> /dev/null; then
    echo -e "${GREEN}✓ Poetry found${NC}"
    echo -e "${BLUE}Installing dependencies with Poetry...${NC}"
    poetry install
    echo -e "${GREEN}✓ Dependencies installed${NC}"
elif command -v pip &> /dev/null; then
    echo -e "${YELLOW}Poetry not found, using pip...${NC}"
    echo -e "${GREEN}✓ pip found${NC}"
    echo -e "${BLUE}Installing test dependencies...${NC}"
    pip install pytest pytest-asyncio pytest-cov httpx
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}Error: Neither Poetry nor pip found!${NC}"
    exit 1
fi

# Test the setup
echo
echo -e "${BLUE}Testing environment setup...${NC}"
export ENVIRONMENT=testing

if [[ -f "scripts/run-tests.sh" ]]; then
    echo -e "${BLUE}Running environment tests...${NC}"
    ./scripts/run-tests.sh env
    
    echo
    echo -e "${GREEN}=== Test environment setup complete! ===${NC}"
    echo
    echo -e "${CYAN}You can now run tests with:${NC}"
    echo -e "${WHITE}  ./scripts/run-tests.sh           ${GRAY}# Run all tests${NC}"
    echo -e "${WHITE}  ./scripts/run-tests.sh unit      ${GRAY}# Run unit tests${NC}"
    echo -e "${WHITE}  ./scripts/run-tests.sh coverage  ${GRAY}# Run with coverage${NC}"
    echo -e "${WHITE}  ./scripts/test-quick.sh          ${GRAY}# Run fast tests only${NC}"
    echo
    echo -e "${CYAN}Available test types:${NC}"
    echo -e "${WHITE}  all, unit, integration, coverage, fast, env, watch, debug${NC}"
else
    echo -e "${RED}Error: scripts/run-tests.sh not found!${NC}"
    exit 1
fi