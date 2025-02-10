# Usage Guide

## Basic Usage

### Installation

Install using UV (recommended):
```bash
uv pip install .
```

Or using pip:
```bash
pip install .
```

### Configuration

Create a `config.toml` file:
```toml
[global]
model = "google/gemini-pro-vision-1.0"  # Default vision model

[[sources]]
type = "bear"
src_dir = "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files"
dest_dir = "output/bear"

[[sources]]
type = "xbookmarks"
src_dir = "~/Library/Containers/com.apple.Safari/Data/Library/Safari/Bookmarks.plist"
dest_dir = "output/bookmarks"
```

### Running

Basic usage:
```bash
consolidate-markdown --config config.toml
```

With specific processor:
```bash
consolidate-markdown --config config.toml --processor bear
```

With debug output:
```bash
consolidate-markdown --config config.toml --debug
```

## Command Line Options

### Core Options
- `--config`: Path to config file (required)
- `--processor`: Specific processor to run
- `--debug`: Enable debug logging
- `--force`: Force regeneration of all files
- `--limit`: Limit number of items to process
- `--no-image`: Skip image analysis
- `--version`: Show version information
- `--help`: Show help message

### Examples

Process only recent items:
```bash
consolidate-markdown --config config.toml --limit 10
```

Skip image analysis:
```bash
consolidate-markdown --config config.toml --no-image
```

Force regeneration:
```bash
consolidate-markdown --config config.toml --force
```

## Configuration Options

### Global Settings

```toml
[global]
# Vision model for image analysis
model = "google/gemini-pro-vision-1.0"

# Default cache directory
cache_dir = ".cm/cache"

# Default log directory
log_dir = ".cm/logs"

# Default log level
log_level = "INFO"
```

### Source-Specific Settings

Each source can have its own settings:
```toml
[[sources]]
type = "bear"
src_dir = "path/to/source"
dest_dir = "path/to/output"
model = "gpt-4o"  # Override global model
```

## Environment Variables

### API Keys
- `OPENROUTER_API_KEY`: OpenRouter API key
- `OPENAI_API_KEY`: OpenAI API key (if using GPT-4 Vision)

### Paths
- `CM_CONFIG_PATH`: Default config path
- `CM_CACHE_DIR`: Override cache directory
- `CM_LOG_DIR`: Override log directory

### Debug
- `CM_DEBUG`: Enable debug mode
- `CM_LOG_LEVEL`: Set log level

## Output Organization

### Directory Structure
```
output/
├── bear/
│   ├── work/
│   │   └── notes.md
│   └── personal/
│       └── notes.md
├── bookmarks/
│   ├── tech/
│   │   └── bookmarks.md
│   └── other/
│       └── bookmarks.md
└── chatgpt/
    └── conversations/
        └── chat.md
```

### File Naming
- Bear notes: `{title}.md`
- X Bookmarks: `{date}-{title}.md`
- ChatGPT: `{date}-{conversation}.md`
- Claude: `{date}-{title}.md`

## Best Practices

### Performance
1. Use incremental processing
2. Enable caching
3. Process in batches
4. Monitor resource usage

### Organization
1. Use clear directory structure
2. Group related content
3. Use consistent naming
4. Maintain backups

### Maintenance
1. Regular cache cleanup
2. Log rotation
3. Backup configuration
4. Update dependencies

## Common Workflows

### 1. Daily Notes Backup
```bash
# Morning backup
consolidate-markdown --config config.toml --processor bear --limit 10
```

### 2. Weekly Archive
```bash
# Sunday full backup
consolidate-markdown --config config.toml --force
```

### 3. Quick Export
```bash
# Export without images
consolidate-markdown --config config.toml --no-image
```

### 4. Development
```bash
# Debug mode for testing
consolidate-markdown --config config.toml --debug --limit 5
```
