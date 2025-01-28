# Architecture Overview

This document describes the high-level architecture of the consolidate-markdown tool.

## Components

### Runner

The Runner is the main orchestrator that:
- Loads and validates configuration
- Initializes source processors
- Executes the consolidation process
- Collects and reports results

### Source Processors

Source processors handle specific types of input:
- Read source files
- Process content
- Generate output files
- Cache results for efficiency

### Configuration

Configuration is handled through:
- TOML configuration files
- Command line options
- Environment variables (future)

### Caching

The caching system:
- Stores processed content
- Tracks file modifications
- Enables incremental updates
- Improves performance

### Logging

The logging system:
- Provides detailed progress information
- Records errors and warnings
- Generates processing summaries
- Supports debugging

## Key Features

### Scalability
- Independent source processing
- Resource usage limits
- Efficient caching

### Extensibility
- Pluggable source processors
- Configurable output formats
- Custom processing rules

### Reliability
- Error handling and recovery
- Validation at each step
- Detailed logging
- Atomic file operations

## Data Flow

1. Configuration Loading
   - Parse command line args
   - Load TOML config
   - Validate settings

2. Source Processing
   - Initialize processors
   - Read source files
   - Process content
   - Generate output

3. Result Collection
   - Track statistics
   - Record errors
   - Generate summary

## Future Enhancements

1. Additional Source Types
   - Support for more input formats
   - Custom source processors

2. Output Formats
   - HTML generation
   - PDF export
   - Custom templates

3. Performance
   - Improved caching
   - Resource optimization

4. Integration
   - API endpoints
   - Webhooks
   - Event notifications

## Directory Structure
```
consolidate_markdown/
├── .cm/                    # Working directory
│   ├── logs/              # Log files
│   ├── markitdown/        # Document conversion
│   └── images/            # Image processing
├── src/
│   └── consolidate_markdown/
│       ├── processors/    # Source processors
│       ├── attachments/   # File handlers
│       └── config.py      # Configuration
└── tests/
    ├── unit/             # Unit tests
    └── integration/      # Integration tests
```

## Extension Points

### Adding New Source Types
1. Create new processor class inheriting from `SourceProcessor`
2. Implement `process()` and `validate()` methods
3. Add to `PROCESSORS` registry in Runner

### Adding File Type Support
1. Update `AttachmentProcessor` routing
2. Implement conversion in `MarkItDown`
3. Add metadata extraction
4. Update tests and documentation

## Performance Considerations

### Memory Management
- Streaming file processing
- Cleanup of temporary files
- Resource monitoring

### Processing Optimization
- Parallel source processing
- Caching of converted files
- Skip unchanged files

### Scalability
- Independent source processing
- Configurable thread count
- Resource usage limits
