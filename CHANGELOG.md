# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-27

### Added
- Initial release of Consolidate Markdown
- Support for Bear.app notes and X Bookmarks processing
- AI-powered image analysis using GPT-4o
- Document conversion to Markdown (docx, pdf, csv, xlsx)
- Image format conversion (heic, svg, jpg, png)
- Parallel processing with --sequential option
- Configurable processing pipeline via TOML
- Detailed logging and progress tracking
- Atomic file operations and backup system
- Error recovery and graceful failure handling

### Dependencies
- Python 3.12+
- UV for environment management
- OpenAI API key for GPT-4o integration
- Platform-specific tools for image conversion

### Security
- Safe path handling for spaces and special characters
- Secure API key management
- No execution of untrusted content

### Documentation
- Complete architecture documentation
- Configuration guide with examples
- Installation and quick start guides
- Troubleshooting documentation
- API reference and development guide
