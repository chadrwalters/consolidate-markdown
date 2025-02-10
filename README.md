# consolidate-markdown

A tool to consolidate markdown files from various sources into a single location.

## Features

- Consolidate markdown files from multiple sources
- GPT-powered image analysis and description
- PDF text extraction using pdfminer-six
- Configurable output formats
- Caching for improved performance
- Detailed logging and error reporting

## Installation

```bash
# Using UV (recommended)
uv pip install .

# Using pip (alternative)
pip install consolidate-markdown
```

## Usage

1. Create a configuration file (e.g., `config.toml`):

```toml
[global]
cm_dir = ".cm"
no_image = false
force = false
api_provider = "openrouter"  # or "openai"
openrouter_key = "your_key_here"  # Required for OpenRouter
openai_key = "your_key_here"      # Required for OpenAI

[[sources]]
type = "bear"
src_dir = "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files"
dest_dir = "output/bear"
options = { model = "google/gemini-pro-vision-1.0" }  # Optional: specify model

[[sources]]
type = "xbookmarks"
src_dir = "~/Library/Containers/com.apple.Safari/Data/Library/Safari/Bookmarks.plist"
dest_dir = "output/bookmarks"
```

2. Run the tool:

```bash
consolidate-markdown --config config.toml
```

## Options

- `--config PATH`: Path to configuration file (default: config.toml)
- `--no-image`: Skip image analysis
- `--force`: Force regeneration of all files
- `--debug`: Enable debug logging
- `--processor TYPE`: Run only the specified processor type (bear, xbookmarks, chatgptexport)
- `--limit N`: Process only the N most recent items from each source

## Examples

```bash
# Process all sources
consolidate-markdown --config config.toml

# Process only Bear notes
consolidate-markdown --config config.toml --processor bear

# Process last 5 items from each source
consolidate-markdown --config config.toml --limit 5

# Process last 2 Bear notes only
consolidate-markdown --config config.toml --processor bear --limit 2

# Force regeneration of all files
consolidate-markdown --config config.toml --force
```

## Documentation

- [Configuration Guide](docs/configuration.md)
- [Architecture Overview](docs/architecture.md)

## Model Performance

The tool supports multiple vision models through OpenRouter, each with different strengths and performance characteristics. Our latest model analysis (February 2024) shows:

- **GPT-4 Vision**: Best overall performance for both technical and UI content
- **Google Gemini Pro Vision**: Strong technical understanding, excellent value
- **Yi Vision**: Good balance of capabilities and speed
- **DeepInfra BLIP**: Reliable for basic tasks, competitive speed

For detailed performance analysis, benchmarks, and recommendations, see our [Model Performance Analysis](docs/model_performance.md).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following our standards:
   - Use UV for dependency management
   - Run pre-commit hooks before committing
   - Ensure all tests pass with `uv run pytest`
4. Submit a pull request

For detailed contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE) for details
