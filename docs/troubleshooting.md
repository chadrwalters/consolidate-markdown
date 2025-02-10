# Troubleshooting Guide

This document provides solutions for common issues you may encounter when using consolidate-markdown.

## Command Line Issues

### Invalid Processor Type

**Problem**: Error when using `--processor` with an invalid type.

**Solution**:
1. Use one of the supported processor types:
   - `bear`
   - `xbookmarks`
   - `chatgptexport`
2. Check for typos in the processor name
3. Verify the processor type is configured in your config.toml

Example:
```bash
# Correct usage
consolidate-markdown --config config.toml --processor bear

# Incorrect usage (will error)
consolidate-markdown --config config.toml --processor bears
```

### Item Limit Issues

**Problem**: `--limit` option not working as expected.

**Solutions**:
1. Verify the limit is a positive integer
2. Check if source directories contain the expected number of items
3. Ensure items have valid modification times for sorting
4. Use debug logging to see which items are being selected:
   ```bash
   consolidate-markdown --config config.toml --limit 5 --debug
   ```

## Configuration Issues

### Source Directory Not Found

**Problem**: Source directory specified in config.toml cannot be found.

**Solutions**:
1. Verify the directory path is correct
2. Check if the directory exists
3. Ensure you have read permissions
4. Use absolute paths or paths relative to home (~)

Example config:
```toml
[[sources]]
type = "bear"
src_dir = "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files"
dest_dir = "output/bear"
```

### Multiple Sources of Same Type

**Problem**: Issues when configuring multiple sources of the same type.

**Solutions**:
1. Use unique destination directories for each source
2. Verify each source directory exists
3. Check permissions for all directories
4. Use debug logging to track processing:
   ```bash
   consolidate-markdown --config config.toml --debug
   ```

Example config:
```toml
[[sources]]
type = "bear"
src_dir = "~/work/notes"
dest_dir = "output/work"

[[sources]]
type = "bear"
src_dir = "~/personal/notes"
dest_dir = "output/personal"
```

## Processing Issues

### PDF Processing

**Problem**: PDF attachments not converting correctly or returning empty text.

**Solutions**:
1. Verify the PDF contains actual text content (not just scanned images)
2. Check if the PDF is password-protected or encrypted
3. For scanned PDFs, consider using OCR software first
4. Use debug logging to see processing details:
   ```bash
   consolidate-markdown --config config.toml --debug
   ```

**Note**: While we use Microsoft's MarkItDown library for general document conversion, we've implemented a custom PDF handler using pdfminer-six due to limitations in MarkItDown's PDF support. This provides more reliable text extraction but has the following limitations:
- No support for scanned PDFs without OCR
- No automatic table structure preservation
- Limited formatting preservation

For best results with PDFs:
- Use PDFs with embedded text (not scanned)
- Keep formatting simple
- Avoid complex layouts with multiple columns
- For scanned PDFs, pre-process with OCR software

### No Items Processed

**Problem**: Tool runs but no items are processed.

**Solutions**:
1. Check source directory contains files
2. Verify file permissions
3. Ensure processor type matches source content
4. Try processing specific source:
   ```bash
   consolidate-markdown --config config.toml --processor bear --debug
   ```

### Partial Processing

**Problem**: Only some items are processed.

**Solutions**:
1. Check if `--limit` option is set
2. Verify file permissions for all items
3. Look for error messages in debug log
4. Try forcing regeneration:
   ```bash
   consolidate-markdown --config config.toml --force
   ```

### Cache Issues

**Problem**: Changes not reflected in output.

**Solutions**:
1. Force regeneration:
   ```bash
   consolidate-markdown --config config.toml --force
   ```
2. Delete cache and output:
   ```bash
   consolidate-markdown --config config.toml --delete
   ```
3. Check cache directory permissions
4. Verify sufficient disk space

## Processor-Specific Issues

### Bear Notes

**Problem**: Bear notes not processing.

