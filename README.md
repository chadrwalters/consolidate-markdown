# Consolidate Markdown

A tool for consolidating various data sources into markdown files.

## Overview

This tool processes data from multiple sources and converts them into markdown files. Supported sources include:

- Claude conversations
- Bear notes
- Gmail emails
- Images (with metadata)
- XBookmarks

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/chadrwalters/consolidate-markdown.git
   cd consolidate-markdown
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   uv pip install -e .
   ```

3. Copy the example configuration file and edit it with your settings:
   ```bash
   cp config.toml.example config.toml
   ```

## Configuration

Edit the `config.toml` file to configure:

- Output directory
- API keys (if needed)
- Source directories for each data type
- Logging level

## Usage

Run the main script:

```bash
python -m consolidate_markdown
```

Or use specific processors:

```bash
python -m consolidate_markdown --processor claude
python -m consolidate_markdown --processor bear
python -m consolidate_markdown --processor gmail
python -m consolidate_markdown --processor image
python -m consolidate_markdown --processor xbookmarks
```

## Development

### Running Tests

```bash
pytest
```

### Running Specific Tests

```bash
pytest tests/unit/test_claude_processor.py
```

## License

[MIT License](LICENSE)
