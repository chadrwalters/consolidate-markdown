---
description: "Core system startup and initialization sequence"
globs:
  - "**/*"  # This rule applies to all files as it's the entry point
version: 1.0.0
status: Active
---

# System Startup Sequence
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines the standardized startup sequence for the entire system. It coordinates the initialization process, ensuring proper system bootup, rule loading, and mode initialization. For detailed validation procedures, see `01-validation.md`.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Startup Sequence](#startup-sequence)
- [Mode Management](#mode-management)
- [Response Templates](#response-templates)
- [Command Triggers](#command-triggers)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)
- [Dependencies](#dependencies)

## Startup Sequence
### 1. System Initialization
1. Initialize in read-only mode
2. Load core configuration
3. Set up logging system
4. Initialize error handlers
5. Verify system state

### 2. Rule Loading
1. Scan `.cursor/rules/` directory
2. Sort rules by numeric prefix (00-99)
3. Load rule metadata and globs
4. Trigger validation system (see `01-validation.md`)
5. Wait for validation completion

### 3. Documentation Review
1. Examine docs/ directory contents
2. Review key documentation files:
   - README.md
   - architecture.md
   - configuration.md
3. Build documentation hierarchy
4. Extract key requirements

### 4. Mode Initialization
1. Enter PLAN mode
2. Review current project state
3. Identify incomplete tasks
4. Note any blockers or dependencies
5. Build task dependency graph

### 5. Status Report
1. Confirm PLAN mode active
2. Summarize loaded rules
3. Report system state
4. Present initialization summary

## Mode Management
### PLAN Mode Requirements
- Enforce read-only operations
- Load all rules before proceeding
- Generate constraints summary
- Validate current state
- Require user confirmation

### Mode Transition Protocol
1. Validate current mode state
2. Check transition prerequisites
3. Verify user confirmation
4. Log mode change
5. Update system state

## Response Templates
### Bootup Response
```
[BOOTUP] Initializing AI Assistant...
1. Loading rules from .cursor/rules/
2. Processing rule dependencies
3. Validating rule conflicts
4. Generating constraints summary

Core Rules Loaded:
- [List key MUST/MUST NOT constraints]
- [List key SHOULD/RECOMMENDED guidelines]

Bootup Status: [SUCCESS/FAILURE]
Current Mode: PLAN

Ready for instructions. Please confirm to proceed.
```

### PLAN Mode Response
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

### ACT Mode Response
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

### Response Requirements
#### MUST
- Include mode indicator in header
- Show relevant constraints
- List active rules
- Provide clear status
- Request confirmation when needed
- Show progress for long operations
- Include next steps

#### MUST NOT
- Mix modes in single response
- Skip constraint validation
- Hide error conditions
- Proceed without confirmation
- Leave status unclear
- Omit next steps

## Command Triggers
### Primary Triggers
- `-startup`: Trigger system startup sequence
- `-init`: Alternative command for startup
- `-plan`: Run startup before entering plan mode

### Command Chaining Rules
1. When `-plan` is used without prior startup, run startup first
2. When `-init` or `-startup` is used, automatically enter PLAN mode
3. Commands must be executed in proper sequence
4. Status must be reported after each command

## Mandatory Constraints
### MUST
- Execute complete startup sequence
- Initialize in read-only mode
- Load all available rules
- Review key documentation
- Initialize in PLAN mode
- Report startup status
- Follow command trigger patterns
- Generate initialization report
- Track startup progress
- Report completion status

### MUST NOT
- Skip any startup steps
- Modify files during startup
- Execute tasks before completion
- Start in any mode other than PLAN
- Skip documentation review
- Proceed without rule loading
- Ignore command triggers
- Leave state uninitialized

## Advisory Guidelines
### SHOULD
- Generate concise status reports
- Group related documentation
- Track startup progress
- Log initialization results
- Maintain state history
- Monitor system changes
- Optimize startup sequence
- Document dependencies

### RECOMMENDED
- Clear status indicators
- Progress tracking
- Documentation indexing
- State tracking
- Performance optimization
- Startup metrics collection
- Health monitoring
- Resource management

## Exception Clauses
Startup exceptions allowed when:
- Emergency system recovery needed
- Critical system failure
- Resource constraints prevent full startup
- Documentation temporarily unavailable
- Rule system being upgraded
- Manual override authorized
- Temporary bypass approved
- Migration in progress

## Examples
### Good Startup Sequence
```python
from typing import Optional
from myapp.startup import StartupManager, RuleProcessor
from myapp.context import StartupContext

def initialize_system() -> bool:
    """Initialize system with proper startup sequence.

    Returns:
        bool: Startup success status
    """
    context = StartupContext(operation="initialize_system")

    try:
        # Initialize startup manager
        with StartupManager(context) as startup:
            # Initialize core systems
            startup.initialize_core_systems()

            # Load and validate rules
            rules = RuleProcessor().load_rules()
            await ValidationManager.validate_rules(rules)  # Async validation

            # Review documentation
            if not startup.review_documentation():
                raise StartupError("Documentation review failed")

            # Initialize PLAN mode
            if not startup.initialize_plan_mode():
                raise StartupError("Plan mode initialization failed")

            # Generate status report
            return startup.generate_status_report()

    except StartupError as e:
        logger.error("System startup failed", extra={"error": str(e)})
        raise
    finally:
        # Ensure cleanup
        cleanup_resources()
```

### Bad Startup Usage
```python
def bad_startup():
    # No proper sequence or validation
    rules = load_rules()  # No validation
    enter_plan_mode()  # No documentation review
    return True  # No status report
```

## Migration Notes
- Previous .mdc extension files should be converted to .md
- Command triggers should follow new pattern format
- All startup steps must be properly sequenced
- Previous bootup and AI startup rules are now consolidated

## Dependencies
- 01-validation.md (Rule validation system)
- 02-base.md (Base system standards)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Combined bootup and AI startup rules
- Established unified startup sequence
- Moved validation to 01-validation.md
- Added mode management
- Added status reporting
