# Consolidate Markdown

A tool for consolidating various data sources into markdown files.

## Overview

This tool processes data from multiple sources and converts them into markdown files. Supported sources include:

- Claude conversations
- ChatGPT conversations
- Bear notes
- Gmail emails
- Images (with metadata)
- XBookmarks

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/chadrwalters/consolidate-markdown.git
   cd consolidate-markdown
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   uv pip install -e .
   ```

3. Copy the example configuration file and edit it with your settings:
   ```bash
   cp config.toml.example config.toml
   ```

## Configuration

Edit the `config.toml` file to configure:

- Output directory
- API keys (if needed)
- Source directories for each data type
- Logging level

### ChatGPT Processor Configuration

To configure the ChatGPT processor, add the following to your `config.toml` file:

```toml
[[sources]]
type = "chatgpt"
src_dir = "/path/to/chatgpt/export"
dest_dir = "/path/to/output/directory"
```

The ChatGPT processor supports the following configuration options:

- `src_dir`: Directory containing ChatGPT export files
- `dest_dir`: Directory where markdown files will be created
- `no_image`: Whether to skip GPT image description generation (global option)
- `cache`: Whether to use caching to avoid reprocessing unchanged files (global option)

## Usage

Run the main script:

```bash
python -m consolidate_markdown
```

Or use specific processors:

```bash
python -m consolidate_markdown --processor claude
python -m consolidate_markdown --processor bear
python -m consolidate_markdown --processor gmail
python -m consolidate_markdown --processor image
python -m consolidate_markdown --processor xbookmarks
python -m consolidate_markdown --processor chatgpt
```

## Output Format

The tool generates a flat directory structure with only markdown files. Attachments (images, documents) are not copied to the output directory; instead, information about attachments is embedded as comments in the markdown output.

### Attachment Format

#### Images

Images are represented as comments in the markdown:

```markdown
<!-- ATTACHMENT: IMAGE: image.jpg (800x600, 150KB) -->
<!-- GPT Description: A scenic mountain landscape with snow-capped peaks -->
![A scenic mountain landscape with snow-capped peaks]()
```

#### Documents

Documents are represented as comments in the markdown:

```markdown
<!-- ATTACHMENT: DOCUMENT: document.pdf (250KB) -->
<!-- Content: The document contains information about... -->
[document.pdf]()
```

### ChatGPT Conversation Format

ChatGPT conversations are converted to markdown files with the following structure:

```markdown
# Conversation Title
*Created: 2023-05-15 14:30:45*

## User:
User message content

## Assistant:
Assistant message content

<!-- ATTACHMENT: IMAGE: image.jpg (800x600, 150KB) -->
<!-- GPT Description: A scenic mountain landscape with snow-capped peaks -->
![A scenic mountain landscape with snow-capped peaks]()

## User:
Another user message
```

This approach provides several benefits:
- Simplified output directory structure (flat hierarchy)
- Reduced disk space usage (no duplicate files)
- Preserved attachment metadata
- Better compatibility with version control systems

## Adding New Processors

Consolidate Markdown is designed to be extensible, allowing you to add support for new data sources by creating new processors. This guide outlines the steps and best practices for adding a new processor, drawing from the implementation of the ChatGPT processor as an example.

### 1. Create a New Processor Class

Create a new Python file within the `src/consolidate_markdown/processors/` directory (e.g., `src/consolidate_markdown/processors/your_processor.py`). Your processor class should:

* **Inherit from `SourceProcessor`**: This base class provides common functionalities like caching, progress tracking, and attachment handling.
* **Implement `_process_impl(self, config: Config) -> ProcessingResult`**: This is the core method where your processor's logic resides. It should:
  * Initialize and return a `ProcessingResult` object to track processing statistics.
  * Iterate through your source data (files, API responses, etc.).
  * For each item, perform the necessary parsing, data extraction, and markdown conversion.
  * Utilize helper methods from `SourceProcessor` and `AttachmentHandlerMixin` (if applicable) to manage caching and attachments.
  * Update the `ProcessingResult` object with relevant statistics (processed, generated, from cache, skipped, errors).
* **Define `_processor_type` Property**: This property (using `@property` decorator) should return a unique string identifier for your processor type (e.g., `"your_source_type"`). This string is used for logging, caching, and result tracking.
* **Implement `validate(self) -> None` (Optional but Recommended)**: This method is called during processor initialization to validate the source configuration. You should check if the `src_dir` exists and if any required dependencies are available.
* **Call `super().__init__(source_config, cache_manager)` in `__init__**: Ensure you initialize the base `SourceProcessor` class correctly.

