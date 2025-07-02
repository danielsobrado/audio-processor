#!/bin/bash

# Audio Processor - Test Runner for WSL/Linux
# Usage: ./run-tests.sh [test-type] [options]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;96m'
NC='\033[0m' # No Color

# Set test environment
export ENVIRONMENT=testing
export PYTHONPATH="$(pwd)"

echo -e "${CYAN}=== Audio Processor Test Runner (WSL/Linux) ===${NC}"
echo

# Check if .env.test exists
if [[ ! -f ".env.test" ]]; then
    echo -e "${RED}Error: .env.test file not found!${NC}"
    echo "Please ensure .env.test exists before running tests."
    echo "You can copy from .env.example and modify for testing."
    exit 1
fi

# Determine test type
TEST_TYPE=${1:-all}

# Check if poetry is available
if command -v poetry &> /dev/null; then
    echo -e "${GREEN}Using Poetry environment${NC}"
    PYTEST_CMD="poetry run pytest"
elif command -v pytest &> /dev/null; then
    echo -e "${YELLOW}Using system Python environment${NC}"
    PYTEST_CMD="pytest"
else
    echo -e "${RED}Error: pytest not found! Please install pytest or use poetry.${NC}"
    exit 1
fi

echo -e "${CYAN}Running tests with environment: ${ENVIRONMENT}${NC}"
echo

# Function to run tests with error handling
run_test() {
    echo -e "${BLUE}$1${NC}"
    if $PYTEST_CMD "${@:2}"; then
        echo -e "${GREEN}✓ Tests completed successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Tests failed${NC}"
        return 1
    fi
}

# Execute tests based on type
case "$TEST_TYPE" in
    "all")
        run_test "Running all tests..." -v
        ;;
    "unit")
        run_test "Running unit tests..." -v tests/unit/
        ;;
    "integration")
        run_test "Running integration tests..." -v tests/integration/
        ;;
    "coverage")
        run_test "Running tests with coverage..." --cov=app --cov-report=html --cov-report=term-missing -v
        # Open coverage report if available and running in WSL with Windows integration
        if [[ -f "htmlcov/index.html" ]] && command -v explorer.exe &> /dev/null; then
            echo -e "${CYAN}Opening coverage report...${NC}"
            explorer.exe htmlcov/index.html &> /dev/null &
        elif [[ -f "htmlcov/index.html" ]] && command -v xdg-open &> /dev/null; then
            echo -e "${CYAN}Opening coverage report...${NC}"
            xdg-open htmlcov/index.html &> /dev/null &
        fi
        ;;
    "fast")
        run_test "Running fast tests only..." -v -m "not slow"
        ;;
    "env")
        run_test "Running environment tests..." -v tests/unit/test_environment.py
        ;;
    "watch")
        echo -e "${BLUE}Running tests in watch mode...${NC}"
        echo -e "${YELLOW}Note: Install pytest-watch for better watch functionality${NC}"
        $PYTEST_CMD -f
        ;;
    "debug")
        run_test "Running tests with debug output..." -v -s --tb=long
        ;;
    "help"|"-h"|"--help")
        echo -e "${CYAN}Audio Processor Test Runner${NC}"
        echo
        echo "Usage: ./run-tests.sh [test-type] [options]"
        echo
        echo "Test types:"
        echo "  all          Run all tests (default)"
        echo "  unit         Run unit tests only"
        echo "  integration  Run integration tests only"
        echo "  coverage     Run tests with coverage report"
        echo "  fast         Run tests excluding slow ones"
        echo "  env          Run environment configuration tests"
        echo "  watch        Run tests in watch mode"
        echo "  debug        Run tests with verbose debug output"
        echo "  help         Show this help message"
        echo
        echo "Examples:"
        echo "  ./run-tests.sh                    # Run all tests"
        echo "  ./run-tests.sh unit               # Run unit tests"
        echo "  ./run-tests.sh coverage           # Run with coverage"
        echo "  ./run-tests.sh -v tests/unit/     # Custom pytest options"
        exit 0
        ;;
    *)
        echo -e "${YELLOW}Running custom test: $*${NC}"
        $PYTEST_CMD "$@"
        ;;
esac

TEST_EXIT_CODE=$?

echo
if [[ $TEST_EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}=== All tests passed! ===${NC}"
else
    echo -e "${RED}=== Some tests failed! ===${NC}"
fi

exit $TEST_EXIT_CODE