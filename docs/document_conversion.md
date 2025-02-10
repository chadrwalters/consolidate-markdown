# Document Conversion

This document explains how consolidate-markdown handles various document formats when converting them to markdown.

## Supported Formats

### Images
- Formats: JPG, PNG, HEIC, SVG
- Processing: Uses GPT-4 Vision for image analysis and description
- Output: Markdown with embedded image and description

### Text Files
- Formats: TXT, CSV, JSON
- Processing: Direct conversion with format-specific handling
- Output: Plain text or structured markdown (e.g., tables for CSV)

### PDFs
- Processing: Custom handler using pdfminer-six
- Features:
  - Text extraction from embedded text
  - Basic formatting preservation
  - Support for most standard PDFs
- Limitations:
  - No OCR for scanned documents
  - Limited table structure preservation
  - No support for complex layouts
  - No automatic handling of columns

### Microsoft Office Documents
- Processing: Uses Microsoft's MarkItDown library
- Formats: DOCX, XLSX, PPTX
- Features:
  - Basic text and structure preservation
  - Table conversion
  - List formatting

## Implementation Details

### PDF Processing
We initially used Microsoft's MarkItDown library for PDF conversion but encountered limitations with text extraction. To provide more reliable PDF support, we now use a custom handler based on pdfminer-six that:

1. Extracts text content from PDFs
2. Cleans up whitespace and formatting
3. Handles basic document structure

For best results with PDFs:
- Use PDFs with embedded text rather than scanned documents
- Pre-process scanned PDFs with OCR software
- Keep layouts simple and avoid complex formatting
- Consider breaking multi-column documents into single columns

### Future Improvements
We are actively monitoring improvements in both MarkItDown and other document conversion libraries. Future versions may include:
- OCR integration for scanned PDFs
- Better table structure preservation
- Improved handling of complex layouts
- Column detection and reflow
