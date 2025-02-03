# Rules System Overview

## Introduction
The rules system provides a standardized framework for maintaining consistency and quality across the project. Rules are organized in a flat directory structure with numeric prefixes indicating their category and purpose.

## Directory Structure
```
.cursor/rules/
├── 00-startup.md       # Core startup sequence
├── 01-validation.md    # Rule validation system
├── 02-base.md         # Base system standards
├── 10-python-style.md # Python coding standards
├── ...                # Additional rules
└── globs.yaml         # Pattern matching configuration
```

## Rule Categories

### Core Rules (00-02)
Foundation rules that define system behavior and validation:
- Startup sequence
- Rule validation
- Base standards

### Language Rules (10-19)
Language-specific coding standards:
- Python style guide
- Type hint requirements
- Testing standards

### Documentation Rules (20-29)
Documentation and formatting requirements:
- Markdown style guide
- Documentation standards

### Process Rules (30-39)
Development workflow standards:
- Git workflow
- Pre-commit hooks

### Operation Rules (40-59)
System operation standards:
- Error handling
- Logging
- Operation modes

### Integration Rules (60-79)
External integration standards:
- Command triggers
- Service integrations

## Rule Structure
Each rule follows a standardized format:

```markdown
---
description: "Rule purpose"
globs:
  - "pattern/to/match/*.ext"
version: 1.0.0
status: Active
---

# Rule Title
Version: 1.0.0
Last Updated: YYYY-MM-DD

## Abstract/Purpose
...

## Table of Contents
...

## Sections
...
```

## Validation System
Rules are automatically validated through:

### Pre-commit Hooks
- Structure validation
- Pattern verification
- Cross-reference checking

### CI/CD Pipeline
- Automated validation
- Conflict detection
- Summary generation

### Documentation Generation
- Quick references
- Constraint summaries
- Dependency graphs

## Pattern Matching
Rules use glob patterns to define their scope:

```yaml
# Example from globs.yaml
patterns:
  source:
    python:
      - "src/**/*.py"
      - "!src/**/tests/**"
```

## Best Practices
1. Follow the standardized format
2. Use clear, specific constraints
3. Include practical examples
4. Document exceptions
5. Maintain cross-references
6. Keep patterns focused
7. Update changelogs

## Integration
The rules system integrates with:
- Pre-commit hooks
- CI/CD pipelines
- Documentation generation
- Code analysis tools

## Maintenance
Regular maintenance includes:
1. Reviewing and updating rules
2. Validating patterns
3. Checking cross-references
4. Generating documentation
5. Testing automation

## Additional Resources
- [Rule Creation Guide](creation.md)
- [Template Reference](../../.cursor/rules/00-template.md)
