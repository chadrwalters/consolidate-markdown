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

## Processor Differences

### ⚠️ Important: Attachment Handling
Different chat platforms provide significantly different levels of access to attachments in their exports. Understanding these differences is crucial for choosing the right processor for your needs:

#### Claude (Limited)
- ❌ NO access to original binary files
- ❌ NO preservation of original formatting
- ✓ Only provides metadata and extracted text
- ✓ Preserves metadata for empty attachments
- ⚠️ See [Claude Attachment Handling](claude-attachments.md) for detailed limitations

#### ChatGPT (Full Access)
- ✓ Full access to original files
- ✓ Preserves binary content and formatting
- ✓ Maintains file system metadata
- ✓ Supports downloading original files

### Example Outputs

#### Claude Attachment (Extracted Text Only)
```markdown
<!-- CLAUDE EXPORT: Extracted content from example.pdf -->
<details>
<summary>📄 example.pdf (1.2MB PDF) - Extracted Content</summary>

Original File Information:
- Type: PDF
- Size: 1.2MB
- Extracted: 2024-01-30
- Note: Original file not available in Claude export

Extracted Content:
```text
[Text content extracted by Claude]
```

</details>
```

#### ChatGPT Attachment
```markdown
<!-- ATTACHMENT: example.pdf -->
<details>
<summary>📄 example.pdf</summary>

![PDF Preview](artifacts/example.pdf)

[Download PDF](artifacts/example.pdf)

</details>
```

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

## AI Development Guidelines

The project uses AI assistance through Cursor IDE. All AI interactions follow a standardized startup procedure defined in `.cursor/rules/00-ai-startup.rules.mdc`. This ensures consistent and thorough project understanding before any development work begins.

Key aspects of AI interaction:
- Standardized startup sequence
- Rule-based development guidelines
- Documentation-first approach
- Plan-driven development
