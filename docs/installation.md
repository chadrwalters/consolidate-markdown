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
   cp example_config.toml consolidate_config.toml
   ```

2. Edit `consolidate_config.toml` with your settings:
   - Set input/output directories
   - Configure GPT API key if using image analysis
   - Adjust processing options

## Verification

Run the test suite to verify your installation:
```bash
uv run pytest
```

All tests should pass. If you encounter any issues, check the [Troubleshooting Guide](troubleshooting.md).
