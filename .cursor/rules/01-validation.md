---
description: "Rule validation and conflict detection system"
globs:
  - "**/*"  # This rule applies to all files as it handles rule validation
version: 1.0.0
status: Active
---

# Rule Validation and Conflict Detection
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines the validation process for rules, including conflict detection, resolution protocols, logging requirements, and phase/task validation. It ensures rule consistency, proper handling of conflicts, and validates phase completion criteria.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Rule Scanner](#rule-scanner)
- [Conflict Management](#conflict-management)
- [Phase Validation](#phase-validation)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)

## Rule Scanner
### Scanner Components
1. File System Scanner
   - Discover rule files
   - Validate file names
   - Check file permissions
   - Verify file integrity

2. Content Parser
   - Parse frontmatter
   - Extract metadata
   - Validate structure
   - Check formatting

3. Dependency Analyzer
   - Build dependency graph
   - Detect cycles
   - Validate references
   - Check version compatibility

4. Constraint Extractor
   - Parse MUST/MUST NOT rules
   - Extract SHOULD/RECOMMENDED
   - Validate syntax
   - Check completeness

### Scanning Process
1. Initialize scanner
2. Discover rule files
3. Parse content
4. Extract metadata
5. Build indexes
6. Generate reports

### Validation Checks
1. File format validation
2. Structure verification
3. Metadata completeness
4. Dependency resolution
5. Constraint validation
6. Cross-reference checking

## Conflict Management
### Conflict Index
- Rule pairs with conflicts
- Conflict severity levels
- Resolution requirements
- Override conditions
- Exception cases

### Resolution Protocol
1. Detect conflict
2. Analyze severity
3. Identify resolution options
4. Present to user
5. Apply resolution
6. Log decision

### Conflict Types
1. Direct Contradictions
   - Opposing constraints
   - Incompatible requirements
   - Conflicting glob patterns

2. Indirect Conflicts
   - Dependency cycles
   - Overlapping scopes
   - Implicit contradictions

3. Version Conflicts
   - Incompatible versions
   - Deprecated features
   - Breaking changes

### Logging System
#### Log Levels
- ERROR: Blocking conflicts
- WARNING: Potential issues
- INFO: Resolution actions
- DEBUG: Validation details
- TRACE: Scanner operations

#### Log Categories
- Rule Discovery
- Content Validation
- Conflict Detection
- Resolution Actions
- System State
- User Decisions

#### Log Format
```
[LEVEL] [TIMESTAMP] [CATEGORY] Message
- Context: {relevant details}
- Action: {taken or required}
- Status: {current state}
```

## Phase Validation
### Completion Criteria
- All tasks in phase must be completed
- All validation checks must pass
- No unresolved conflicts
- All required artifacts present
- Documentation updated
- .Plan status updated
- .Plan consistency verified

### Task Sequence Validation
- Tasks must be executed in order
- Dependencies must be satisfied
- State must be consistent
- Progress must be tracked
- .Plan must reflect current state

### Phase Transition Requirements
- All completion criteria met
- Validation results logged
- Status report generated
- User confirmation obtained (if required)
- .Plan updated and validated
- .Plan consistency verified

### Validation Reporting
- Task completion status
- Phase completion status
- Validation results
- Error conditions
- Warnings and notifications
- .Plan update status
- .Plan consistency status

## Mandatory Constraints
### MUST
- Validate all rules during bootup
- Check for conflicting constraints between rules
- Log all validation results
- Report conflicts to user
- Maintain conflict index
- Track rule dependencies
- Validate glob patterns
- Verify rule format compliance
- Check semantic descriptions
- Validate phase completion criteria
- Track task completion status
- Verify phase transitions
- Log validation results for each phase
- Validate .Plan status updates
- Verify .Plan consistency
- Track phase completion in .Plan
- Validate phase completion criteria against .Plan
- Ensure .Plan reflects current state
- Run complete rule scan before validation
- Maintain detailed validation logs
- Follow resolution protocol
- Track conflict resolutions

### MUST NOT
- Allow conflicting rules without resolution
- Skip validation steps
- Ignore dependency cycles
- Proceed with invalid rules
- Override user conflict decisions
- Skip phase completion validation
- Allow invalid task sequences
- Ignore phase transition requirements
- Allow inconsistent .Plan state
- Skip .Plan validation
- Proceed with invalid .Plan status
- Bypass conflict resolution
- Ignore validation errors
- Skip logging requirements

## Advisory Guidelines
### SHOULD
- Cache validation results
- Provide conflict resolution suggestions
- Group related conflicts
- Track resolution history
- Monitor rule changes
- Track phase progress
- Log task sequence
- Report validation metrics
- Monitor .Plan changes
- Track .Plan history
- Validate .Plan formatting

### RECOMMENDED
- Regular validation checks
- Automated conflict detection
- Clear error reporting
- Resolution templates
- Performance optimization
- Phase completion reports
- Task sequence validation
- Progress tracking
- .Plan backup creation
- .Plan version control
- .Plan consistency checks

## Exception Clauses
Validation exceptions allowed when:
- Emergency hotfixes needed
- System critical failures
- Resource constraints
- Legacy system integration
- Third-party limitations
- Manual override authorized
- Temporary bypass approved
- Phased migration in progress

## Examples
### Good Validation Usage
```python
from typing import Optional
from myapp.validation import RuleScanner, ConflictManager
from myapp.context import ValidationContext

def validate_rules(phase: str) -> bool:
    """Validate rules with proper conflict detection.

    Args:
        phase: Current phase identifier

    Returns:
        bool: Validation success status
    """
    context = ValidationContext(operation="validate_rules", phase=phase)

    try:
        # Initialize scanner and conflict manager
        with RuleScanner(context) as scanner:
            # Discover and validate rules
            rules = scanner.discover_rules()
            validation_result = scanner.validate_rules(rules)

            if not validation_result.is_valid:
                # Handle conflicts if found
                with ConflictManager(context) as conflicts:
                    resolution = conflicts.resolve(
                        validation_result.conflicts,
                        interactive=True
                    )

                    if resolution.requires_user_action:
                        return False

                    # Apply resolutions and revalidate
                    scanner.apply_resolutions(resolution)
                    return scanner.validate_rules(rules).is_valid

            return True

    except ValidationError as e:
        logger.error("Rule validation failed", extra={"error": str(e)})
        raise
    finally:
        # Ensure cleanup
        cleanup_resources()
```

### Bad Validation Usage
```python
def bad_validation(rules):
    # No proper validation or conflict handling
    scanner = RuleScanner()
    result = scanner.validate(rules)  # No context or error handling
    return result  # No conflict resolution or cleanup
```

## Migration Notes
- Update validation process
- Implement conflict detection
- Add resolution handling
- Configure logging
- Train team

## Dependencies
- @rule(00-bootup.md:startup_sequence)
- @rule(40-error-handling.md:error_procedures)
- @rule(41-logging.md:log_levels)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined validation process
- Added conflict management
- Set phase validation rules