**Example (Conceptual):**

```python
from pathlib import Path
from typing import Optional
from ..cache import CacheManager
from ..config import Config, SourceConfig
from .base import SourceProcessor, ProcessingResult

class YourProcessor(SourceProcessor):
    """Processor for Your Data Source."""

    def __init__(
        self, source_config: SourceConfig, cache_manager: Optional[CacheManager] = None
    ):
        """Initialize YourProcessor."""
        super().__init__(source_config, cache_manager)
        self.validate()

    @property
    def _processor_type(self) -> str:
        """Return the processor type."""
        return "your_source_type"

    def validate(self) -> None:
        """Validate source configuration."""
        if not self.source_config.src_dir.exists():
            raise ValueError(f"Source directory does not exist: {self.source_config.src_dir}")

    def _process_impl(self, config: Config) -> ProcessingResult:
        """Process data from Your Data Source."""
        result = ProcessingResult()
        # Ensure destination directory exists
        self._ensure_dest_dir()

        source_files = list(self.source_config.src_dir.glob("*.yourdata")) # Example file glob

        for source_file in self._apply_limit(source_files):
            try:
                # 1. Read and Parse Source File
                content = source_file.read_text(encoding="utf-8")
                # ... Your custom parsing logic to extract data ...

                # 2. Convert to Markdown
                markdown_content = f"# Processed File: {source_file.name}\n\n{content}" # Example markdown

                # 3. Write Output File
                output_path = self.source_config.dest_dir / f"{source_file.stem}.md"
                self.process_file_with_cache( # Using caching mechanism
                    source_file, content, output_path, config, result, None, lambda x: markdown_content
                )
                result.add_generated(self._processor_type) # Update stats

            except Exception as e:
                error_msg = f"Error processing {source_file.name}: {str(e)}"
                self.logger.error(error_msg)
                result.add_error(error_msg, self._processor_type)
                result.add_skipped(self._processor_type)

        self.logger.info(f"Completed processing {self._processor_type} source: {result}")
        return result
```

### 2. Update Configuration

* **Add a new `SourceConfig` entry**: In `config.py`, add a new dataclass entry to the `Config.sources` list in `config.template.toml` and `config.toml.example` to allow users to configure your new processor in `config.toml`.

  ```toml
  [[sources]]
  type = "your_source_type"
  srcDir = "~/Path/to/your/data" # Example path
  destDir = "./output/your_output" # Example output directory
  # Add any processor-specific configuration options here if needed
  ```

* **Add `VALID_SOURCE_TYPES`**: Make sure to add your processor's `type` string (e.g., `"your_source_type"`) to the `VALID_SOURCE_TYPES` list in `config.py` to ensure it's recognized as a valid source type.

### 3. Register Your Processor

* **Import your processor class**: In `src/consolidate_markdown/__init__.py`, import your new processor class.
* **Register your processor**: Add your processor to the `PROCESSOR_TYPES` dictionary using `register_processor()`. The key should be the same `type` string you defined in your `SourceConfig` and the `_processor_type` property of your processor class.

  ```python
  from .processors.base import SourceProcessor
  from .processors.bear import BearProcessor
  from .processors.xbookmarks import XBookmarksProcessor
  from .processors.chatgpt import ChatGPTProcessor # Example
  from .processors.claude import ClaudeProcessor # Example
  # Import your new processor here:
  from .processors.your_processor import YourProcessor

  PROCESSOR_TYPES: Dict[str, Type[SourceProcessor]] = {}

  def register_processor(name: str, processor_class: Type[SourceProcessor]) -> None:
      """Register a processor type."""
      PROCESSOR_TYPES[name] = processor_class

  # Register existing processors:
  register_processor("bear", BearProcessor)
  register_processor("xbookmarks", XBookmarksProcessor)
  register_processor("claude", ClaudeProcessor)
  register_processor("chatgpt", ChatGPTProcessor)

  # Register your new processor:
  register_processor("your_source_type", YourProcessor)

  __all__ = [
      # ... other exports ...
      "PROCESSOR_TYPES",
      "register_processor",
      "YourProcessor", # Add your processor to __all__
  ]
  ```

