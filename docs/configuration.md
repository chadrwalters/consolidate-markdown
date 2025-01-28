# Configuration Guide

This document describes how to configure the consolidate-markdown tool.

## Configuration File Format
The tool uses TOML format for configuration. Create a file named `config.toml`:

```toml
[global]
cm_dir = ".cm"                      # Working directory
log_level = "INFO"                  # Logging level (DEBUG, INFO, WARNING, ERROR)
force_generation = false            # Force regeneration of all files
no_image = false                    # Skip GPT image analysis
openai_key = "<YOUR_KEY_HERE>"      # OpenAI API key

[[sources]]
type = "bear"                       # Source type: "bear" or "xbookmarks"
srcDir = "/path/to/bear/notes"      # Source directory
destDir = "/path/to/output/bear"    # Output directory

[[sources]]
type = "xbookmarks"
srcDir = "/path/to/x/bookmarks"
destDir = "/path/to/output/x"
```

## Command Line Options

```bash
consolidate-markdown --config config.toml [options]

Options:
  --config PATH     Path to configuration file (default: config.toml)
  --no-image       Skip image analysis
  --force          Force regeneration of all files
  --delete         Delete existing output files before processing
  --log-level      Set logging level (DEBUG, INFO, WARNING, ERROR)
  --debug          Enable debug logging (same as --log-level DEBUG)
```

## Processing Summary
The tool provides detailed statistics for each source and overall:
```
Summary for Bear Source:
  - X notes processed (markdown files)
  - Y images skipped (when using --no-image)
  - Z documents processed (non-image attachments)

Summary for Xbookmarks Source:
  - A notes processed (bookmark entries)
  - B images skipped (when using --no-image)
  - C documents processed (non-image attachments)

Overall:
  - Total notes processed
  - Total images skipped
  - Total documents processed
  - Any errors encountered
```

## Environment Variables
- `OPENAI_API_KEY`: OpenAI API key (overrides config file)
- `CM_LOG_LEVEL`: Override logging level
- `CM_NO_IMAGE`: Set to "1" to disable image analysis

## Directory Structure
- `.cm/`: Working directory for temporary files
  - `logs/`: Log files
  - `markitdown/`: Document conversion workspace
  - `images/`: Image processing workspace
- Output directories: Specified in config for each source

## File Type Support
- Images: jpg, jpeg, png, svg, heic
- Documents: docx, pdf, csv, xlsx
- Text: md, txt

## Example Configurations

### Basic Setup
```toml
[global]
cm_dir = ".cm"
log_level = "INFO"
no_image = true

[[sources]]
type = "bear"
srcDir = "~/Documents/Bear Notes"
destDir = "./output/bear"
```

### Multiple Sources
```toml
[global]
cm_dir = ".cm"
log_level = "INFO"
openai_key = "sk-..."

[[sources]]
type = "bear"
srcDir = "/notes/bear"
destDir = "/output/bear"

[[sources]]
type = "xbookmarks"
srcDir = "/bookmarks/x"
destDir = "/output/x"
```

### Production Setup
```toml
[global]
cm_dir = "/var/lib/cm"
log_level = "WARNING"
force_generation = false
no_image = false
openai_key = "${OPENAI_API_KEY}"

[[sources]]
type = "bear"
srcDir = "/data/bear"
destDir = "/www/notes"
```

## System Requirements

### Required Programs
The following third-party programs must be installed and available in your system PATH:

#### Image Processing
- **HEIC Conversion**
  - macOS: `sips` (built-in)
  - Linux/Windows: Install an alternative HEIC converter
- **SVG Conversion** (at least one of):
  - `inkscape` (preferred, supports more SVG features)
  - `rsvg-convert` (faster, but more basic)

#### Document Processing
- **pandoc**: Required for converting various document formats to markdown
  - Supports: docx, pdf, csv, xlsx
  - Must be in system PATH

### Verifying Installation
You can verify the required programs are installed and accessible:

```bash
# Check pandoc
pandoc --version

# Check inkscape
inkscape --version  # or
rsvg-convert --version

# Check sips (macOS only)
sips --version
```

### Program-Specific Configuration
Some programs may require additional configuration:

#### Inkscape
- Default SVG to PNG conversion settings can be adjusted in Inkscape preferences
- Command-line options can be modified in config.toml:
```toml
[global]
inkscape_options = "--export-type=png --export-dpi=300"
```

#### Pandoc
- Default conversion options can be customized:
```toml
[global]
pandoc_options = "--wrap=none --reference-links"
```
