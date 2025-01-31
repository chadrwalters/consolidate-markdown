# Consolidate Markdown Documentation

## Overview

This documentation covers the consolidate-markdown project, a tool for processing and consolidating Markdown files from various sources into a unified format.

## Contents

1. [Product Requirements](prd.md)
   - Detailed product requirements and specifications
   - Feature descriptions and technical requirements

2. [Configuration](configuration.md)
   - Configuration file format and options
   - Command line arguments
   - Environment variables

3. [Data Formats](schemas/README.md)
   - Schemas for supported data formats
   - Export format specifications
   - Common patterns and structures

4. [Examples](examples.md)
   - Usage examples and common patterns
   - Configuration examples
   - Processing demonstrations

5. [Caching](caching.md)
   - Cache management and behavior
   - Force regeneration options
   - Performance considerations

## Quick Links

- [Bear Export Schema](schemas/bear_export.md)
- [ChatGPT Export Schema](schemas/chatgpt_export.md)
- [Claude Export Schema](schemas/claude_export.md)
- [XBookmarks Export Schema](schemas/xbookmarks_export.md)

## Getting Started

1. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

2. Configure sources in `consolidate_config.toml`

3. Run the tool:
   ```bash
   uv run python -m consolidate_markdown --config ./consolidate_config.toml
   ```

## Additional Resources

- [Configuration Template](../config.template.toml)
- [Test Fixtures](../tests/fixtures/README.md)
- [Source Code](../src/consolidate_markdown/)
