# Data Format Schemas

This directory contains schema definitions for various data formats used in the consolidate-markdown project.

## Available Schemas

### Export Formats

1. [Bear Export Schema](bear_export.md)
   - Schema for notes exported from Bear.app
   - Includes note structure, attachments, and media handling

2. [ChatGPT Export Schema](chatgpt_export.md)
   - Schema for conversations exported from ChatGPT
   - Includes message structure, metadata, and content types

3. [Claude Export Schema](claude_export.md)
   - Schema for conversations exported from Anthropic's Claude
   - Includes message structure, tools, and special content handling

4. [XBookmarks Export Schema](xbookmarks_export.md)
   - Schema for bookmarks exported from X (Twitter)
   - Includes tweet content, media attachments, and metadata

## Common Elements

All schemas share some common elements in their documentation:

1. **Overview**
   - Description of the data format
   - Basic organization principles

2. **Structure**
   - Directory layout (if applicable)
   - File organization
   - Content format

3. **Media Handling**
   - Supported file types
   - Attachment processing
   - Special content handling

4. **Examples**
   - Sample structures
   - Format demonstrations
   - Common patterns

## Usage

These schemas serve as reference documentation for:
- Understanding the structure of exported data
- Implementing data processors
- Debugging format issues
- Extending functionality to new formats
