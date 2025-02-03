---
description: "Operation modes and transition rules for system behavior"
globs:
  - "src/**/modes.py"
  - "src/**/operations.py"
  - "!src/legacy/**/*.py"
  - "!src/deprecated/**/*.py"
version: 1.0.0
status: Active
---

# Operation Modes Rules
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines operation modes, transition rules, and safety controls. It ensures consistent, safe, and controlled system behavior across different operational states. This rule works in conjunction with error handling standards (40-error-handling.md) for state preservation during errors and logging standards (41-logging.md) for mode-specific logging requirements.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Mode Definitions](#mode-definitions)
- [Transition Rules](#transition-rules)
- [Restrictions](#restrictions)
- [Override Procedures](#override-procedures)
- [Workflows](#workflows)
- [Safety Controls](#safety-controls)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)

## Mode Definitions
### Plan Mode
Trigger: `-plan`
Description: Analysis and planning mode without system modifications

#### Characteristics
- Read-only operations
- Impact analysis
- Resource estimation
- Safety validation
- Plan generation

#### Indicators
- Mode indicator: [PLAN]
- Read-only operations enforced

#### Response Template
```
[PLAN MODE] Analyzing Request...
Current Context:
- Active Rules: [list relevant rules]
- Constraints: [list active constraints]

Analysis:
[Analysis content]

Proposed Actions:
[List of actions]

Awaiting confirmation to proceed to ACT mode.
```

#### Restrictions
- No file system changes
- No state modifications
- No external API calls
- No resource allocation
- No command execution

### Act Mode
Trigger: `-act`
Description: Execution mode for system modifications

#### Characteristics
- Write operations
- State changes
- Resource management
- Command execution
- External interactions

#### Indicators
- Mode indicator: [ACT]
- Write operations enabled

#### Response Template
```
[ACT MODE] Executing Actions...
Validated Constraints:
- [List of checked constraints]

Executing:
[Current action]

Progress:
[Action status]

Next Steps:
[Upcoming actions]
```

#### Requirements
- Valid trigger command
- Basic safety checks
- Resource validation
- Response template compliance
- Status tracking enabled

## Transition Rules
### Requirements
- Valid trigger command
- Basic safety checks
- Clean system state

### Process
#### Pre-transition
- Basic state check
- Mode compatibility

#### Execution
- Mode switch
- Permission updates
- Logging transition

#### Post-transition
- Mode indicator update
- Operation confirmation
- User notification

## Restrictions
### Plan Mode
#### Filesystem
- Read-only access
- No file creation
- No modifications
- No deletions
- Path validation

#### Operations
- Analysis only
- Resource estimation
- Impact assessment
- Plan validation
- Safety checks

### Act Mode
#### Filesystem
- Workspace limits
- Permission checks
- Change tracking
- Backup creation
- State preservation

#### Operations
- Authorization required
- Resource limits
- Operation logging
- State tracking
- Rollback points

#### Processing Limits
- Default --limit of 5 items required
- Override only with explicit user command
- Use --processor when targeting specific processor
- Document any limit overrides in logs
- Monitor context window usage

#### Testing
##### Bug Fixes
- Reproduction test case required first
- Test must demonstrate bug before fix
- Skip only if integration too complex
- Document skipped test cases
- Include bug reference in test

##### Source Data
- Use real config directories
- Enforce --limit in tests
- Use --processor when applicable
- Maintain test fixtures
- Document data requirements

## Override Procedures
### Authorization
- Admin credentials
- Emergency protocol
- Time limitation
- Scope restriction
- Full logging

### Process
- Override request
- Risk assessment
- Authorization check
- Mode transition
- Enhanced monitoring

### Limitations
- Time-bound access
- Restricted operations
- Mandatory logging
- Review requirement
- Auto-expiration

## Workflows
### Plan Mode
#### Analysis
- Resource scanning
- Impact assessment
- Dependency check
- Risk evaluation
- Plan generation

#### Validation
- Safety checks
- Resource validation
- Permission verification
- State assessment
- Plan review

### Act Mode
#### Execution
- Pre-execution check
- Resource allocation
- Operation execution
- State tracking
- Result validation

#### Monitoring
- Resource usage
- Operation progress
- State changes
- Error detection
- Performance metrics

## Safety Controls
### Validation
- Permission checks
- Resource limits
- State validation
- Operation safety
- Impact assessment

### Monitoring
- Resource usage
- Operation status
- Error detection (see 40-error-handling.md)
- Performance metrics
- Security events
- Mode-specific logging (see 41-logging.md)

### Protection
- Resource isolation
- State preservation
- Error prevention
- Data protection
- Access control

## Mandatory Constraints
### PLAN Mode Constraints
#### MUST
- Validate all operations before execution
- Perform impact analysis for proposed changes
- Generate detailed execution plan
- Check resource requirements
- Verify safety constraints
- Document proposed changes

#### MUST NOT
- Make direct file system changes
- Modify system state
- Execute commands without validation
- Allocate resources
- Make external API calls

### ACT Mode Constraints
#### MUST
- Follow approved plan from PLAN mode
- Validate resources before allocation
- Track all state changes
- Create recovery points
- Log all operations
- Verify results

#### MUST NOT
- Execute unapproved operations
- Exceed resource limits
- Skip validation steps
- Ignore safety controls
- Bypass logging

## Advisory Guidelines
### SHOULD
- Use mode indicators
- Implement monitoring
- Document transitions
- Review changes
- Test workflows
- Validate states
- Track resources
- Analyze impact
- Maintain logs
- Follow best practices

### RECOMMENDED
- Regular reviews
- State validation
- Resource tracking
- Alert tuning
- Documentation updates
- Performance profiling
- Impact assessment
- Team training
- Mode testing
- Workflow validation

## Exception Clauses
Operation mode exceptions allowed when:
- Emergency fixes needed
- System critical failures
- Resource constraints
- Legacy system integration
- Third-party limitations

## Examples
### Good Mode Usage
```python
from typing import Optional
from myapp.modes import PlanMode, ActMode
from myapp.context import OperationContext

def process_data(data_id: str, mode: str = "plan") -> bool:
    """Process data with proper mode handling.

    Args:
        data_id: Data identifier
        mode: Operation mode (plan/act)

    Returns:
        bool: Success status
    """
    context = OperationContext(operation="process_data", data_id=data_id)

    if mode == "plan":
        with PlanMode(context) as plan:
            # Analysis only, no modifications
            impact = plan.analyze_impact()
            resources = plan.estimate_resources()
            return plan.validate_safety()

    elif mode == "act":
        with ActMode(context) as act:
            try:
                # Actual modifications with safety
                act.validate_resources()
                act.execute_changes()
                act.verify_state()
                return True
            except StateError as e:
                act.rollback()
                return False
```

### Bad Mode Usage
```python
def bad_mode_handling(x):
    # No mode control, mixed operations
    analyze_data(x)  # Read operation
    modify_state(x)  # Write operation in same context
    return True  # No validation or safety checks
```

## Migration Notes
- Update mode handling
- Implement transitions
- Add safety controls
- Configure monitoring
- Train team

## Dependencies
- @rule(02-base.md:format_requirements)
- @rule(40-error-handling.md:error_procedures)
- @rule(41-logging.md:log_levels)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined operation modes
- Set transition rules
- Added safety controls