**Solutions**:
1. Verify Bear notes directory path
2. Check file permissions
3. Ensure notes are in expected format
4. Try processing with debug:
   ```bash
   consolidate-markdown --config config.toml --processor bear --debug
   ```

### X Bookmarks

**Problem**: X bookmarks not processing.

**Solutions**:
1. Check bookmarks file exists
2. Verify file format is correct
3. Ensure read permissions
4. Try processing with debug:
   ```bash
   consolidate-markdown --config config.toml --processor xbookmarks --debug
   ```

### ChatGPT Export

**Problem**: ChatGPT exports not processing.

**Solutions**:
1. Verify export directory contains conversations.json
2. Check file format is valid
3. Ensure read permissions
4. Try processing with debug:
   ```bash
   consolidate-markdown --config config.toml --processor chatgptexport --debug
   ```

## Common Error Messages

### "Invalid processor type"

**Cause**: Specified processor type is not supported.
**Solution**: Use one of: bear, xbookmarks, chatgptexport

### "Source directory not found"

**Cause**: Source directory does not exist or is inaccessible.
**Solution**: Verify path and permissions

### "No items found to process"

**Cause**: Source directory empty or items not recognized.
**Solution**: Check source directory contents and processor type

### "Cache directory not writable"

**Cause**: Insufficient permissions for cache directory.
**Solution**: Check .cm directory permissions

## Debugging Tips

1. Enable debug logging:
   ```bash
   consolidate-markdown --config config.toml --debug
   ```

2. Process specific source:
   ```bash
   consolidate-markdown --config config.toml --processor TYPE
   ```

3. Limit items for testing:
   ```bash
   consolidate-markdown --config config.toml --limit 1
   ```

4. Force regeneration:
   ```bash
   consolidate-markdown --config config.toml --force
   ```

5. Check log files in .cm/logs/

## Getting Help

If you continue to experience issues:

1. Enable debug logging
2. Check all log files
3. Verify configuration
4. Test with minimal configuration
5. Report issues with:
   - Debug logs
   - Configuration file
   - Error messages
   - Steps to reproduce

## Common Issues

### Installation Problems
```
Problem: ImportError: No module named 'consolidate_markdown'
Solution: Ensure you've installed the package with 'uv pip install -e .'
```

```
Problem: Missing dependencies
Solution: Run 'uv pip install -e ".[dev]"' for development dependencies
```

### Configuration Issues
```
Problem: "Invalid configuration" error
Solution: Check config.toml format and paths
```

```
Problem: "Unknown source type" error
Solution: Verify source type is "bear" or "xbookmarks"
```

### Processing Errors

#### Bear Notes
```
Problem: Missing attachments
Solution: Ensure Bear note folders contain referenced files
```

```
Problem: Invalid markdown links
Solution: Check Bear note export format
```

#### X Bookmarks
```
Problem: Missing index.md
Solution: Verify bookmark directory structure
```

```
Problem: Media file errors
Solution: Check media file permissions and formats
```

### Document Conversion

#### DOCX Files
```
Problem: "Pandoc not found" error
Solution: Install pandoc using package manager
```

```
Problem: Conversion fails
Solution: Check file permissions and format
```

#### Image Processing

##### HEIC Conversion
```
Problem: HEIC conversion fails on macOS
Solution: sips is built-in, ensure file permissions are correct
```

```
Problem: HEIC conversion fails on Linux
Solution: Install libheif-tools:
  Ubuntu/Debian: sudo apt install libheif-tools
  Fedora: sudo dnf install libheif-tools
  Arch: sudo pacman -S libheif
```

```
Problem: HEIC conversion fails on Windows
Solution: Install ImageMagick:
  choco install imagemagick
  Verify HEIC support is included in installation
```

##### SVG Conversion
```
Problem: "Inkscape not found" error
Solution: Install Inkscape:
  macOS: brew install inkscape
  Linux: sudo apt install inkscape (or equivalent)
  Windows: choco install inkscape
```

