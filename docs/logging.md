# Logging System

## Overview

The consolidate-markdown tool uses a comprehensive logging system built on Python's standard logging module, enhanced with Rich for beautiful console output.

## Configuration

### Log Levels

1. **DEBUG** (`--debug`)
   - Most verbose output
   - Shows all processing steps
   - Includes API calls and responses
   - Shows file operations
   - Displays cache operations

2. **INFO** (default)
   - Shows progress information
   - Reports major operations
   - Displays summaries
   - Shows important warnings

3. **WARNING**
   - Shows only warnings
   - Reports potential issues
   - Displays error recovery
   - Shows skipped operations

4. **ERROR**
   - Shows only errors
   - Reports failed operations
   - Displays critical issues

### Console Output

#### Rich Integration
Uses Rich for enhanced console output:
```python
from rich.logging import RichHandler

# Configure Rich handler
handler = RichHandler(
    rich_tracebacks=True,
    markup=True,
    show_path=False
)
```

#### Color Scheme
- DEBUG: Blue
- INFO: Green
- WARNING: Yellow
- ERROR: Red
- CRITICAL: Red (bold)

### File Logging

#### Log File Structure
```
.cm/
  └── logs/
      ├── consolidate.log     # Current log file
      └── archive/           # Old log files
          ├── YYYY-MM-DD.log
          └── YYYY-MM-DD.log
```

#### Rotation Policy
- Daily rotation
- Compression of old logs
- 30-day retention
- Size-based splitting

## Implementation

### Logger Setup
```python
def setup_logging(config):
    """Configure logging based on config."""
    level = logging.DEBUG if config.debug else logging.INFO

    # Console handler with Rich
    console_handler = RichHandler(
        level=level,
        rich_tracebacks=True,
        markup=True,
        show_path=False
    )

    # File handler
    file_handler = RotatingFileHandler(
        filename=".cm/logs/consolidate.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[console_handler, file_handler]
    )
```

### Usage Examples

#### Basic Logging
```python
import logging

logger = logging.getLogger(__name__)

# Standard logging
logger.debug("Processing file: %s", filename)
logger.info("Completed source: %s", source.name)
logger.warning("Skipping invalid file: %s", filename)
logger.error("Failed to process: %s", filename)
```

#### Rich Formatting
```python
# With Rich markup
logger.info("[bold green]Successfully processed[/bold green]: %s", filename)
logger.warning("[yellow]Cache miss[/yellow]: %s", cache_key)
logger.error("[red]API error[/red]: %s", error_message)
```

## Best Practices

### Message Guidelines
1. Be specific and concise
2. Include relevant context
3. Use appropriate log levels
4. Format consistently
5. Include timestamps

### Performance
1. Use lazy evaluation
2. Avoid excessive debug logs
3. Rotate logs regularly
4. Clean old logs
5. Monitor log size

### Security
1. Sanitize sensitive data
2. Mask API keys
3. Validate log paths
4. Secure log files
5. Monitor access

## Future Improvements

### Planned Features
1. Structured logging
2. JSON log format
3. Log aggregation
4. Performance metrics
5. Error analytics

### Integration Plans
1. Error reporting
2. Metrics collection
3. Log analysis
4. Alert system
5. Dashboard integration
