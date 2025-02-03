---
description: "Logging standards and management practices"
globs:
  - "logs/**/*.log"
  - "src/**/logging.py"
  - "!logs/archive/**"
  - "!logs/temp/**"
version: 1.0.0
status: Active
---

# Logging Rules
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines logging standards, practices, and management policies. It ensures consistent, efficient, and maintainable logging across the project. This rule works in conjunction with error handling standards (40-error-handling.md) for error reporting, operation modes (50-operation-modes.md) for mode-specific logging requirements, and command triggers (70-command-triggers.md) for command execution logging.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Log Levels](#log-levels)
- [Format Standards](#format-standards)
- [Rotation Policies](#rotation-policies)
- [Aggregation](#aggregation)
- [Monitoring](#monitoring)
- [Configuration](#configuration)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)

## Log Levels
### Debug
Purpose: Detailed information for debugging
- Variable values
- Function entry/exit
- State changes
- Performance data
- Temporary debugging

### Info
Purpose: General operational events
- Application startup
- Configuration loaded
- Task completion
- State transitions
- User actions

### Warning
Purpose: Potential issues or unexpected states
- Deprecated features
- Resource usage high
- Missing optional data
- Slow performance
- Recovery attempts

### Error
Purpose: Error events that might still allow operation
- Exception caught (see 40-error-handling.md for hierarchy)
- Task failure
- Connection issues
- Data validation
- Resource unavailable
- Mode transition failures (see 50-operation-modes.md)

### Critical
Purpose: Critical events causing system failure
- Application crash
- Data corruption
- Security breach
- Resource exhaustion
- System halt

## Format Standards
### Message Template
```
{timestamp} [{level}] {logger}: {message} {context}
```

### Timestamp Format
ISO 8601 (YYYY-MM-DD HH:mm:ss.sss±ZZZZ)

### Structured Format
```json
{
    "timestamp": "2025-01-31T10:30:00.000Z",
    "level": "ERROR",
    "logger": "app.module",
    "message": "Operation failed",
    "context": {
        "operation": "data_process",
        "user_id": "12345",
        "error_code": "ERR001"
    }
}
```

### Required Context
- timestamp
- level
- logger
- message

### Optional Context
- correlation_id
- user_id
- session_id
- request_id
- version

## Rotation Policies
### Triggers
- Size: 100MB per file
- Time: Daily rotation
- Application restart
- Manual rotation
- Error threshold

### Retention
- 7 days of daily logs
- 4 weeks of weekly logs
- 12 months of monthly logs
- Compress archived logs
- Secure deletion

### Naming
Pattern: `{app}-{YYYY-MM-DD}.log[.gz]`
Example: `myapp-2025-01-31.log.gz`

## Aggregation
### Collection
- Centralized logging
- Structured format
- Secure transport
- Buffer handling
- Failure recovery

### Processing
- Parse structured data
- Enrich context
- Correlate events
- Filter sensitive data
- Index for search

### Storage
- Compressed archives
- Searchable index
- Backup strategy
- Retention policy
- Access control

## Monitoring
### Metrics
- Error rate
- Log volume
- Response time
- Resource usage
- User activity

### Alerts
- Error threshold
- Pattern detection
- Resource limits
- Security events
- System health

### Dashboards
- Error overview
- Performance metrics
- User activity
- Resource usage
- System health

## Configuration
### Setup
- Environment-based config
- Log level control
- Handler configuration
- Format definition
- Path management

### Handlers
- Console output
- File rotation
- Network transport
- Error notification
- Debug capture

### Integration
- Framework integration
- Library configuration
- Third-party handlers
- Custom formatters
- Context processors

## Mandatory Constraints
### MUST
- Use appropriate log levels
- Include required context
- Follow format standards
- Implement rotation policies
- Configure handlers properly
- Secure sensitive data
- Monitor log metrics
- Handle log failures
- Clean up old logs
- Document log formats
- Use structured logging
- Follow naming conventions

### MUST NOT
- Log sensitive data
- Mix log formats
- Skip log rotation
- Ignore log failures
- Leave logs unmonitored
- Use inconsistent levels
- Bypass handlers
- Disable logging
- Fill disk space
- Log without context
- Mix timestamp formats
- Skip log cleanup

## Advisory Guidelines
### SHOULD
- Use context managers
- Implement buffering
- Monitor performance
- Review logs regularly
- Update configurations
- Test log rotation
- Document patterns
- Analyze metrics
- Maintain dashboards
- Follow best practices

### RECOMMENDED
- Regular reviews
- Pattern analysis
- Storage optimization
- Alert tuning
- Format validation
- Performance profiling
- Resource monitoring
- Impact assessment
- Team training
- Documentation updates

## Exception Clauses
Logging exceptions allowed when:
- Emergency debugging
- System critical failures
- Resource constraints
- Legacy system integration
- Third-party limitations

## Examples
### Good Logging
```python
import logging
from typing import Any, Dict
from myapp.context import LogContext

logger = logging.getLogger(__name__)

def process_user_data(user_id: str, data: Dict[str, Any]) -> bool:
    """Process user data with proper logging.

    Args:
        user_id: User identifier
        data: User data to process

    Returns:
        bool: Success status
    """
    with LogContext(operation="process_user_data", user_id=user_id):
        try:
            logger.info("Starting user data processing", extra={"data_size": len(data)})
            result = validate_and_process(data)
            logger.info("User data processing completed", extra={"status": "success"})
            return result
        except ValidationError as e:
            logger.error("Data validation failed", extra={"error": str(e)})
            return False
        except ProcessingError as e:
            logger.critical("Processing failed", extra={"error": str(e)})
            raise
```

### Bad Logging
```python
def bad_logging(x):
    # No context, mixed formats, inappropriate level
    print("Processing started...")  # Don't use print for logging
    try:
        result = process(x)
        logging.info("Done")  # No context
    except:
        logging.error("Failed")  # No details
    return result
```

## Migration Notes
- Update log formats
- Implement structured logging
- Add monitoring
- Configure rotation
- Train team

## Dependencies
- @rule(40-error-handling.md:error_reporting)
- @rule(50-operation-modes.md:mode_logging)
- @rule(70-command-triggers.md:command_logging)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined log levels
- Set format standards
- Added rotation policies
