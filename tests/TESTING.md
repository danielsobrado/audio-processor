# Test Scripts Documentation

This directory contains comprehensive test runner scripts for both Windows and WSL/Linux environments.

## Quick Start

### Windows (Command Prompt)
```cmd
# Setup test environment (first time only)
scripts\setup-tests.bat

# Run all tests
scripts\run-tests.bat

# Run quick tests
scripts\test-quick.bat
```

### Windows (PowerShell)
```powershell
# Setup test environment (first time only)
.\scripts\setup-tests.bat

# Run all tests
.\scripts\run-tests.ps1

# Run with coverage
.\scripts\run-tests.ps1 coverage
```

### WSL/Linux
```bash
# Setup test environment (first time only)
./scripts/setup-tests.sh

# Run all tests
./scripts/run-tests.sh

# Run quick tests
./scripts/test-quick.sh
```

## Available Scripts

### Setup Scripts
- **`scripts/setup-tests.bat`** / **`scripts/setup-tests.sh`** - First-time environment setup
  - Creates `.env.test` from `.env.example`
  - Installs dependencies (Poetry or pip)
  - Makes scripts executable (Linux/WSL)
  - Runs environment validation tests

### Main Test Runners
- **`scripts/run-tests.bat`** - Windows Command Prompt test runner
- **`scripts/run-tests.sh`** - WSL/Linux bash test runner  
- **`scripts/run-tests.ps1`** - Windows PowerShell test runner

### Quick Test Scripts
- **`scripts/test-quick.bat`** / **`scripts/test-quick.sh`** - Fast tests only (excludes slow tests)

## Test Types

All main test runners support these test types:

| Type | Description |
|------|-------------|
| `all` | Run all tests (default) |
| `unit` | Run unit tests only |
| `integration` | Run integration tests only |
| `coverage` | Run tests with coverage report |
| `fast` | Run tests excluding slow ones |
| `env` | Run environment configuration tests |
| `watch` | Run tests in watch mode |
| `debug` | Run tests with verbose debug output |
| `help` | Show help message |

## Examples

### Windows Command Prompt
```cmd
scripts\run-tests.bat                    # All tests
scripts\run-tests.bat unit               # Unit tests only
scripts\run-tests.bat coverage           # With coverage report
scripts\run-tests.bat fast               # Fast tests only
scripts\run-tests.bat debug              # Debug mode
scripts\run-tests.bat -v tests/unit/     # Custom pytest options
```

### PowerShell
```powershell
.\scripts\run-tests.ps1                  # All tests
.\scripts\run-tests.ps1 unit             # Unit tests only
.\scripts\run-tests.ps1 coverage         # With coverage report
.\scripts\run-tests.ps1 help             # Show help
```

### WSL/Linux
```bash
./scripts/run-tests.sh                   # All tests
./scripts/run-tests.sh unit              # Unit tests only
./scripts/run-tests.sh coverage          # With coverage report
./scripts/run-tests.sh fast              # Fast tests only
./scripts/run-tests.sh watch             # Watch mode
./scripts/run-tests.sh help              # Show help
```

## Environment Setup

### Automatic Setup
Run the setup script for your platform:
```bash
# Windows
scripts\setup-tests.bat

# WSL/Linux  
./scripts/setup-tests.sh
```

### Manual Setup
1. **Copy environment file:**
   ```bash
   cp .env.example .env.test
   ```

2. **Install dependencies:**
   ```bash
   # With Poetry (recommended)
   poetry install
   
   # With pip
   pip install pytest pytest-asyncio pytest-cov httpx
   pip install -r requirements.txt
   ```

3. **Make scripts executable (WSL/Linux only):**
   ```bash
   chmod +x scripts/*.sh
   ```

## Test Configuration

### Environment Variables
Tests automatically use the `testing` environment with these settings:
- **Database**: SQLite in-memory for isolation
- **Redis**: Separate database (DB 15)
- **Celery**: In-memory broker for speed
- **External APIs**: Mocked/disabled
- **Models**: Smallest/fastest configurations

