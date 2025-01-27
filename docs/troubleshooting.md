# Troubleshooting Guide

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
