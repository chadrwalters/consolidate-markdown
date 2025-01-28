# Test Fixtures

This directory contains sanitized test fixtures for various test scenarios.

## Directory Structure
```
tests/fixtures/
├── attachments/
│   ├── images/
│   │   ├── sample.heic (Lightning image from libheif test suite)
│   │   └── sample.jpg  (Generated test image)
│   ├── documents/
│   │   ├── sample.docx (Project proposal template)
│   │   ├── sample.csv  (Product inventory data)
│   │   └── sample.xlsx (Monthly financial report)
│   └── text/
│       ├── sample.txt  (Configuration file)
│       └── sample.json (API documentation)
├── bear/
│   ├── basic_note.md   (Pure markdown formatting)
│   ├── format_test.md  (Mixed attachments demo)
│   └── format_test/    (Attachment directory)
└── xbookmarks/
    └── sample_bookmark/
        ├── index.md    (Sample tweet with attachments)
        └── media/      (Linked attachments)
```

## Test Cases

### Basic Note Test
- Text formatting (bold, italic)
- Lists (ordered, unordered)
- Code blocks
- Links
- Tags

### Format Test
- Image attachments (JPG, HEIC)
- Document attachments (DOCX, CSV, XLSX)
- Text file attachments (TXT, JSON)
- Mixed content with captions
- Special characters in filenames

### X Bookmark Test
- Tweet content with thread
- Multiple attachment types
- Hashtags and engagement metrics
- User profile links

## Sample Files

### Images
- `sample.jpg`: Generated test image
- `sample.heic`: Lightning photo from libheif test suite

### Documents
- `sample.docx`: Generic project proposal with sections
- `sample.csv`: Product inventory with 10 items
- `sample.xlsx`: Monthly financial data

### Text Files
- `sample.txt`: Configuration file with settings
- `sample.json`: API documentation with endpoints

## Test Plan

### 1. Basic Functionality Tests
- Verify markdown parsing and rendering
- Test basic text formatting (bold, italic, lists)
- Validate code block syntax highlighting
- Check link handling and tag processing

### 2. Attachment Integration Tests
- Test image file handling (JPG, HEIC)
- Verify document processing (DOCX, CSV, XLSX)
- Validate text file imports (TXT, JSON)
- Check mixed content with multiple attachments
- Test special character handling in filenames

### 3. X Bookmarks Migration Tests
- Validate tweet content preservation
- Test media file attachments
- Verify metadata (hashtags, metrics)
- Check user profile link handling

### 4. Edge Cases
- Test large files and multiple attachments
- Verify handling of special characters
- Test missing or invalid attachments
- Check empty or malformed content

### 5. Performance Tests
- Measure processing time for different file types
- Test memory usage with large attachments
- Verify concurrent processing capabilities

### 6. Integration Tests
- Test end-to-end workflow
- Verify file organization structure
- Validate cross-references between notes
- Check attachment path resolution
