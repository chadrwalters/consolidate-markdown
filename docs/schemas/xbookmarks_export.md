# XBookmarks Export Schema

This document describes the schema for bookmarks exported from X (formerly Twitter) through the browser extension.

## Overview

XBookmarks exports are organized as a directory structure containing individual bookmark directories, each representing a saved tweet or thread. Each bookmark directory contains an index file and associated media/attachments.

## Directory Structure

```
_XBookmarks/
├── images/                     # Global images directory
├── index.md                    # Global index file
└── {timestamp_id}/            # Individual bookmark directories
    ├── index.md               # Bookmark content and metadata
    ├── images/                # Bookmark-specific images
    └── media/                 # Other media attachments
```

## Bookmark Directory Structure

Each bookmark directory follows this naming pattern:
- Format: `YYYY_MM_DD_TWEETID`
- Example: `2024_08_05_1820577518979604929`

### Components:
- `YYYY_MM_DD`: Future date when the bookmark will be processed
- `TWEETID`: Unique identifier of the tweet

## Index File Structure

The `index.md` file in each bookmark directory contains:

1. **Header**
   - Tweet author link: `**[Username](https://x.com/username)**`
   - Optional description or thread context

2. **Content**
   - Main tweet text
   - Thread content (if applicable)

3. **Attachments Section**
   - Images subsection
     - List of image files with descriptions
   - Documents subsection
     - List of document files with descriptions
   - Code & Config subsection
     - List of code or configuration files

4. **Metadata**
   - Hashtags
   - Engagement metrics (retweets, likes)

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

## Processing Behavior

1. **Cache Management**
   - Content hashing for change detection
   - Timestamp-based cache invalidation

2. **Output Format**
   - Single markdown file per bookmark
   - Embedded media references
   - Preserved metadata and structure

## Example Structure

```markdown
**[SampleUser](https://x.com/sampleuser)**

A sample tweet demonstrating various content types and attachments.

Here's a thread about open source software and development practices. 🧵

## Attachments

### Images
- Beautiful landscape photo (sample.jpg)
- Sunset at the beach (sample.heic)

### Documents
- Project Overview (sample.docx)
- Data Analysis (sample.xlsx)
- Survey Results (sample.csv)

### Code & Config
- Environment Setup (sample.txt)
- API Schema (sample.json)

#OpenSource #Development #Testing

🔁 42 ❤️ 128
```
