# Code Quality and Linting Setup

This project uses automated code quality checks to maintain consistent code style and catch potential issues early.

## What's Included

### Pre-Commit Hooks (Automatic)

The following checks run automatically before each commit:

- **Trailing whitespace removal**: Removes unnecessary whitespace at line ends
- **End-of-file fixing**: Ensures files end with a newline
- **YAML validation**: Checks YAML file syntax
- **Large file detection**: Prevents accidentally committing large files
- **Ruff linting**: Basic Python code quality checks (app directory only)
- **Ruff formatting**: Automatic code formatting (app directory only)

These hooks are **lightweight and fast** to avoid slowing down your development workflow.

### Manual Comprehensive Checks

For more thorough code quality analysis, use the manual linting scripts:

```bash
# Basic checks (same as pre-commit but manual)
python scripts/run_linting.py

# Comprehensive checks including type checking and docstring validation
python scripts/run_linting.py --all

# Auto-fix issues where possible
python scripts/run_linting.py --fix

# Both comprehensive and auto-fix
python scripts/run_linting.py --all --fix
```

**Windows PowerShell:**
```powershell
# Basic checks
.\scripts\run_linting.ps1

# Comprehensive checks
.\scripts\run_linting.ps1 -All

# Auto-fix issues
.\scripts\run_linting.ps1 -Fix

# Both comprehensive and auto-fix
.\scripts\run_linting.ps1 -All -Fix
```

## Configuration

### Ruff (Linting and Formatting)

Configuration in `pyproject.toml`:
- **Line length**: 100 characters (more lenient than strict 88)
- **Target Python version**: 3.12
- **Ignored rules**: Module import order, line length (handled by formatter), unused imports/variables
- **Special handling**: Very lenient rules for scripts, tests, and migrations

### Pydocstyle (Docstring Checking)

- **Convention**: Google style docstrings
- **Relaxed mode**: Many docstring requirements are ignored initially to avoid overwhelming developers
- **Scope**: Only runs on app directory, excludes tests and scripts

### MyPy (Type Checking)

- **Mode**: Relaxed (allows untyped functions initially)
- **Imports**: Ignores missing type stubs
- **Scope**: Only runs on app directory

## Installation and Setup

This is automatically set up when you install the development dependencies:

```bash
# Install all development dependencies including linting tools
uv add --dev pydocstyle flake8-docstrings mypy pre-commit ruff

# Install pre-commit hooks
uv run pre-commit install
```

## Philosophy

This setup follows a **progressive enhancement** approach:

1. **Pre-commit hooks** are minimal and fast, focusing on basic formatting and obvious issues
2. **Manual comprehensive checks** provide deeper analysis when you want it
3. **Configuration is lenient** initially, allowing teams to gradually tighten standards
4. **Test and script directories** have relaxed rules to avoid hindering experimentation

## Customizing the Rules

### Making Rules Stricter

As your codebase matures, you can:

1. Remove ignored rules from `pyproject.toml` [tool.ruff.lint] ignore list
2. Remove ignored docstring rules from the pydocstyle configuration
3. Enable stricter mypy checking by setting `disallow_untyped_defs = true`

### Adding More Checks to Pre-Commit

Edit `.pre-commit-config.yaml` to add back the mypy and pydocstyle hooks if you want them to run automatically.

### Per-Project Customization

Each tool's configuration is in `pyproject.toml`, making it easy to adjust rules per project needs.

## Troubleshooting

### Pre-commit hooks failing
```bash
# Run hooks manually to see detailed output
uv run pre-commit run --all-files

# Update hook environments
uv run pre-commit autoupdate
```

### Manual linting script not found
```bash
# Make sure you're in the project root
cd /path/to/audio-processor

# Run with uv
uv run python scripts/run_linting.py
```

### Ruff not found
```bash
# Install development dependencies
uv add --dev ruff

# Or reinstall all dev dependencies
uv sync
```

## IDE Integration

Most modern IDEs can integrate with these tools:

- **VS Code**: Install Python, Ruff, and MyPy extensions
- **PyCharm**: Enable inspections for the installed tools
- **Vim/Neovim**: Use plugins like ALE or null-ls

Configure your IDE to use the same settings from `pyproject.toml` for consistency.