### Pytest Configuration
Settings are in `pyproject.toml`:
- **Test discovery**: `test_*.py` files in `tests/` directory
- **Async support**: Automatic async test detection
- **Markers**: `slow`, `integration`, `unit`
- **Coverage**: Source code analysis with exclusions

## Coverage Reports

When running with coverage, reports are generated in:
- **Terminal**: Summary during test run
- **HTML**: `htmlcov/index.html` (auto-opens on Windows)

Coverage includes:
- **Line coverage** of all app code
- **Missing lines** highlighted
- **Exclusions** for test files and migration scripts

## Troubleshooting

### Common Issues

1. **".env.test not found"**
   ```bash
   cp .env.example .env.test
   ```

2. **"pytest not found"**
   ```bash
   pip install pytest pytest-asyncio pytest-cov httpx
   ```

3. **"Permission denied" (WSL/Linux)**
   ```bash
   chmod +x scripts/*.sh
   ```

4. **PowerShell execution policy**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

### Debug Mode
For detailed test output:
```bash
# Windows
scripts\run-tests.bat debug

# WSL/Linux
./scripts/run-tests.sh debug

# PowerShell  
.\scripts\run-tests.ps1 debug
```

### Environment Validation
Test environment setup:
```bash
# Windows
scripts\run-tests.bat env

# WSL/Linux
./scripts/run-tests.sh env
```

### OpenRouter LLM Configuration
For testing LLM-based graph processing with OpenRouter:
```powershell
# Windows PowerShell
$env:OPENROUTER_API_KEY = "sk-or-v1-your-key-here"
$env:GRAPH_LLM_PROVIDER = "openrouter"
$env:GRAPH_LLM_MODEL = "openai/gpt-3.5-turbo"
$env:GRAPH_ENABLED = "true"
$env:GRAPH_ENTITY_EXTRACTION_METHOD = "llm_based"
$env:GRAPH_TOPIC_EXTRACTION_METHOD = "llm_based"
$env:GRAPH_SENTIMENT_ANALYSIS_ENABLED = "true"
$env:GRAPH_RELATIONSHIP_EXTRACTION_METHOD = "llm_based"

# Run OpenRouter tests
python test_openrouter_config.py
python test_llm_graph_advanced.py
```

```bash
# WSL/Linux
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
export GRAPH_LLM_PROVIDER="openrouter"
export GRAPH_LLM_MODEL="openai/gpt-3.5-turbo"
export GRAPH_ENABLED="true"
export GRAPH_ENTITY_EXTRACTION_METHOD="llm_based"
export GRAPH_TOPIC_EXTRACTION_METHOD="llm_based"
export GRAPH_SENTIMENT_ANALYSIS_ENABLED="true"
export GRAPH_RELATIONSHIP_EXTRACTION_METHOD="llm_based"

# Run OpenRouter tests
python test_openrouter_config.py
python test_llm_graph_advanced.py
```

## Script Features

### Cross-Platform Support
- **Windows**: Command Prompt, PowerShell
- **WSL**: Full Linux compatibility  
- **Auto-detection**: Poetry vs pip environments

### User Experience
- **Colored output** for better readability
- **Progress indicators** and status messages
- **Error handling** with helpful messages
- **Auto-opening** coverage reports

### Flexibility
- **Custom test patterns** support
- **Environment isolation** 
- **Watch mode** for development
- **Multiple output formats**

## Integration with IDE

### VS Code
Add to `.vscode/tasks.json`:
```json
{
    "label": "Run Tests",
    "type": "shell",
    "command": "./scripts/run-tests.sh",
    "args": ["${input:testType}"],
    "group": "test"
}
```

### PyCharm
Configure pytest as test runner with:
- **Environment**: `ENVIRONMENT=testing`
- **Working directory**: Project root
- **Additional arguments**: From script options