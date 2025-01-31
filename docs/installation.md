# Installation Guide

## System Requirements

### Python Environment
- Python 3.12 or higher
- uv package manager

### Required System Tools
- `pandoc` for document conversion
- `librsvg` (provides `rsvg-convert`) for SVG conversion
- HEIC conversion tool (one of the following):
  - ImageMagick (recommended, works on all platforms)
  - `sips` (built-in on macOS)
  - `libheif-tools` (Linux alternative)

## Platform-Specific Installation

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install pandoc
brew install librsvg
brew install imagemagick  # optional, sips is built-in

# Verify installations
pandoc --version
rsvg-convert --version
convert --version  # for ImageMagick
```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt-get update

# Install required tools
sudo apt-get install pandoc
sudo apt-get install librsvg2-bin

# Install HEIC conversion tool (choose one):
sudo apt-get install imagemagick  # recommended
# or
sudo apt-get install libheif-tools

# Verify installations
pandoc --version
rsvg-convert --version
convert --version  # if using ImageMagick
heif-convert --version  # if using libheif-tools
```

### Windows

1. Install [Python 3.12](https://www.python.org/downloads/) or higher
2. Install [Pandoc](https://pandoc.org/installing.html)
3. Install [librsvg](https://wiki.gnome.org/Projects/LibRsvg)
4. Install [ImageMagick](https://imagemagick.org/script/download.php#windows)
5. Add all installed programs to your system PATH

Verify installations in PowerShell:
```powershell
python --version
pandoc --version
rsvg-convert --version
magick --version
```

## Python Package Installation

```bash
# Install with uv
uv pip install .

# Install development dependencies (optional)
uv pip install -e ".[dev]"
```

## Configuration

1. Copy the template configuration:
   ```bash
   cp config.template.toml config.toml
   ```

2. Edit `config.toml` with your settings:
   ```toml
   [global]
   cm_dir = ".cm"  # Cache directory
   no_image = false  # Set to true to skip image analysis
   openai_key = ""  # Optional: for GPT-4V image analysis

   [[sources]]
   type = "claude"  # Processor type for Claude exports
   src_dir = "path/to/claude/exports"  # Directory containing conversations.json
   dest_dir = "output/claude"  # Output directory for markdown files
   ```

## Claude-Specific Setup

### Export Location
The Claude processor expects the following files in your source directory:
- `conversations.json`: Contains all conversation data
- `users.json`: Contains user metadata (optional)

### Attachments
If your conversations include attachments:
1. Create an `attachments` directory in your source directory
2. Place all attachment files there
3. Ensure file names match the references in conversations.json

### Output Structure
The processor will generate:
- Markdown files for each conversation
- An index file grouping conversations by date
- An artifacts directory for extracted code and content
- Processed attachments in the output directory

## Verification

Run the test suite to verify your installation:
```bash
uv run pytest
```

All tests should pass. If you encounter any issues, check the [Troubleshooting Guide](troubleshooting.md).

## Next Steps

1. Read the [Configuration Guide](configuration.md) for detailed settings
2. Check the [Examples](examples.md) for common usage patterns
3. Review the [Troubleshooting Guide](troubleshooting.md) if needed
