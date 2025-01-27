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
  - macOS: `sips` (built-in, used for HEIC conversion)
  - Linux/Windows: Install an alternative HEIC converter
  - `inkscape` or `rsvg-convert` (for SVG conversion)
- **Document Processing**
  - `pandoc` (for document format conversion)

## Installation

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required programs
brew install inkscape  # or brew install librsvg for rsvg-convert
brew install pandoc
```

#### Linux (Ubuntu/Debian)
```bash
# Install required programs
sudo apt-get update
sudo apt-get install inkscape  # or librsvg2-bin for rsvg-convert
sudo apt-get install pandoc
```

#### Windows
1. Install [Inkscape](https://inkscape.org/release/) or [librsvg](https://wiki.gnome.org/Projects/LibRsvg)
2. Install [Pandoc](https://pandoc.org/installing.html)
3. Add the installed programs to your system PATH

# Install with uv
uv pip install .

# Create and edit config
cp example_config.toml consolidate_config.toml
```

## Usage
```bash
# Run consolidation (uses cache by default)
uv run python -m consolidate_markdown --config consolidate_config.toml

# Force regeneration (clears cache)
uv run python -m consolidate_markdown --config consolidate_config.toml --force

# Use --sequential for easier debugging
uv run python -m consolidate_markdown --config consolidate_config.toml --sequential

# Skip GPT image analysis (uses cached analyses if available)
uv run python -m consolidate_markdown --config consolidate_config.toml --no-image
```

## Documentation
See [docs/README.md](docs/README.md) for full documentation including:
- [Installation Guide](docs/installation.md)
- [Configuration Guide](docs/configuration.md)
- [Architecture Overview](docs/architecture.md)
- [Caching System](docs/caching.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

## License
MIT

## Changelog
See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.
