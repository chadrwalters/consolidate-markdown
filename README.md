# Consolidate Markdown (v1.0.0)

Convert and consolidate Markdown files from multiple sources with AI-powered image analysis.

## Features
- Process Bear.app notes and X Bookmarks
- AI-powered image descriptions using GPT-4o
- Document conversion to Markdown (docx, pdf, csv, xlsx)
- Image format conversion (heic, svg, jpg, png)
- Configurable processing pipeline
- Parallel processing with --sequential option
- Atomic file operations and backup system
- Smart caching system for files and GPT analyses

## Requirements

### Python
- Python 3.12 or higher
- uv package manager

### Third-Party Programs
- **Image Processing**
  - HEIC Conversion (one of the following):
    - ImageMagick (recommended, works on all platforms)
    - macOS: `sips` (built-in)
    - Linux: `libheif-tools`
  - SVG Conversion:
    - `librsvg` (provides `rsvg-convert`)
- **Document Processing**
  - `pandoc` (for document format conversion)

## Installation

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required programs
brew install librsvg
brew install pandoc
brew install imagemagick  # optional, sips is built-in
```

#### Linux (Ubuntu/Debian)
```bash
# Install required programs
sudo apt-get update
sudo apt-get install librsvg2-bin
sudo apt-get install pandoc
sudo apt-get install imagemagick  # recommended for HEIC conversion
# or
sudo apt-get install libheif-tools  # alternative for HEIC conversion
```

#### Windows
1. Install [librsvg](https://wiki.gnome.org/Projects/LibRsvg)
2. Install [Pandoc](https://pandoc.org/installing.html)
3. Install [ImageMagick](https://imagemagick.org/script/download.php#windows) for HEIC conversion
4. Add the installed programs to your system PATH

# Install with uv
uv pip install .

# Create and edit config
cp example_config.toml consolidate_config.toml
