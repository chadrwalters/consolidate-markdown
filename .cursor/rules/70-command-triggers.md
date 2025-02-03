---
description: "Command trigger patterns and automation rules"
globs:
  - "src/**/triggers/**/*.py"
  - "src/**/commands/**/*.py"
  - "src/**/integrations/**/*.py"
  - "src/**/adapters/**/*.py"
  - "!src/**/deprecated/**/*.py"
  - "!src/**/legacy/**/*.py"
version: 1.0.0
status: Active
---

# Command Triggers Rules
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines command trigger patterns, automation rules, and command formats. It ensures consistent, secure, and controlled command execution across the project. This rule works in conjunction with operation modes (50-operation-modes.md) for mode-specific triggers, error handling standards (40-error-handling.md) for command failures, and logging standards (41-logging.md) for command execution logging.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Trigger Patterns](#trigger-patterns)
- [Command Formats](#command-formats)
- [Automation Rules](#automation-rules)
- [Security](#security)
- [Error Handling](#error-handling)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)

## Trigger Patterns
### Mode Transitions
#### Plan Mode (see 50-operation-modes.md)
Pattern: `^-plan\b`
Description: Trigger PLAN mode
Examples:
- `-plan`
- `-plan <scope>`

#### Act Mode (see 50-operation-modes.md)
Pattern: `^-act\b`
Description: Trigger ACT mode
Examples:
- `-act`
- `-act <scope>`

### Pattern Definition
- Regular expression based patterns
- Natural language triggers
- Context-aware activation
- Mode-specific patterns (see 50-operation-modes.md)
- Priority-based execution

### Pattern Categories
#### File Operations
- Creation triggers
- Modification triggers
- Deletion triggers
- Move/rename triggers

#### System Operations
- Resource monitoring
- Performance triggers
- Health check triggers
- Error detection (see 40-error-handling.md)

#### User Interactions
- Command input
- Selection events
- Navigation events
- Focus changes

## Command Formats
### Mode Commands
#### Plan Mode
Syntax: `-plan [scope]`
Description: Enter planning mode (see 50-operation-modes.md)
Options:
- scope: Optional scope limitation

Examples:
- `-plan`
- `-plan filesystem`
- `-plan analysis`

#### Act Mode
Syntax: `-act [scope]`
Description: Enter action mode (see 50-operation-modes.md)
Options:
- scope: Optional scope limitation

Examples:
- `-act`
- `-act filesystem`
- `-act implementation`

### Processing Limits
#### Limit Option
Syntax: `--limit <count>`
Description: Limit number of items processed
Default: 5
Required: true

Options:
- count: Maximum number of items to process

Examples:
- `--limit 5`
- `--limit 10`

Exceptions:
- When explicitly overridden by user

#### Processor Option
Syntax: `--processor <n>`
Description: Limit processing to specific processor

Options:
- name: Name of processor to use

Examples:
- `--processor bear`
- `--processor chatgpt`
- `--processor claude`
- `--processor xbookmarks`

### Command Structure
- Command prefix requirements
- Parameter formatting
- Option specifications
- Flag definitions
- Escape sequences
- Variable substitution

### Command Restrictions
#### Prohibited Patterns
- Never use '| cat' or pipe to cat
- Use direct command output instead
- For git commands, use -P or --no-pager options
- For less/more, use alternative output methods
- For head/tail, use direct line number options

### Command Types
#### File System
- Path manipulation
- Content operations
- Permission changes
- Attribute updates

#### Process
- Execution control
- Resource allocation
- Priority management
- State transitions (see 50-operation-modes.md)

#### System
- Configuration updates
- Service management
- Security operations
- Maintenance tasks

## Automation Rules
### Execution Flow
- Pre-execution validation
- Permission checking
- Resource verification
- State validation (see 50-operation-modes.md)
- Context evaluation
- Post-execution cleanup

### Constraints
- Resource limits
- Time constraints
- Concurrency limits
- Dependency checks
- State requirements
- Mode restrictions (see 50-operation-modes.md)

### Chain Execution
- Sequential execution
- Parallel processing
- Dependency resolution
- Error propagation (see 40-error-handling.md)
- State management
- Result aggregation

## Security
### Authorization
- Permission levels
- Role requirements
- Context validation
- Token verification
- Session management
- Access logging (see 41-logging.md)

### Validation
- Input sanitization
- Parameter validation
- Path verification
- Resource access checks
- State validation
- Output verification

### Controls
- Rate limiting
- Resource isolation
- Audit logging (see 41-logging.md)
- Error masking
- Version control
- Secure defaults

## Error Handling
### Categories (see 40-error-handling.md)
- Syntax errors
- Permission errors
- Resource errors
- State errors
- Timeout errors
- System errors

### Recovery (see 40-error-handling.md)
- Error detection
- State preservation
- Rollback procedures
- Retry strategies
- Fallback options
- Error reporting

### Prevention
- Input validation
- State verification
- Resource checking
- Mode compatibility (see 50-operation-modes.md)

## Mandatory Constraints
### MUST
- Use proper trigger patterns
- Follow command formats
- Validate all input
- Check permissions
- Handle errors properly (see 40-error-handling.md)
- Log all commands (see 41-logging.md)
- Verify state changes
- Implement security
- Follow automation rules
- Clean up resources
- Document commands
- Use proper limits
- Follow mode restrictions (see 50-operation-modes.md)

### MUST NOT
- Use prohibited patterns
- Skip validation
- Bypass security
- Ignore errors
- Leave resources open
- Mix command types
- Break mode rules
- Hide command output
- Skip logging
- Exceed limits
- Break workflows
- Ignore state changes

## Advisory Guidelines
### SHOULD
- Use clear patterns
- Implement monitoring
- Document triggers
- Review commands
- Test workflows
- Validate states
- Track resources
- Analyze impact
- Maintain logs
- Follow best practices

### RECOMMENDED
- Regular reviews
- Pattern analysis
- Command testing
- Security audits
- Documentation updates
- Performance profiling
- Impact assessment
- Team training
- Workflow validation
- State verification

## Exception Clauses
Command trigger exceptions allowed when:
- Emergency fixes needed
- System critical failures
- Resource constraints
- Legacy system integration
- Third-party limitations

## Examples
### Good Command Pattern
```python
from myapp.triggers import CommandTrigger
from myapp.modes import PlanMode
from myapp.logging import Logger

def handle_plan_command(scope: str = None) -> None:
    """Handle plan mode command trigger.

    Args:
        scope: Optional scope limitation
    """
    try:
        trigger = CommandTrigger("-plan", scope)
        trigger.validate()
        with PlanMode():
            trigger.execute()
    except Exception as e:
        Logger.error(f"Plan command failed: {e}")
        raise
```

### Bad Command Pattern
```python
# Missing validation and error handling
def bad_command(cmd):
    os.system(cmd)  # Direct execution without checks
```

## Migration Notes
- Update command patterns
- Implement new triggers
- Add validation
- Update logging
- Test workflows

## Dependencies
- @rule(40-error-handling.md:exception_hierarchy)
- @rule(41-logging.md:command_logging)
- @rule(50-operation-modes.md:mode_transitions)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined trigger patterns
- Set command formats
- Added automation rules
- Specified security requirements
- Added integration patterns
- Defined adapter interfaces
- Added cross-references to related rules
