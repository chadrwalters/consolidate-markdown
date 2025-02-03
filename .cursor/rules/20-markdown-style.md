---
description: "Markdown formatting and style standards for documentation"
globs:
  - "docs/**/*.md"
  - "**/*.md"
  - "!node_modules/**/*.md"
  - "!build/**/*.md"
  - "!dist/**/*.md"
  - "!tests/**/*.md"
version: 1.0.0
status: Active
---

# Markdown Style Rules
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines the formatting and style standards for Markdown documentation. It ensures consistent, accessible, and maintainable documentation across the project. For documentation content requirements and processes, see `21-markdown-docs.md`.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Formatting Standards](#formatting-standards)
- [Header Conventions](#header-conventions)
- [Code Blocks](#code-blocks)
- [Diagrams](#diagrams)
- [Accessibility](#accessibility)
- [Links and Tables](#links-and-tables)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)

## Formatting Standards
### General Rules
- Use consistent spacing
- One blank line between sections
- No trailing whitespace
- Use UTF-8 encoding
- Line length ≤ 80 characters

### Paragraphs
- One blank line before and after
- No indentation for paragraphs
- Use soft wrapping
- Consistent line endings
- No double spaces

### Emphasis
- Use * for italics
- Use ** for bold
- Use *** for bold italics
- No underscores for emphasis
- No mixed emphasis styles

### Lists
#### Unordered Lists
- Use - for list items
- Consistent indentation (2 spaces)
- One item per line
- Align wrapped content
- Blank line before and after

#### Ordered Lists
- Use 1. for all items
- Let Markdown handle numbering
- Consistent indentation
- Align wrapped content
- Blank line before and after

## Header Conventions
### Structure
- Use ATX headers (#)
- Space after hash marks
- Title case for headers
- No trailing hashes
- Maximum of 4 levels

### Hierarchy
1. # Title (H1)
2. ## Major Section (H2)
3. ### Subsection (H3)
4. #### Minor Section (H4)

### Spacing
- Two blank lines before H1
- One blank line after H1
- One blank line before H2-H4
- One blank line after H2-H4

## Code Blocks
### Fenced Code
```python
# Use triple backticks (```)
def example():
    return "Hello, World!"
```

### Inline Code
Use `pip install` for package installation

### Code Block Rules
- Specify language
- Indent content consistently
- No trailing whitespace
- Blank line before and after
- Escape backticks if needed

## Diagrams
### Supported Formats
- Mermaid for flowcharts
- PlantUML for UML
- ASCII art for simple diagrams
- SVG for complex graphics
- PNG for screenshots

### Requirements
- Include alt text
- Use consistent styling
- Provide source files
- Document generation steps
- Optimize for readability

## Accessibility
### Images
- Alt text for all images
- Descriptive file names
- Text alternatives for diagrams
- Caption complex images
- No text as images

### Structure
- Logical heading hierarchy
- Descriptive link text
- List for navigation
- Tables with headers
- Clear document structure

## Links and Tables
### Link Formatting
- Use reference style for repeated links
- Descriptive link text
- No bare URLs
- Check link validity
- Use relative paths

### Table Example
| Name   | Type    | Description    |
| ------ | ------- | -------------- |
| id     | integer | Primary key    |
| name   | string  | Resource name  |
| status | enum    | Current status |

## Mandatory Constraints
### MUST
- Follow line length limits
- Use proper heading hierarchy
- Include alt text for images
- Specify code block languages
- Use consistent formatting
- Follow list conventions
- Include table headers
- Check link validity
- Use UTF-8 encoding
- Maintain accessibility
- Document diagrams
- Follow spacing rules

### MUST NOT
- Skip accessibility features
- Use inconsistent formatting
- Leave broken links
- Mix emphasis styles
- Use bare URLs
- Skip alt text
- Exceed heading levels
- Use text as images
- Leave trailing whitespace
- Mix list styles
- Skip table headers
- Use underscores for emphasis

## Advisory Guidelines
### SHOULD
- Use reference links
- Optimize images
- Validate Markdown
- Review accessibility
- Check formatting
- Update documentation
- Verify links
- Clean obsolete content
- Use diagrams effectively
- Follow best practices

### RECOMMENDED
- Regular validation
- Link checking
- Format verification
- Accessibility review
- Content updates
- Style consistency
- Documentation audits
- Image optimization
- Diagram maintenance
- Structure review

## Exception Clauses
Style exceptions allowed when:
- Technical limitations exist
- Tool constraints apply
- Legacy content needs support
- Special formatting required
- Accessibility conflicts occur

## Examples
### Good Example
```markdown
# Document Title

## Introduction
This is a well-formatted paragraph with proper spacing
and line length limits.

### Code Example
```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

### Bad Example
```markdown
#Poorly Formatted Title
This paragraph has no spacing and exceeds the line length limit by continuing far beyond what is recommended for readable documentation.
* Inconsistent list style
_ Wrong emphasis style _
[bad link](http://example.com)bare url http://example.com
```

## Migration Notes
- Update existing documents
- Fix formatting issues
- Add missing alt text
- Correct heading hierarchy
- Validate all links

## Dependencies
- @rule(02-base.md:format_requirements)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined style standards
- Added accessibility rules
- Set formatting requirements
