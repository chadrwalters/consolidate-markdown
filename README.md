# consolidate-markdown

A tool to consolidate markdown files from various sources into a single location.

## Features

- Consolidate markdown files from multiple sources
- GPT-powered image analysis and description
- PDF text extraction using pdfminer-six
- Configurable output formats
- Caching for improved performance
- Detailed logging and error reporting
- Standardized rules system for consistency

## Installation

```bash
pip install consolidate-markdown
```

## Usage

1. Create a configuration file (e.g., `config.toml`):

```toml
[global]
cm_dir = ".cm"
no_image = false
force = false

[[sources]]
type = "bear"
src_dir = "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files"
dest_dir = "output/bear"

[[sources]]
type = "xbookmarks"
src_dir = "~/Library/Containers/com.apple.Safari/Data/Library/Safari/Bookmarks.plist"
dest_dir = "output/bookmarks"
```

2. Run the tool:

```bash
consolidate-markdown --config config.toml
```

## Rules System

The project follows a standardized rules system located in `.cursor/rules/` that ensures consistent behavior and quality:

### Core Rules (00-02)
- `00-startup.md`: Core startup sequence and initialization
- `01-validation.md`: Rule validation and conflict detection
- `02-base.md`: Base system standards

### Language Rules (10-19)
- `10-python-style.md`: Python coding standards
- `11-python-typing.md`: Type hint requirements
- `12-python-testing.md`: Testing standards

### Documentation Rules (20-29)
- `20-markdown-style.md`: Markdown formatting standards
- `21-markdown-docs.md`: Documentation requirements

### Process Rules (30-39)
- `30-git-workflow.md`: Git workflow standards
- `31-pre-commit.md`: Pre-commit hook requirements

### Operation Rules (40-59)
- `40-error-handling.md`: Error handling standards
- `41-logging.md`: Logging requirements
- `50-operation-modes.md`: Operation mode definitions

### Integration Rules (60-79)
- `70-command-triggers.md`: Command pattern standards

### Rule Validation

All rules are automatically validated through:
1. Pre-commit hooks for local validation
2. CI/CD pipeline checks
3. Automated conflict detection
4. Generated documentation summaries

For detailed information about the rules system, see:
- [Rules Overview](docs/rules/overview.md)
- [Rule Creation Guide](docs/rules/creation.md)

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
3. Make your changes
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details
