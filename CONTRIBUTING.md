# Contributing to Consolidate Markdown

First off, thank you for considering contributing to Consolidate Markdown! It's people like you that make it such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include any error messages

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* A clear and descriptive title
* A detailed description of the proposed functionality
* An explanation of why this enhancement would be useful
* Possible implementation details if you have them

### Pull Requests

* Fill in the required template
* Follow the Python style guides (Black, isort, mypy)
* Include appropriate test cases
* Update documentation as needed
* End all files with a newline

## Development Process

1. Fork the repo and create your branch from `main`
2. Install development dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```
3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```
4. Make your changes
5. Run the test suite:
   ```bash
   uv run pytest
   ```
6. Push to your fork and submit a pull request

## Style Guides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Python Style Guide

* Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
* Use [Black](https://github.com/psf/black) for code formatting
* Sort imports with [isort](https://pycqa.github.io/isort/)
* Type hint all functions (checked with mypy)
* Document all public functions and classes

## Additional Notes

### Issue and Pull Request Labels

* `bug`: Something isn't working
* `enhancement`: New feature or request
* `documentation`: Improvements or additions to documentation
* `good first issue`: Good for newcomers
* `help wanted`: Extra attention is needed
