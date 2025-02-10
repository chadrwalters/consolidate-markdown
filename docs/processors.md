# Source Processors

## Overview

Source processors are responsible for handling different types of input sources in consolidate-markdown. Each processor is specialized for a specific input format and handles the conversion to standardized markdown output.

## Available Processors

### 1. Bear Notes Processor

#### Features
- Processes Bear note exports
- Handles attachments and images
- Preserves tags and metadata
- Supports nested notes

#### Configuration
```toml
[[sources]]
type = "bear"
src_dir = "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files"
dest_dir = "output/bear"
```

### 2. Claude Export Processor

#### Features
- Processes Claude conversation exports
- Extracts code artifacts
- Handles tool outputs
- Preserves conversation structure

#### Configuration
```toml
[[sources]]
type = "claude"
src_dir = "~/Downloads/claude_exports"
dest_dir = "output/claude"
```

### 3. X Bookmarks Processor

#### Features
- Processes X (Twitter) bookmarks
- Downloads media content
- Preserves thread structure
- Includes engagement metrics

#### Configuration
```toml
[[sources]]
type = "xbookmarks"
src_dir = "~/Library/Containers/com.apple.Safari/Data/Library/Safari/Bookmarks.plist"
dest_dir = "output/bookmarks"
```

### 4. ChatGPT Export Processor

#### Features
- Processes ChatGPT conversation exports
- Extracts code blocks
- Handles multi-modal content
- Preserves conversation metadata

#### Configuration
```toml
[[sources]]
type = "chatgptexport"
src_dir = "~/Downloads/chatgpt_exports"
dest_dir = "output/chatgpt"
```

## Implementation Details

### Base Processor Class
```python
class BaseProcessor:
    """Base class for all source processors."""

    def __init__(self, config):
        self.config = config
        self.cache = Cache()
        self.logger = logging.getLogger(__name__)

    def process(self):
        """Process the source files."""
        raise NotImplementedError

    def validate(self):
        """Validate source configuration."""
        raise NotImplementedError

    def cleanup(self):
        """Clean up temporary files."""
        raise NotImplementedError
```

### Common Features

#### Cache Management
- Content hashing
- Timestamp tracking
- Incremental updates

#### Error Handling
- Invalid file formats
- Missing dependencies
- API failures
- Resource limits

#### Resource Management
- Memory optimization
- File streaming
- Cleanup routines

## Best Practices

### Development Guidelines
1. Inherit from BaseProcessor
2. Implement required methods
3. Use consistent error handling
4. Follow cache patterns
5. Clean up resources

### Performance Tips
1. Stream large files
2. Use incremental processing
3. Implement smart caching
4. Handle rate limits
5. Monitor resource usage

### Error Handling
1. Validate inputs early
2. Provide clear messages
3. Clean up on failure
4. Log appropriately
5. Support recovery

## Future Improvements

### Planned Features
1. Additional processors
   - Notion exports
   - Obsidian vaults
   - Evernote exports
   - OneNote notebooks

2. Enhanced capabilities
   - Better error recovery
   - Improved caching
   - Parallel processing
   - Resource monitoring

3. Integration options
   - Plugin system
   - Custom processors
   - Event hooks
   - Metrics collection
