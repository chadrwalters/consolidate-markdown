---
description: "Error handling standards and recovery procedures"
globs:
  - "src/**/exceptions.py"
  - "src/**/errors.py"
  - "!src/legacy/**/*.py"
  - "!src/deprecated/**/*.py"
version: 1.0.0
status: Active
---

# Error Handling Rules
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines the error handling standards, exception hierarchy, and recovery procedures. It ensures consistent, robust, and maintainable error management across the project. This rule works in conjunction with logging standards (41-logging.md) for error reporting, operation modes (50-operation-modes.md) for state preservation during errors, and command triggers (70-command-triggers.md) for command failure handling.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Exception Hierarchy](#exception-hierarchy)
- [Error Procedures](#error-procedures)
- [Recovery Processes](#recovery-processes)
- [Error Reporting](#error-reporting)
- [Monitoring and Debugging](#monitoring-and-debugging)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)

## Exception Hierarchy
### Base Exceptions
- AppError: Base application exception
- ConfigError: Configuration issues
- ProcessError: Processing failures
- ValidationError: Input validation
- ResourceError: Resource access

### Specialized Exceptions
#### Configuration
- ConfigNotFound
- ConfigInvalid
- ConfigPermission

#### Process
- ProcessTimeout
- ProcessFailed
- ProcessInterrupted

#### Validation
- InputInvalid
- FormatInvalid
- TypeMismatch

#### Resource
- ResourceNotFound
- ResourceUnavailable
- ResourcePermission

## Error Procedures
### Function Level
- Handle known errors
- Document exceptions
- Preserve context
- Clean up resources
- Log appropriately

### Module Level
- Aggregate related errors
- Provide error context
- Handle module-specific issues
- Log error patterns
- Maintain consistency

### Application Level
- Global error handling
- User feedback
- System recovery
- Error reporting
- Monitoring alerts

## Recovery Processes
### Retry Strategy
- Exponential backoff
- Maximum attempts
- Failure conditions
- Success criteria
- Timeout limits

### Fallback Strategy
- Alternative methods
- Degraded operation
- User notification
- Data preservation
- Service continuity

### Cleanup Process
- Resource release
- State restoration
- Data consistency
- Log completion
- Notify monitoring

## Error Reporting
### Requirements
- Error ID generation
- Stack trace preservation
- Context capture
- User impact assessment
- Resolution status
- Integration with logging system (see 41-logging.md)
- Mode-aware error handling (see 50-operation-modes.md)

### Format
```json
{
    "error_id": "unique-id",
    "timestamp": "iso-8601",
    "level": "error",
    "code": "error-code",
    "message": "user-friendly-message",
    "details": "technical-details",
    "stack_trace": "formatted-trace",
    "context": {
        "user": "user-info",
        "action": "action-info",
        "state": "state-info"
    }
}
```

## Monitoring and Debugging
### Tools
- pdb/ipdb for interactive
- logging for tracing
- debugpy for remote
- profilers for performance
- memory trackers

### Metrics
- Error rates
- Recovery success
- Performance impact
- Resource usage
- User impact

### Alerts
- Critical failures
- Pattern detection
- Resource exhaustion
- Security incidents
- Recovery failures

## Mandatory Constraints
### MUST
- Use proper exception hierarchy
- Handle all known errors
- Document exceptions
- Clean up resources
- Log appropriately
- Generate error IDs
- Preserve context
- Report errors
- Monitor metrics
- Follow recovery procedures
- Maintain consistency
- Update documentation

### MUST NOT
- Use bare except
- Silence errors
- Skip cleanup
- Leave resources open
- Mix error levels
- Ignore context
- Skip logging
- Hide stack traces
- Break hierarchy
- Bypass monitoring
- Leave errors undocumented
- Skip error reporting

## Advisory Guidelines
### SHOULD
- Use specific exceptions
- Implement retries
- Monitor patterns
- Review regularly
- Update procedures
- Test recovery
- Document patterns
- Analyze impacts
- Maintain alerts
- Follow best practices

### RECOMMENDED
- Regular reviews
- Pattern analysis
- Recovery testing
- Alert tuning
- Documentation updates
- Performance profiling
- Resource monitoring
- Impact assessment
- User feedback
- Team training

## Exception Clauses
Error handling exceptions allowed when:
- Emergency fixes needed
- System critical failures
- Resource constraints
- Legacy system integration
- Third-party limitations

## Examples
### Good Error Handling
```python
from typing import Optional
from myapp.exceptions import ConfigError, ResourceError

def get_user_config(user_id: str) -> dict:
    """Get user configuration safely.

    Args:
        user_id: User identifier

    Returns:
        User configuration dictionary

    Raises:
        ConfigError: If configuration is invalid
        ResourceError: If resource is unavailable
    """
    try:
        config = load_config(user_id)
        validate_config(config)
        return config
    except FileNotFoundError as e:
        raise ConfigError(f"Config not found for user {user_id}") from e
    except ValidationError as e:
        raise ConfigError(f"Invalid config for user {user_id}") from e
    except IOError as e:
        raise ResourceError("Unable to access config storage") from e
    finally:
        cleanup_resources()
```

### Bad Error Handling
```python
def bad_error_handling(x):
    try:
        # Bare except, no cleanup, no context
        result = process(x)
        return result
    except:  # Never do this!
        print("Error occurred")
        return None
```

## Migration Notes
- Update exception hierarchy
- Implement error reporting
- Add monitoring
- Test recovery
- Train team

## Dependencies
- @rule(02-base.md:format_requirements)
- @rule(10-python-style.md:code_standards)
- @rule(11-python-typing.md:type_hints)
- @rule(41-logging.md:error_logging)
- @rule(50-operation-modes.md:state_preservation)
- @rule(70-command-triggers.md:error_handling)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined error hierarchy
- Set handling standards
- Added recovery procedures
