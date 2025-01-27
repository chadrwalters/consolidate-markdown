# Consolidate Markdown (v1.0.0)

A unified command-line tool that processes Markdown files from multiple sources with AI-powered image analysis.

## Quick Start
```bash
# Install with uv
uv pip install .

# Run with example config
uv run python -m consolidate_markdown --config ./example_config.toml
```

## Documentation
- [Installation Guide](./installation.md) - Setup and requirements
- [Configuration Guide](./configuration.md) - Configure the tool
- [Architecture](./architecture.md) - Design and implementation
- [Development Guide](./development.md) - Contributing and development
- [API Reference](./api.md) - API documentation
- [File Support](./file_support.md) - Supported file types

## Key Features
- Process Bear.app notes and X Bookmarks
- AI-powered image descriptions using GPT-4o
- Document conversion to Markdown
- Configurable processing pipeline
- Detailed processing statistics:
  - Notes processed (markdown files)
  - Images processed/skipped
  - Documents processed (non-image attachments)

## Version
- Current: v1.0.0
- Status: In Development
- Phase: 1 - Sequential Processing