```
Problem: SVG conversion fails with permissions
Solution: Ensure Inkscape has execute permissions and is in PATH
```

```
Problem: SVG conversion is slow
Solution: Use --sequential flag for large batches of SVGs
```

### API Integration
```
Problem: OpenAI API errors
Solution: Verify API key and network connection
```

```
Problem: Rate limiting
Solution: Implement backoff or use --no-image
```

### Third-Party Program Problems

#### HEIC Conversion Failures
- **macOS**: Ensure `sips` is available (built into macOS)
  ```bash
  sips --version
  ```
- **Linux/Windows**: Install and configure an alternative HEIC converter

#### SVG Conversion Issues
1. **Inkscape Not Found**
   ```
   FileNotFoundError: [Errno 2] No such file or directory: 'inkscape'
   ```
   - Verify Inkscape is installed: `inkscape --version`
   - Check if it's in your PATH
   - Try installing rsvg-convert as alternative

2. **SVG Conversion Failed**
   ```
   Error processing attachment: SVG conversion failed
   ```
   - Check SVG file is valid: `inkscape --verify file.svg`
   - Try with rsvg-convert if Inkscape fails
   - Check for unsupported SVG features

#### Document Conversion Problems
1. **Pandoc Missing**
   ```
   FileNotFoundError: [Errno 2] No such file or directory: 'pandoc'
   ```
   - Install pandoc: `brew install pandoc` or `apt-get install pandoc`
   - Verify installation: `pandoc --version`

2. **Conversion Failed**
   ```
   Error: pandoc document conversion failed
   ```
   - Check input file is valid
   - Try converting manually with pandoc
   - Check pandoc has required format support

### Installation Verification
Run this script to verify all required programs:

```bash
#!/bin/bash
echo "Checking required programs..."

# Check pandoc
if command -v pandoc >/dev/null; then
    echo "✅ pandoc found: $(pandoc --version | head -n1)"
else
    echo "❌ pandoc not found"
fi

# Check SVG converters
if command -v inkscape >/dev/null; then
    echo "✅ inkscape found: $(inkscape --version | head -n1)"
else
    if command -v rsvg-convert >/dev/null; then
        echo "✅ rsvg-convert found: $(rsvg-convert --version | head -n1)"
    else
        echo "❌ No SVG converter found (need inkscape or rsvg-convert)"
    fi
fi

# Check HEIC converter
if [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v sips >/dev/null; then
        echo "✅ sips found (macOS)"
    else
        echo "❌ sips not found (required on macOS)"
    fi
else
    echo "ℹ️ Non-macOS system, ensure HEIC converter is installed"
fi
```

## Performance Issues

### Memory Usage
```

```

### ChatGPT Export Processing

#### Export Format
```
Problem: "conversations.json not found" error
Solution: Ensure you're pointing to the correct export directory containing conversations.json
```

```
Problem: Invalid conversations data format
Solution: Verify the export is from a supported ChatGPT version and contains valid JSON
```

#### Image Analysis
```
Problem: "OpenAI API error" during image processing
Solution:
- Check OpenAI API key is valid
- Verify you have access to GPT-4 Vision API
- Consider using --no-image flag to skip analysis
```

```
Problem: Image analysis is slow
Solution:
- Enable caching (default)
- Use --no-image for initial testing
- Process in smaller batches
```

#### Output Format
```
Problem: Missing conversation dates
Solution: Dates default to "00000000" if create_time is not in export
```

```
Problem: Embedded attachments not displaying
Solution:
- Check file permissions
- Verify attachment paths in conversations.json
- Ensure attachments were included in export
```

