# Rule Creation Guide

## Introduction
This guide walks through the process of creating new rules for the system. Follow these steps to ensure your rule is properly structured and integrated.

## Quick Start
1. Copy the template from `00-template.md`
2. Choose an appropriate numeric prefix
3. Fill in all required sections
4. Add glob patterns
5. Run validation

## Detailed Steps

### 1. Rule Planning
Before creating a rule, consider:
- What problem does it solve?
- Which files should it affect?
- What are the key constraints?
- How will it be validated?
- What dependencies exist?

### 2. File Creation
```bash
# Copy template
cp .cursor/rules/00-template.md .cursor/rules/XX-your-rule.md

# Edit the new rule
code .cursor/rules/XX-your-rule.md
```

### 3. Frontmatter
```yaml
---
description: "Clear description of rule's purpose"
globs:
  - "pattern/to/match/*.ext"  # Files this rule applies to
version: 1.0.0
status: Active  # or Draft, Deprecated
---
```

### 4. Required Sections
Every rule must include:
1. Title and Version
2. Abstract/Purpose
3. Table of Contents
4. Mandatory Constraints
5. Advisory Guidelines
6. Exception Clauses
7. Examples
8. Migration Notes
9. Dependencies
10. Changelog

### 5. Glob Patterns
Define patterns in your rule:
```yaml
globs:
  - "src/**/*.py"      # Match all Python files
  - "!src/legacy/**"   # Exclude legacy directory
```

Reference existing patterns:
```yaml
globs:
  - "@patterns.source.python"  # Use predefined pattern
```

### 6. Constraints
Define clear constraints:

```markdown
### MUST
- Specific requirement
- Another requirement

### MUST NOT
- Specific prohibition
- Another prohibition

### SHOULD
- Recommended practice
- Another recommendation
```

### 7. Examples
Include both good and bad examples:

```markdown
### Good Example
```python
# Good code example with explanation
```

### Bad Example
```python
# Bad code example with explanation
```
```

### 8. Validation
Run the validation tools:
```bash
# Validate structure
pre-commit run rule-validation --files .cursor/rules/XX-your-rule.md

# Check conflicts
pre-commit run rule-conflict-check --files .cursor/rules/XX-your-rule.md

# Generate summary
pre-commit run rule-summary --files .cursor/rules/XX-your-rule.md
```

### 9. Documentation
1. Update rule references
2. Add cross-references
3. Document dependencies
4. Update changelogs

## Best Practices
1. Use clear, specific language
2. Include practical examples
3. Document exceptions clearly
4. Keep patterns focused
5. Maintain cross-references
6. Update related rules
7. Test validation

## Common Issues
1. Missing required sections
2. Vague constraints
3. Conflicting patterns
4. Incomplete examples
5. Missing dependencies

## Rule Lifecycle
1. Draft -> Active -> Deprecated
2. Version increments for changes
3. Migration notes for updates
4. Changelog maintenance

## Templates
See [00-template.md](../../.cursor/rules/00-template.md) for the full template structure.

## Additional Resources
- [Rules Overview](overview.md)
- [Base Standards](../../.cursor/rules/02-base.md)
