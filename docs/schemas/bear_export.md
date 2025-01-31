# Bear Export Schema

This document describes the schema for notes exported from Bear.app, including their structure and attachment handling.

## Overview

Bear exports are organized as a flat directory structure containing markdown files and corresponding attachment directories. Each note is represented by a `.md` file, with an optional directory of the same name (minus extension) containing its attachments.

## Directory Structure

```
_BearNotes/
├── Note Title.md              # Main note file
├── Note Title/               # Attachment directory (optional)
│   ├── image1.jpg           # Image attachments
│   ├── document.pdf         # Document attachments
│   └── config.txt           # Text attachments
├── Another Note.md
└── Another Note/            # Another note's attachments
```

## Note File Structure

Each `.md` file follows standard Markdown format with Bear-specific enhancements:

1. **Title**
   - First-level heading (`# Title`)
   - Used as the note's display name

2. **Content**
   - Standard Markdown formatting
     - Bold (`**text**`)
     - Italic (`*text*`)
     - Lists (ordered and unordered)
     - Code blocks
     - Links
   - Bear-specific formatting
     - Tags (`#tag`)
     - Task lists
     - Internal note links

3. **Attachments**
   - Image references: `![Caption](Note Title/image.jpg)`
   - Document embeddings: `[Document](Note Title/doc.pdf)<!-- {"embed":"true"} -->`
   - Support for relative paths with spaces and special characters

## Media Handling

### Supported Image Types
- `.jpg`
- `.jpeg`
- `.png`
- `.gif`
- `.svg`
- `.heic`

### Supported Document Types
- Any non-image file type
- Common types:
  - `.docx`
  - `.xlsx`
  - `.pdf`
  - `.txt`
  - `.json`
  - `.csv`
  - `.html`

## Processing Behavior

1. **Cache Management**
   - Content hashing for change detection
   - Timestamp-based cache invalidation
   - Separate tracking for documents and images

2. **Output Format**
   - Single markdown file per note
   - Embedded media references
   - Preserved metadata and structure

## Example Structure

```markdown
# Sample Note

This is a sample Bear note for testing basic functionality.

## Text Formatting
Regular text with **bold** and *italic* formatting.

## Lists
1. First item
2. Second item
   - Sub-item A
   - Sub-item B

## Code Block
```python
def greet(name):
    return f"Hello, {name}!"
```

## Attachments
![Sample Photo](Note Title/sample.jpg)
*A beautiful landscape photo*

[Project Proposal](Note Title/sample.docx)<!-- {"embed":"true"} -->
*Overview of the project goals and timeline*

## Tags
#testing #sample #markdown
```
