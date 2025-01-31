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
# Process only Claude exports
consolidate-markdown --config config.toml --processor claude

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

# Process last 10 Claude conversations only
consolidate-markdown --config config.toml --processor claude --limit 10

# Process last 2 Bear notes only
consolidate-markdown --config config.toml --processor bear --limit 2
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

### Multiple Claude Sources

```toml
[global]
cm_dir = ".cm"
no_image = false

[[sources]]
type = "claude"
src_dir = "~/work/claude"
dest_dir = "output/work"
options = {
    date_format = "%Y%m%d",
    title_format = "{date}-{name}"
}

[[sources]]
type = "claude"
src_dir = "~/personal/claude"
dest_dir = "output/personal"
options = {
    date_format = "%Y%m%d",
    title_format = "Personal-{date}-{name}"
}
```

Process specific Claude source:
```bash
# Process last 5 work conversations
consolidate-markdown --config config.toml --processor claude --limit 5

# Force regeneration of all personal conversations
consolidate-markdown --config config.toml --processor claude --force
```

### Mixed Sources

```toml
[global]
cm_dir = ".cm"
no_image = false

[[sources]]
type = "claude"
src_dir = "~/Documents/Claude Exports"
dest_dir = "output/claude"
options = {
    extract_artifacts = true,
    track_versions = true
}

[[sources]]
type = "bear"
src_dir = "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files"
dest_dir = "output/bear"

[[sources]]
type = "chatgptexport"
src_dir = "~/Downloads/chatgpt_exports"
dest_dir = "output/chatgpt"
```

Process specific combinations:
```bash
# Process last 10 items from Claude and Bear
consolidate-markdown --config config.toml --limit 10

# Process only Claude exports with debug logging
consolidate-markdown --config config.toml --processor claude --debug
```

## Common Claude Workflows

### Initial Setup
```bash
# Create initial output with artifact extraction
consolidate-markdown --config config.toml --processor claude

# Create initial output without artifact extraction
consolidate-markdown --config config.toml --processor claude --no-artifacts
```

### Regular Updates
```bash
# Process only recent conversations
consolidate-markdown --config config.toml --processor claude --limit 10

# Update with attachment processing
consolidate-markdown --config config.toml --processor claude --process-attachments
```

### Artifact Management
```bash
# Force regeneration of artifacts
consolidate-markdown --config config.toml --processor claude --force-artifacts

# Update artifact versions
consolidate-markdown --config config.toml --processor claude --update-artifacts
```

### Debugging Claude Processing
```bash
# Debug conversation processing
consolidate-markdown --config config.toml --processor claude --debug --limit 2

# Debug artifact extraction
consolidate-markdown --config config.toml --processor claude --debug --force-artifacts

# Debug attachment processing
consolidate-markdown --config config.toml --processor claude --debug --process-attachments
```

## Error Handling Examples

### Retry Failed Conversations
```bash
# Retry failed conversations with debug logging
consolidate-markdown --config config.toml --processor claude --retry-failed --debug

# Force retry all conversations
consolidate-markdown --config config.toml --processor claude --retry-all --force
```

### Handle Missing Files
```bash
# Skip missing attachments
consolidate-markdown --config config.toml --processor claude --skip-missing

# Report missing files
consolidate-markdown --config config.toml --processor claude --report-missing
```

### Data Validation
```bash
# Validate conversation format
consolidate-markdown --config config.toml --processor claude --validate

# Check file integrity
consolidate-markdown --config config.toml --processor claude --check-integrity
```

## Best Practices

1. Regular Updates:
   - Process recent conversations frequently
   - Use --limit to focus on new content
   - Enable artifact tracking for code management

2. Artifact Management:
   - Use version tracking for code changes
   - Maintain artifact relationships
   - Regularly update artifact index

3. Attachment Handling:
   - Keep attachments organized
   - Process attachments after initial setup
   - Verify attachment references

4. Error Recovery:
   - Use debug logging for issues
   - Retry failed operations
   - Validate data integrity

For more detailed information, see the [Configuration Guide](configuration.md) and [Troubleshooting Guide](troubleshooting.md).
