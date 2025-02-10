# Image Analysis

## Overview

This document describes how consolidate-markdown handles image analysis using GPT-4 Vision and other vision models.

## Supported Models

### Default Model
- `google/gemini-pro-vision-1.0`: Default vision model
  - Pros:
    - Fast response time
    - Lower cost per image
    - Good accuracy
  - Cons:
    - Limited context window
    - Less detail than GPT-4

### Alternative Models
- `gpt-4-vision-preview`: OpenAI's vision model
  - Pros:
    - Highest accuracy
    - Most detailed descriptions
    - Best context understanding
  - Cons:
    - Higher latency
    - More expensive
    - Rate limits

## Configuration

### Global Settings
```toml
[global]
model = "google/gemini-pro-vision-1.0"  # Default model
```

### Per-Source Settings
```toml
[[sources]]
type = "bear"
model = "gpt-4-vision-preview"  # Override for specific source
```

## Implementation Details

### Image Processing Flow
1. Image discovery
   - Find images in source content
   - Validate file types
   - Check cache status

2. Format conversion
   - Convert HEIC to JPEG
   - Resize large images
   - Optimize quality

3. Analysis request
   - Prepare API request
   - Send to vision model
   - Handle response

4. Cache management
   - Store analysis results
   - Track image hashes
   - Handle cache invalidation

### Supported Image Types
- JPEG/JPG
- PNG
- GIF (first frame only)
- HEIC (converted to JPEG)
- SVG (rasterized)
- WebP

### Rate Limiting
- Configurable delays between requests
- Automatic retries on rate limits
- Queue management for large batches

### Error Handling
- Invalid image formats
- API failures
- Timeout handling
- Fallback strategies

## Best Practices

### Image Preparation
1. Optimize image size
   - Keep under 4MB
   - Max dimension 2048px
   - Preserve aspect ratio

2. Format selection
   - Use JPEG for photos
   - Use PNG for screenshots
   - Convert HEIC to JPEG

3. Quality settings
   - JPEG quality 85%
   - PNG compression level 7
   - WebP quality 80%

### Analysis Guidelines
1. Request specific details
   - Content description
   - Text extraction
   - Object detection
   - Scene analysis

2. Handle responses
   - Parse structured data
   - Extract key information
   - Format for markdown

3. Cache management
   - Use content-based hashing
   - Track image modifications
   - Clear cache selectively

## Future Improvements

### Planned Features
1. Additional models
   - Support for local models
   - Custom model integration
   - Model comparison tools

2. Enhanced analysis
   - Object counting
   - Color analysis
   - Style detection
   - Face detection (optional)

3. Performance optimization
   - Parallel processing
   - Batch analysis
   - Smart queuing
   - Resource management
