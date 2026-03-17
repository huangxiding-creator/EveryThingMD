# Contributing to EveryThingMD

First off, thank you for considering contributing to EveryThingMD! It's people like you that make EveryThingMD such a great tool.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/EveryThingMD.git`
3. Create a branch: `git checkout -b my-new-feature`
4. Make your changes
5. Submit a pull request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/huangxiding-creator/EveryThingMD.git
cd EveryThingMD

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check .
```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed and expected**
- **Include screenshots if applicable**
- **Include your environment details** (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and expected behavior**
- **Explain why this enhancement would be useful**

### Your First Code Contribution

Unsure where to begin contributing? You can start by looking through these issues:

- `good first issue` - issues that should only require a few lines of code
- `help wanted` - issues that need attention from contributors

## Pull Request Process

1. **Update the README.md** with details of changes to the interface
2. **Update the CHANGELOG.md** with details of your changes
3. **Add tests** for any new functionality
4. **Ensure all tests pass**: `pytest`
5. **Run linting**: `ruff check .`
6. **Update documentation** if needed

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- Line length: 100 characters
- Use double quotes for strings
- Use type hints for all public functions

### Code Quality Tools

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy dir2md/
```

### Commit Message Format

We follow conventional commits:

```
<type>: <description>

[optional body]

Types:
- feat: A new feature
- fix: A bug fix
- docs: Documentation changes
- style: Code style changes (formatting, etc.)
- refactor: Code refactoring
- test: Adding or updating tests
- chore: Maintenance tasks
```

## Testing

We require tests for all new functionality:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=dir2md --cov-report=html

# Run specific test file
pytest tests/test_dual_converter.py
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Fixtures and test configuration
├── test_dual_converter.py
├── test_quality_evaluator.py
└── test_integration.py
```

## Documentation

- Update README.md for user-facing changes
- Update docstrings for API changes
- Add inline comments for complex logic
- Update type hints for better IDE support

## Release Process

1. Update version in `pyproject.toml` and `__init__.py`
2. Update `CHANGELOG.md`
3. Create a new release on GitHub
4. Build and publish to PyPI (maintainers only)

---

Thank you for contributing! 🎉
