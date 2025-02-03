---
description: "Template for creating standardized rule documentation"
globs:
  - "**/*.md"  # This template applies to all rule files
version: 1.0.0
status: Active
---

# Rule Documentation Template
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This template defines the standardized structure for all rule documentation. It provides the required sections and formatting guidelines. For core system standards and requirements, see `02-base.md`.

## Table of Contents
- [Required Sections](#required-sections)
- [Section Guidelines](#section-guidelines)
- [Template Usage](#template-usage)
- [Examples](#examples)
- [Dependencies](#dependencies)

## Required Sections
Every rule file MUST include these sections in order:

### 1. Frontmatter
```yaml
---
description: "Clear description of rule's purpose"
globs:
  - "pattern/to/match/*.ext"  # Files this rule applies to
version: 1.0.0
status: Active  # or Draft, Deprecated
---
```

### 2. Title and Version
```markdown
# Rule Title
Version: 1.0.0
Last Updated: YYYY-MM-DD
```

### 3. Abstract/Purpose
Brief description of what this rule governs and why it exists.

### 4. Table of Contents
Standard sections to include:
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- Additional rule-specific sections
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)
- [Dependencies](#dependencies)

### 5. Rule-Specific Sections
Add sections relevant to your rule type:
- Technical requirements
- Workflows
- Validation steps
- Configuration details
- Integration points

### 6. Mandatory Constraints
```markdown
### MUST
- Clear, specific requirements
- One requirement per line
- Active voice, explicit terms

### MUST NOT
- Clear prohibitions
- Specific actions to avoid
- Include rationale if needed
```

### 7. Advisory Guidelines
```markdown
### SHOULD
- Recommended practices
- Include reasoning
- Note implications

### RECOMMENDED
- Best practices
- Optimization tips
- Alternative approaches
```

### 8. Exception Clauses
Document allowed exceptions:
- When they apply
- Who can authorize
- Required documentation
- Alternative approaches

### 9. Examples
```markdown
### Good Example
[Example with explanation]

### Bad Example
[Counter-example with explanation]
```

### 10. Migration Notes
- Steps for adoption
- Breaking changes
- Timeline guidance
- Transition steps

### 11. Dependencies
- List required rules
- External dependencies
- Version requirements

### 12. Changelog
```markdown
### 1.0.0 (YYYY-MM-DD)
- Initial version
- Key changes
```

## Section Guidelines
### Content Requirements
- Each section must be complete
- Use clear, concise language
- Include practical examples
- Reference other rules properly
- Follow base standards (see `02-base.md`)

### Formatting Rules
- Use proper heading levels
- Consistent list formatting
- Code block language tags
- Proper link references
- Standard section order

## Template Usage
### Creating New Rules
1. Copy this template
2. Fill in all required sections
3. Add rule-specific content
4. Validate against base standards
5. Update metadata and version

### Updating Existing Rules
1. Check missing sections
2. Add required content
3. Update formatting
4. Verify dependencies
5. Update changelog

## Examples
### Good Rule File
```markdown
---
description: "Python code formatting standards"
globs:
  - "src/**/*.py"
version: 1.0.0
status: Active
---

# Python Formatting Standards
Version: 1.0.0
Last Updated: 2024-02-02

[Complete sections following template...]
```

### Bad Rule File
```markdown
# Python Rules

Some formatting rules...
Maybe some examples...
// TODO: Add more details
```

## Dependencies
- 02-base.md (Core system standards)

## Changelog
### 1.0.0 (2024-02-02)
- Initial template version
- Added required sections
- Added usage guidelines
- Referenced base standards
