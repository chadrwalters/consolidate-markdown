# Usage Examples

## Basic Usage

### Simple Bear Notes Processing
```bash
# config.toml
[global]
cm_dir = ".cm"
no_image = true

[[sources]]
type = "bear"
srcDir = "~/Documents/Bear Notes"
destDir = "./output"

# Run command
consolidate_markdown --config config.toml
```

### X Bookmarks with Image Analysis
```bash
# config.toml
[global]
cm_dir = ".cm"
openai_key = "sk-..."

[[sources]]
type = "xbookmarks"
srcDir = "~/Downloads/x_bookmarks"
destDir = "./output"

# Run command
consolidate_markdown --config config.toml
```

### ChatGPT Export Processing
```bash
# config.toml
[global]
cm_dir = ".cm"
openai_key = "sk-..."  # Optional: for image analysis

[[sources]]
type = "chatgptexport"
srcDir = "~/Downloads/ChatGPT Export"
destDir = "./output/chatgpt"

# Run command
consolidate_markdown --config config.toml
```

## Advanced Usage

### Multiple Sources
```bash
# config.toml
[global]
cm_dir = ".cm"
openai_key = "sk-..."

[[sources]]
type = "bear"
srcDir = "/notes/bear"
destDir = "/output/bear"

[[sources]]
type = "xbookmarks"
srcDir = "/bookmarks/x"
destDir = "/output/x"

# Run command
consolidate_markdown --config config.toml
```

### Force Regeneration
```bash
# Reprocess all files
consolidate_markdown --config config.toml --force

# Clean start
consolidate_markdown --config config.toml --delete
```

### Performance Tuning
```bash
# Sequential processing
consolidate_markdown --config config.toml --sequential

# Skip image analysis
consolidate_markdown --config config.toml --no-image
```

## Error Handling Examples

### Retry Logic
```toml
[global]
cm_dir = ".cm"
log_level = "DEBUG"  # More detailed logging
openai_key = "sk-..."

[[sources]]
type = "bear"
srcDir = "/notes"
destDir = "/output"
```

### Backup Strategy
```bash
# Create backup before processing
cp -r /output /output_backup

# Run with potential destructive options
consolidate_markdown --config config.toml --delete
```

## Workflow Examples

### Daily Notes Backup
```bash
#!/bin/bash
# backup_notes.sh

# Set environment variables
export OPENAI_API_KEY="sk-..."

# Run consolidation
consolidate_markdown --config ~/.config/cm/config.toml

# Backup output
timestamp=$(date +%Y%m%d)
tar -czf "backup_$timestamp.tar.gz" output/
```

### Automated Processing
```bash
# crontab entry
0 2 * * * /path/to/backup_notes.sh >> /var/log/cm_backup.log 2>&1
```

### Integration Example
```python
from consolidate_markdown.config import load_config
from consolidate_markdown.runner import Runner

def process_notes(config_path):
    """Process notes programmatically."""
    config = load_config(config_path)
    runner = Runner(config)
    summary = runner.run()
    return summary.get_summary()
