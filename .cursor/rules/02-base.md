---
description: "Base system rules and core functionality requirements"
globs:
  - "**/*"  # Base rules apply to all files
version: 1.0.0
status: Active
---

# Base System Rules
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines the foundational requirements and constraints that apply across the entire system. It establishes core behaviors, standards, and practices that all other rules must follow or extend.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Core Requirements](#core-requirements)
- [System Standards](#system-standards)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)

## Core Requirements
### File Management
- All rules must be in `.cursor/rules/` directory
- Files must follow numeric prefix convention
- File names must be descriptive and use kebab-case
- All rules must use `.md` extension

### Rule Structure
- Must include frontmatter with metadata
- Must have clear section headings
- Must use standard markdown formatting
- Must include all required sections

### Version Control
- All rules must have version numbers
- Changes must be documented in changelog
- Breaking changes must be noted
- Dependencies must be declared

### Documentation Standards
- Clear and concise language
- Consistent terminology
- Examples where appropriate
- Proper markdown formatting
- Complete section coverage

## System Standards
### Naming Conventions
- Files: `nn-descriptive-name.md`
- Sections: Clear hierarchical structure
- References: `@rule(file:section)`
- Variables: Descriptive and consistent

### Format Requirements
- UTF-8 encoding
- Unix line endings (LF)
- No trailing whitespace
- Consistent indentation
- Maximum line length: 120 characters

### Metadata Requirements
- Description field
- Version number
- Status indicator
- Glob patterns
- Last updated date

### Reference Standards
- Internal: `@rule(file:section)`
- External: Full URLs
- Dependencies: Listed in frontmatter
- Cross-references: Use anchors

## Mandatory Constraints
### MUST
- Follow file naming convention
- Include required sections
- Use proper markdown formatting
- Include version information
- Document changes
- Declare dependencies
- Use standard references
- Follow encoding requirements
- Maintain consistent style
- Include examples
- Provide clear documentation
- Follow system standards

### MUST NOT
- Skip required sections
- Use inconsistent formatting
- Leave sections incomplete
- Ignore naming conventions
- Skip version updates
- Omit change documentation
- Use non-standard references
- Mix formatting styles
- Leave examples unclear
- Break file structure

## Advisory Guidelines
### SHOULD
- Keep documentation current
- Use clear examples
- Follow best practices
- Maintain consistency
- Review periodically
- Update dependencies
- Check references
- Validate formatting
- Monitor changes
- Track usage

### RECOMMENDED
- Regular reviews
- Style checking
- Format validation
- Reference verification
- Dependency updates
- Documentation audits
- Usage analysis
- Impact assessment
- Periodic refactoring
- Style guide compliance

## Exception Clauses
Exceptions to these base rules may be granted only when:
- Required by specific tool constraints
- Needed for backward compatibility
- Explicitly approved by system maintainers
- Documented with clear rationale
- Temporary with migration plan

## Examples
```markdown
---
description: "Example rule following base standards"
globs:
  - "src/**/*.py"
version: 1.0.0
status: Active
---

# Example Rule
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
Clear description of rule's purpose...

## Mandatory Constraints
### MUST
- Follow these requirements...

### MUST NOT
- Break these rules...
```

## Migration Notes
- Convert all existing rules to new format
- Update file extensions to .md
- Add missing sections
- Validate against new standards
- Document exceptions

## Dependencies
- None (This is a base rule)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined base standards
- Established core requirements
- Set system standards
