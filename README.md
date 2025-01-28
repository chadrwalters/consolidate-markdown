# consolidate-markdown

A tool to consolidate markdown files from various sources into a single location.

## Features

- Consolidate markdown files from multiple sources
- GPT-powered image analysis and description
- Configurable output formats
- Caching for improved performance
- Detailed logging and error reporting

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

## Options

- `--config PATH`: Path to configuration file (default: config.toml)
- `--no-image`: Skip image analysis
- `--force`: Force regeneration of all files
- `--debug`: Enable debug logging

## Documentation

- [Configuration Guide](docs/configuration.md)
- [Architecture Overview](docs/architecture.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details
