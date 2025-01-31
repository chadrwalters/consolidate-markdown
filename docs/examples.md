# Usage Examples

This document provides examples of common use cases for the consolidate-markdown tool.

## Basic Usage

Process all configured sources:
```bash
consolidate-markdown --config config.toml
```

## Processor Selection

Process only specific types of content:

```bash
# Process only Bear notes
consolidate-markdown --config config.toml --processor bear

# Process only X bookmarks
consolidate-markdown --config config.toml --processor xbookmarks

# Process only ChatGPT exports
consolidate-markdown --config config.toml --processor chatgptexport
```

## Item Limiting

Process a limited number of items:

```bash
# Process last 5 items from each source
consolidate-markdown --config config.toml --limit 5

# Process last 2 Bear notes only
consolidate-markdown --config config.toml --processor bear --limit 2

# Process last 10 X bookmarks with force regeneration
consolidate-markdown --config config.toml --processor xbookmarks --limit 10 --force
```

## Image Processing

Control image analysis:

```bash
# Skip image analysis
consolidate-markdown --config config.toml --no-image

# Force regeneration of image descriptions
consolidate-markdown --config config.toml --force
```

## Cache Control

Manage caching behavior:

```bash
# Force regeneration of all files
consolidate-markdown --config config.toml --force

# Delete existing output and cache before processing
consolidate-markdown --config config.toml --delete

# Force regeneration of last 5 items only
consolidate-markdown --config config.toml --force --limit 5
```

## Logging

Control log output:

```bash
# Enable debug logging
consolidate-markdown --config config.toml --debug

# Set specific log level
consolidate-markdown --config config.toml --log-level WARNING
```

## Configuration Examples

### Multiple Bear Sources

```toml
[global]
cm_dir = ".cm"
no_image = false

[[sources]]
type = "bear"
src_dir = "~/work/notes"
dest_dir = "output/work"

[[sources]]
type = "bear"
src_dir = "~/personal/notes"
dest_dir = "output/personal"
```

Process specific Bear source:
```bash
# Process last 5 work notes
consolidate-markdown --config config.toml --processor bear --limit 5

# Force regeneration of all personal notes
consolidate-markdown --config config.toml --processor bear --force
```

### Mixed Sources

```toml
[global]
cm_dir = ".cm"
no_image = false

[[sources]]
type = "bear"
src_dir = "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files"
dest_dir = "output/bear"

[[sources]]
type = "xbookmarks"
src_dir = "~/Library/Containers/com.apple.Safari/Data/Library/Safari/Bookmarks.plist"
dest_dir = "output/bookmarks"

[[sources]]
type = "chatgptexport"
src_dir = "~/Downloads/chatgpt_exports"
dest_dir = "output/chatgpt"
```

Process specific combinations:
```bash
# Process last 10 items from Bear and X bookmarks
consolidate-markdown --config config.toml --limit 10

# Process only ChatGPT exports with debug logging
consolidate-markdown --config config.toml --processor chatgptexport --debug
```

## Environment Variables

Use environment variables for configuration:

```bash
# Set OpenAI API key
export OPENAI_API_KEY="your-api-key"

# Set log level
export CM_LOG_LEVEL="DEBUG"

# Disable image analysis
export CM_NO_IMAGE=1

# Run with environment configuration
consolidate-markdown --config config.toml
```

## Common Workflows

### Initial Setup
```bash
# Create initial output with image analysis
consolidate-markdown --config config.toml

# Create initial output without images
consolidate-markdown --config config.toml --no-image
```

### Regular Updates
```bash
# Process only recent items
consolidate-markdown --config config.toml --limit 10

# Update specific content type
consolidate-markdown --config config.toml --processor bear --limit 5
```

### Maintenance
```bash
# Force complete regeneration
consolidate-markdown --config config.toml --delete --force

# Regenerate specific processor
consolidate-markdown --config config.toml --processor xbookmarks --force
```

### Debugging
```bash
# Debug specific processor
consolidate-markdown --config config.toml --processor bear --debug --limit 2

# Debug with forced regeneration
consolidate-markdown --config config.toml --debug --force --limit 1
```

## Error Handling Examples

### Retry Logic
```
