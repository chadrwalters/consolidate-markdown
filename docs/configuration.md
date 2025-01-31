# Configuration Guide

This document describes how to configure the consolidate-markdown tool.

## Command Line Options

The following command line options are available:

- `--config PATH`: Path to configuration file (required)
- `--force`: Force regeneration of all files
- `--delete`: Delete existing output and cache before processing
- `--debug`: Enable debug logging
- `--log-level LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--no-image`: Skip image analysis
- `--processor TYPE`: Run only the specified processor type (claude, bear, xbookmarks, chatgptexport)
- `--limit N`: Process only the N most recent items from each source

## Configuration File

The configuration file uses TOML format and consists of a global section and one or more source sections.

### Global Configuration

The global section defines settings that apply to all processors:

```toml
[global]
# Directory for cache files (required)
cm_dir = ".cm"

# Skip image analysis (optional, default: false)
no_image = false

# OpenAI API key for image analysis (optional)
openai_key = "sk-..."

# Log level (optional, default: INFO)
log_level = "INFO"
```

### Source Configuration

Each source section defines a specific content source to process:

```toml
[[sources]]
# Source type (required)
# Valid values: "claude", "bear", "xbookmarks", "chatgptexport"
type = "claude"

# Source directory (required)
# Path to input files
src_dir = "~/Documents/Claude Exports"

# Destination directory (required)
# Path where processed files will be written
dest_dir = "./output/claude"

# Source-specific options (optional)
# These vary by processor type
options = { key = "value" }
```

## Processor Types

### Claude Exports

Processes Claude conversation exports:

```toml
[[sources]]
type = "claude"
src_dir = "~/Downloads/claude_exports"
dest_dir = "output/claude"
options = {
    # Optional: Custom date format for conversation filenames
    date_format = "%Y%m%d",
    # Optional: Custom title format for conversation files
    title_format = "{date}-{name}",
    # Optional: Preserve original XML tags in output
    preserve_tags = false,
    # Optional: Extract artifacts from conversations
    extract_artifacts = true,
    # Optional: Track artifact versions
    track_versions = true,
    # Optional: Process attachments
    process_attachments = true,
    # Optional: Directory for processed attachments
    attachments_dir = "attachments"
}
```

### Bear Notes

Processes Bear note files:

```toml
[[sources]]
type = "bear"
src_dir = "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files"
dest_dir = "output/bear"
```

### X Bookmarks

Processes X (Twitter) bookmarks:

```toml
[[sources]]
type = "xbookmarks"
src_dir = "~/Library/Containers/com.apple.Safari/Data/Library/Safari/Bookmarks.plist"
dest_dir = "output/bookmarks"
```

### ChatGPT Export

Processes ChatGPT conversation exports:

```toml
[[sources]]
type = "chatgptexport"
src_dir = "~/Downloads/chatgpt_exports"
dest_dir = "output/chatgpt"
```

## Environment Variables

The following environment variables can be used to override configuration:

- `OPENAI_API_KEY`: OpenAI API key for image analysis
- `CM_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `CM_NO_IMAGE`: Skip image analysis (set to any value to enable)
- `CM_CONFIG_PATH`: Path to configuration file

## Example Configurations

### Basic Claude Configuration

```toml
[global]
cm_dir = ".cm"
no_image = true

[[sources]]
type = "claude"
src_dir = "~/Documents/Claude Exports"
dest_dir = "./output/claude"
```

### Advanced Claude Configuration

```toml
[global]
cm_dir = ".cm"
openai_key = "sk-..."  # For image analysis in attachments

[[sources]]
type = "claude"
src_dir = "~/Documents/Claude Exports"
dest_dir = "./output/claude"
options = {
    date_format = "%Y%m%d",
    title_format = "{date}-{name}",
    preserve_tags = false,
    extract_artifacts = true,
    track_versions = true,
    process_attachments = true,
    attachments_dir = "attachments"
}
```

### Multiple Sources Including Claude

```toml
[global]
cm_dir = ".cm"
openai_key = "sk-..."

[[sources]]
type = "claude"
src_dir = "~/Documents/Claude Exports"
dest_dir = "./output/claude"

[[sources]]
type = "bear"
src_dir = "~/Documents/Notes"
dest_dir = "./output/notes"

[[sources]]
type = "chatgptexport"
src_dir = "~/Downloads/chatgpt"
dest_dir = "./output/chatgpt"
```

### Basic Configuration

```toml
[global]
cm_dir = ".cm"
no_image = true

[[sources]]
type = "bear"
src_dir = "~/Documents/Notes"
dest_dir = "./output/notes"
```

### Multiple Sources

```toml
[global]
cm_dir = ".cm"
openai_key = "sk-..."

[[sources]]
type = "bear"
src_dir = "~/Documents/Notes"
dest_dir = "./output/notes"

[[sources]]
type = "xbookmarks"
src_dir = "~/Downloads/bookmarks"
dest_dir = "./output/bookmarks"

[[sources]]
type = "chatgptexport"
src_dir = "~/Downloads/chatgpt"
dest_dir = "./output/chatgpt"
```

### Development Configuration

```toml
[global]
cm_dir = ".cm"
log_level = "DEBUG"
no_image = true

[[sources]]
type = "bear"
src_dir = "./test_data/notes"
dest_dir = "./test_output"
```

## Best Practices

1. Use absolute paths or paths relative to the user's home directory (~) for reliability
2. Keep cache directory (.cm) in the same directory as the configuration file
3. Use separate destination directories for different source types
4. Enable debug logging during initial setup or troubleshooting
5. Use environment variables for sensitive information (e.g., API keys)

## Troubleshooting

Common configuration issues and solutions:

1. File permissions:
   - Ensure read access to source directories
   - Ensure write access to destination and cache directories

2. Path resolution:
   - Use absolute paths if relative paths cause issues
   - Verify paths exist and are accessible

3. API configuration:
   - Set OPENAI_API_KEY environment variable
   - Verify API key is valid if using image analysis

4. Cache issues:
   - Use --delete to start fresh
   - Check .cm directory permissions
   - Verify sufficient disk space

For more detailed troubleshooting information, see troubleshooting.md.
