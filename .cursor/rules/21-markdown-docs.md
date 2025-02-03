---
description: "Markdown documentation requirements and processes"
globs:
  - "docs/**/*.md"
  - "*.md"
  - "!tests/**/*.md"
  - "!temp/**/*.md"
version: 1.0.0
status: Active
---

# Markdown Documentation Rules
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines the documentation requirements, processes, and standards for Markdown documentation. It ensures comprehensive, maintainable, and user-friendly documentation across the project. For Markdown formatting and style standards, see `20-markdown-style.md`.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Documentation Requirements](#documentation-requirements)
- [Documentation Workflow](#documentation-workflow)
- [Example Standards](#example-standards)
- [API Documentation](#api-documentation)
- [Generation and Search](#generation-and-search)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)

## Documentation Requirements
### Essential Documents
- README.md: Project overview
- CONTRIBUTING.md: Contribution guide
- CHANGELOG.md: Version history
- LICENSE: Project license
- docs/: Detailed documentation

### Content Standards
- Clear and concise writing
- Consistent terminology
- Complete examples
- Proper attribution
- Regular updates

### Organization
- Logical structure
- Clear navigation
- Consistent formatting
- Proper categorization
- Easy maintenance

## Documentation Workflow
### Update Triggers
- Code changes
- Feature additions
- Bug fixes
- Process changes
- External updates

### Development Process
1. Review affected docs
2. Update content
3. Verify changes
4. Update references
5. Version control

### Review Process
#### Technical Review
- Accuracy check
- Code validation
- API correctness
- Security review
- Performance impact

#### Editorial Review
- Grammar check
- Style compliance
- Clarity review
- Consistency check
- Format validation

## Example Standards
### Code Examples
```python
# Good Example
def calculate_total(items: List[Item]) -> float:
    """Calculate total price of items.

    Args:
        items: List of items to total

    Returns:
        Total price of all items
    """
    return sum(item.price for item in items)

# Bad Example
def calc(x):  # Missing type hints and documentation
    return sum(x)
```

### Tutorial Format
```markdown
# Feature Tutorial

## Prerequisites
- Python 3.8+
- Required packages
- API access

## Steps
1. Install dependencies
2. Configure settings
3. Initialize client
4. Make API calls
5. Handle responses

## Troubleshooting
- Common errors
- Solutions
- Support contacts
```

### API Documentation
```markdown
## User API

### Create User
POST /api/users

Request:
```json
{
    "name": "John Doe",
    "email": "john@example.com"
}
```

Response:
```json
{
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com"
}
```
```

## Generation and Search
### Documentation Tools
- MkDocs for sites
- Sphinx for Python
- JSDoc for JavaScript
- Swagger for APIs
- Doxygen for C++

### Search Optimization
- Clear titles
- Descriptive headings
- Relevant keywords
- Proper tagging
- Good descriptions

## Mandatory Constraints
### MUST
- Include essential documents
- Follow content standards
- Use proper organization
- Complete review process
- Include code examples
- Document APIs fully
- Maintain versions
- Update on changes
- Follow style guide
- Include search metadata
- Test all examples
- Verify accuracy

### MUST NOT
- Skip documentation
- Leave examples untested
- Ignore reviews
- Mix documentation styles
- Skip version updates
- Leave broken links
- Omit prerequisites
- Use unclear language
- Skip API endpoints
- Leave TODOs
- Mix formatting
- Ignore feedback

## Advisory Guidelines
### SHOULD
- Use active voice
- Keep docs current
- Add diagrams
- Include examples
- Review regularly
- Update references
- Check accuracy
- Monitor feedback
- Improve clarity
- Follow patterns

### RECOMMENDED
- Regular audits
- Style checking
- Link validation
- Example testing
- Version tracking
- Search optimization
- User testing
- Performance review
- Security review
- Accessibility check

## Exception Clauses
Documentation exceptions allowed when:
- Technical limitations exist
- Tool constraints apply
- Legacy systems involved
- Security restrictions
- Emergency updates needed

## Examples
### Good Documentation
```markdown
# User Authentication

## Overview
This guide explains how to implement user authentication
using our secure API endpoints.

## Prerequisites
- API key
- Account credentials
- HTTPS enabled

## Implementation
1. Initialize client
2. Configure credentials
3. Make auth request
4. Handle token response
5. Use token in requests
```

### Bad Documentation
```markdown
Authentication
Do this:
1. get key
2. use it
note: might need https
```

## Migration Notes
- Update all documentation
- Add missing sections
- Implement new format
- Review examples
- Verify accuracy

## Dependencies
- @rule(02-base.md:format_requirements)
- @rule(20-markdown-style.md:formatting_standards)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined documentation standards
- Added workflow requirements
- Set example formats