### 4. Implement Data Parsing and Markdown Conversion

This is the most crucial part and will heavily depend on your source data format.

* **File Handling**: Implement logic to read and parse your source files. Consider using streaming parsers (like `ijson` used in ChatGPT processor) if dealing with potentially large files.
* **Data Extraction**: Extract the relevant information you want to convert to markdown.
* **Markdown Formatting**: Transform the extracted data into markdown. Use standard markdown syntax and consider how to represent different data elements (text, lists, code blocks, etc.).
* **Attachment Handling (if applicable)**:
  * If your source has attachments, use the `AttachmentProcessor` to process them (convert formats, extract metadata).
  * Use `AttachmentHandlerMixin` methods (`_format_image`, `_format_document`, `_process_attachment`) to generate comment-based attachment representations in your markdown output. Avoid physically copying attachment files to the output directory.

### 5. Implement Caching

Leverage the caching mechanism in `SourceProcessor` and `CacheManager` to avoid reprocessing unchanged data.

* **`process_file_with_cache()`**: Use this method in your `_process_impl` to handle caching logic for individual items (e.g., notes, conversations).
* **`should_process_from_cache()`**: This utility function in `base.py` helps determine if an item needs to be processed or if a cached version can be used.
* **`CacheManager`**: The `CacheManager` handles the actual cache storage and retrieval. You generally don't need to modify `CacheManager` directly but should use its methods through the base `SourceProcessor` class.

### 6. Implement Error Handling

* **Custom Exceptions**: Use the custom exception classes defined in `src/consolidate_markdown/exceptions.py` (e.g., `ProcessorError`, `ConversionError`, `APIError`) to raise specific errors within your processor.
* **`ProcessingResult.add_error()`**: Use this method to record errors encountered during processing. This will ensure errors are reported in the summary and log output.
* **`try...except` blocks**: Wrap potentially failing operations (file parsing, API calls, conversions) in `try...except` blocks to gracefully handle errors and prevent the processor from crashing.

### 7. Add Unit Tests

Write comprehensive unit tests for your new processor in the `tests/unit/` directory.

* **Test Core Logic**: Test the main processing logic in `_process_impl` and any helper methods.
* **Test Caching**: Verify that caching works as expected (cache hits and misses).
* **Test Error Handling**: Ensure your processor handles errors gracefully and reports them correctly.
* **Mock External Dependencies**: Use mocking (`unittest.mock` or `pytest-mock`) to isolate your processor from external dependencies (API calls, file system operations, etc.) during unit testing. Look at existing test files (e.g., `test_chatgpt_processor.py`, `test_claude_processor.py`) for examples.

### 8. Update Documentation

* **Add documentation for your processor**: In `README.md`, add a section describing your new processor, its purpose, configuration options (if any), and usage instructions.
* **Update the list of supported sources**: Add your new processor to the list of supported sources in the README.

### 9. Test Thoroughly

* **Run all unit tests**: Ensure all tests pass, including the ones you added for your new processor.
* **Integration testing**: Test your processor with real-world data from your source to ensure it works correctly in practice.

By following these steps and referring to the existing processor implementations (especially `ChatGPTProcessor` and `ClaudeProcessor`), you can effectively add new processors to Consolidate Markdown and expand its capabilities. Remember to prioritize clear, well-tested, and maintainable code.

## Development

### Running Tests

```bash
pytest
```

### Running Specific Tests

```bash
pytest tests/unit/test_claude_processor.py
pytest tests/unit/test_chatgpt_processor.py
```

## License

[MIT License](LICENSE)
