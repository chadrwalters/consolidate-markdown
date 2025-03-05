# Consolidate Markdown Development Guide

## Build, Test & Lint Commands
- Install: `uv pip install -e ".[dev]"`
- Run tests: `uv run pytest`
- Run specific test: `uv run pytest tests/unit/test_file.py::TestClass::test_function -v`
- Coverage report: `uv run pytest --cov=src/consolidate_markdown`
- Lint code: `uv run ruff check .`
- Type checking: `uv run mypy src/`
- Format code: `uv run black src/ tests/`
- Format imports: `uv run isort src/ tests/`
- Run all quality checks: `uv run pre-commit run --all-files`

## Code Style Guidelines
- **Follow Python 3.11+ features** (type hints, f-strings, pathlib)
- **Imports**: Use isort with Black profile (grouped by stdlib/3rd-party/local)
- **Formatting**: 88-char line limit with Black formatter
- **Types**: Strict typing required; use mypy with disallow_untyped_defs=true
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error handling**: Use custom exception classes from exceptions.py
- **Testing**: Every feature needs tests; maintain high coverage
- **Documentation**: Docstrings required for public API
- **Processors**: All new processors inherit from SourceProcessor base class
