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

6. [Testing](testing.md)
   - Unit tests and integration tests
   - Live API testing configuration
   - Test fixtures and data
   - Running tests locally

## API Providers

The tool supports two providers for image analysis:

### OpenAI (Default)
- Uses GPT-4 Vision API directly from OpenAI
- Configure in `config.toml`:
  ```toml
  [global]
  api_provider = "openai"
  openai_key = "sk-..."  # Your OpenAI API key
  ```
- Or use environment variables:
  ```bash
  export OPENAI_API_KEY="your-key"
  ```

### OpenRouter
- Alternative provider that can be more cost-effective
- Configure in `config.toml`:
  ```toml
  [global]
  api_provider = "openrouter"
  openrouter_key = "sk-..."  # Your OpenRouter API key
  ```
- Or use environment variables:
  ```bash
  export OPENROUTER_API_KEY="your-key"
  ```

You can easily switch between providers by changing the `api_provider` setting. Both providers use GPT-4 Vision for image analysis, but OpenRouter may offer different pricing options. See the [Configuration Guide](configuration.md) for detailed setup instructions.

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

2. Set up your API key (choose one):
   ```bash
   # Option 1: OpenAI (default)
   export OPENAI_API_KEY="your-openai-key"

   # Option 2: OpenRouter (alternative)
   export OPENROUTER_API_KEY="your-openrouter-key"
   ```

3. Configure sources in `consolidate_config.toml`:
   ```toml
   [global]
   # Choose your API provider
   api_provider = "openai"  # or "openrouter"

   [[sources]]
   type = "bear"  # or "claude", "xbookmarks", "chatgptexport"
   srcDir = "~/path/to/source"
   destDir = "./output/destination"
   ```

4. Run the tool:
   ```bash
   uv run python -m consolidate_markdown --config ./consolidate_config.toml
   ```

See the [Configuration Guide](configuration.md) for detailed setup options and [API Providers](#api-providers) section above for more details on choosing between OpenAI and OpenRouter.

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
