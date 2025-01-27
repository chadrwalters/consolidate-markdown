# Installation Guide (v1.0.0)

## System Requirements
- Python 3.12+
- uv (Universal Virtualenv)
- OpenAI API key for GPT-4o
- Platform-specific tools:
  - **macOS**:
    - `sips` (built-in) for HEIC conversion
    - Inkscape (`brew install inkscape`) for SVG conversion
  - **Linux**:
    - `libheif-tools` for HEIC conversion
    - Inkscape (`apt install inkscape` or equivalent) for SVG conversion
  - **Windows**:
    - ImageMagick for HEIC conversion
    - Inkscape for SVG conversion

## Installation Steps
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd consolidate-markdown
   ```

2. Install with uv:
   ```bash
   uv pip install .
   ```

3. Install platform-specific tools:
   ```bash
   # macOS
   brew install inkscape

   # Linux (Ubuntu/Debian)
   sudo apt install libheif-tools inkscape

   # Windows (using Chocolatey)
   choco install imagemagick inkscape
   ```

4. Create configuration file:
   ```bash
   cp example_config.toml consolidate_config.toml
   ```

5. Set OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

## Verification
Run the following command to verify installation:
```bash
uv run python -m consolidate_markdown --version
```

## Development Installation
For development, install additional dependencies:
```bash
uv pip install -e ".[dev]"
   ```