```

## Model-Specific Issues

### Model Selection and Configuration

1. **Invalid Model Error**
   - **Problem**: Error about invalid model selection
   - **Solution**:
     * Verify model name matches exactly (including provider prefix)
     * Check if model is supported by your API provider
     * Ensure proper configuration in TOML file
   - **Example Fix**:
     ```toml
     [models]
     default_model = "gpt-4o"  # Correct
     # NOT: default_model = "gpt4" or "gpt-4"
     ```

2. **Model Not Available**
   - **Problem**: Selected model is not accessible
   - **Solution**:
     * Verify API provider configuration
     * Check if model is still supported
     * Try alternate model from same provider
   - **Example Fix**:
     ```toml
     [models]
     default_model = "google/gemini-pro-vision-1.0"
     alternate_model_backup = "gpt-4o"  # Fallback option
     ```

### Performance Issues

1. **Slow Response Times**
   - **Problem**: Model responses are taking too long
   - **Solution**:
     * Switch to faster models (Yi Vision or BLIP)
     * Enable caching for repeated analyses
     * Check network connectivity
     * Verify image size and format
   - **Example Fix**:
     ```toml
     [models]
     default_model = "yi/yi-vision-01"  # Faster model
     ```

2. **Poor Analysis Quality**
   - **Problem**: Model responses lack detail or accuracy
   - **Solution**:
     * Use more capable models (GPT-4 Vision or Gemini Pro)
     * Verify image quality
     * Check if task matches model strengths
   - **Example Fix**:
     ```toml
     [models]
     default_model = "gpt-4o"  # More capable model
     ```

### Technical Content Analysis

1. **Code Recognition Issues**
   - **Problem**: Poor code analysis or syntax recognition
   - **Solution**:
     * Use Gemini Pro Vision for code analysis
     * Ensure code is clearly visible in image
     * Consider image preprocessing
   - **Example Fix**:
     ```toml
     [models]
     default_model = "google/gemini-pro-vision-1.0"  # Best for code
     ```

2. **UI Element Detection Problems**
   - **Problem**: Missing or incorrect UI element identification
   - **Solution**:
     * Use GPT-4 Vision or Gemini Pro for UI analysis
     * Ensure clear screenshots
     * Consider window/element contrast
   - **Example Fix**:
     ```toml
     [models]
     default_model = "gpt-4o"  # Best for UI details
     ```

### Caching and Performance

1. **Cache Misses**
   - **Problem**: Repeated analyses not using cache
   - **Solution**:
     * Verify cache directory permissions
     * Check cache key generation
     * Ensure consistent image paths
   - **Example Fix**:
     ```bash
     # Clear cache and retry
     rm -rf .cm/cache/*
     ```

2. **Resource Usage**
   - **Problem**: High resource usage during analysis
   - **Solution**:
     * Use more efficient models for bulk processing
     * Enable caching
     * Consider batch processing
   - **Example Fix**:
     ```toml
     [models]
     default_model = "deepinfra/blip"  # More efficient
     ```

### Common Error Messages

1. **"Model not supported by provider"**
   ```
   Error: Model 'custom_model' is not supported by provider 'openrouter'
   ```
   - **Solution**: Use only supported models from VALID_MODELS list

2. **"Invalid model alias"**
   ```
   Error: Invalid model alias: unknown_model
   ```
   - **Solution**: Check model alias configuration in TOML file

3. **"API returned no content"**
   ```
   Error: OpenRouter API returned no content for model google/gemini-pro-vision-1.0
   ```
   - **Solution**:
     * Verify API key and permissions
     * Check model availability
     * Try alternate model

### Best Practices

1. **Model Selection**
   - Start with GPT-4 Vision for unknown use cases
   - Use Gemini Pro Vision for technical content
   - Consider Yi Vision for batch processing
   - Always configure a backup model

2. **Configuration**
   - Use environment variables for flexibility
   - Keep model aliases descriptive
   - Document model choices in configuration
   - Test alternate models for your use case

3. **Performance**
   - Enable caching for repeated analyses
   - Use appropriate models for batch processing
   - Monitor and log model performance
   - Consider cost vs. performance tradeoffs
