# Enhanced Console Output Implementation Plan

## Overview

This document outlines the implementation plan for enhancing the console output of the consolidate-markdown tool with rich formatting, color coding, and progress bars. The goal is to provide a more readable and informative user experience in both INFO and DEBUG modes.

## 1. New Dependencies

### Rich
- Install via UV: `uv pip install rich`
- Handles colored logging and pretty console output
- Provides rich text formatting, panels, and tables

### TQDM
- Already in use
- Wraps loops to show progress bars
- Will be integrated with Rich for consistent styling

## 2. Logging Output Enhancement

### File: `src/consolidate_markdown/log_setup.py`

#### Rich Handler Integration
```python
from rich.logging import RichHandler

# In log_setup.py inside setup_logging():
root_logger.setLevel(config.global_config.log_level)
# Clear existing handlers
root_logger.handlers.clear()

# Use RichHandler for console logging with color formatting
console_handler = RichHandler(
    rich_tracebacks=True,
    markup=True,
    show_path=False,
    level=config.global_config.log_level,
)
root_logger.addHandler(console_handler)
```

#### Color Scheme
- DEBUG: Blue/Magenta
- INFO: Green
- WARNING: Yellow
- ERROR: Red

## 3. Progress Bar Integration

### File: `src/consolidate_markdown/runner.py`

#### Source Processing Progress
```python
from tqdm import tqdm

for source in tqdm(self.config.sources, desc="Processing Sources", unit="src"):
    # (existing processing logic)
```

#### Conversation Processing Progress
```python
for conversation in tqdm(conversations, desc="Processing Conversations", unit="conv"):
    # Process each conversation...
```

## 4. Summary Output Enhancement

### File: `src/consolidate_markdown/__main__.py`

#### Rich Console Implementation
```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

def print_summary(result: ProcessingResult):
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric")
    table.add_column("Count", justify="right")

    table.add_row("Processed", str(result.processed))
    table.add_row("Generated", str(result.regenerated))
    table.add_row("From Cache", str(result.from_cache))
    table.add_row("Skipped", str(result.skipped))
    table.add_row("Documents Processed", str(result.documents_processed))
    table.add_row("Images Processed", str(result.images_processed))
    table.add_row("GPT Analyses Skipped", str(result.gpt_skipped))

    panel = Panel(table, title="[bold green]Consolidation Summary[/bold green]", expand=False)
    console.print(panel)
```

## 5. Log Level Integration

### INFO Mode
- Shows colored INFO messages
- Displays progress bars
- Shows final summary panel
- Hides debug details

### DEBUG Mode
- Shows all INFO mode content
- Adds detailed debug messages in blue/magenta
- Includes additional processing details
- Shows full tracebacks when errors occur

## 6. Sample Output

```
[bold red]Deleting .cm directory: .cm[/bold red]
[bold red]Deleting output directory: /Users/.../My Drive/_ChatGPTExport[/bold red]

[green]INFO:[/green] Starting consolidation with 5 items...
[blue]DEBUG:[/blue] Processing conversation: [italic]Tech Career Advice[/italic]
[blue]DEBUG:[/blue] Found 32 messages in tree traversal
[blue]DEBUG:[/blue] Wrote conversation to: /.../20250129 - Tech_Career_Advice.md
...
[Progress bar: Processing Conversations...]

[green]INFO:[/green] Successfully processed: 20250131 - Interview.md
[green]INFO:[/green] Completed bear source: 5 processed [0 from cache]

[bold green]Consolidation Summary[/bold green]
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric                       ┃ Count ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━┫
┃ Processed                    ┃ 20    ┃
┃ Generated                    ┃ 20    ┃
┃ From Cache                   ┃ 0     ┃
┃ Skipped                      ┃ 0     ┃
┃ Documents Processed          ┃ 5     ┃
┃ Images Processed            ┃ 4     ┃
┃ GPT Analyses Skipped        ┃ 4     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━┛
```

## 7. Implementation Steps

1. Add Rich dependency to `pyproject.toml`
2. Modify `log_setup.py` to use RichHandler
3. Update `runner.py` with TQDM progress bars
4. Create summary output function
5. Test in both INFO and DEBUG modes
6. Verify fallback behavior in non-color terminals

## 8. Files to Modify

1. `src/consolidate_markdown/log_setup.py`
   - Switch to RichHandler
   - Add color formatting

2. `src/consolidate_markdown/runner.py`
   - Add TQDM progress bars
   - Integrate with Rich formatting

3. `src/consolidate_markdown/__main__.py`
   - Add summary output function
   - Integrate Rich console

4. `pyproject.toml`
   - Add Rich dependency

## 9. Notes

- Rich's console output requires ANSI color support
- Consider fallback formatting for non-color terminals
- No changes needed to CLI interface
- Existing log levels (--log-level) remain unchanged

## 10. Testing Strategy

### Test Files to Create/Modify

1. `tests/unit/test_log_setup.py`
   ```python
   def test_setup_logging_creates_directory():
       """Test that setup_logging creates the log directory if it doesn't exist."""

   def test_setup_logging_handles_existing_directory():
       """Test that setup_logging works with an existing log directory."""

   def test_logging_writes_successfully():
       """Test that logging actually writes to the file without errors."""

   def test_log_levels():
       """Test different log levels are handled correctly."""

   def test_handlers_setup():
       """Test that both handlers are configured correctly."""

   def test_third_party_logger_levels():
       """Test that third-party loggers are set to WARNING."""
   ```

2. `tests/unit/test_summary.py`
   ```python
   def test_summary_table_creation():
       """Test creation of summary table."""

   def test_processor_columns():
       """Test processor columns in summary table."""

   def test_metric_rows():
       """Test metric rows in summary table."""

   def test_error_display():
       """Test error display in summary."""

   def test_processor_specific_errors():
       """Test processor-specific error display."""

   def test_zero_stats_display():
       """Test display of empty/zero statistics."""

   def test_separator_rows():
       """Test separator rows in summary table."""

   def test_no_errors_message():
       """Test display when no errors are present."""
   ```

### Testing Utilities

1. Mock Console
   ```python
   @pytest.fixture
   def mock_console():
       """Create a mock console for testing."""
       console = Mock(spec=Console)
       console.size = (80, 24)
       console.options = Mock()
       console.is_terminal = True
       # Create a print method that preserves Rich objects
       print_mock = Mock()
       print_mock.side_effect = lambda *args, **kwargs: None
       console.print = print_mock
       return console
   ```

2. Mock Handlers
   ```python
   @pytest.fixture
   def mock_handlers():
       """Create mock handlers for testing."""
       with patch("consolidate_markdown.log_setup.ProgressAwareHandler") as progress_mock, \
            patch("consolidate_markdown.log_setup.RotatingFileHandler") as file_mock, \
            patch("consolidate_markdown.log_setup.console") as console_mock, \
            patch("logging.getLogger") as get_logger_mock:
           # Create mock progress handler
           progress_handler = MagicMock(spec=ProgressAwareHandler)
           progress_handler.level = logging.DEBUG
           progress_mock.return_value = progress_handler

           # Create mock file handler
           file_handler = MagicMock(spec=RotatingFileHandler)
           file_handler.level = logging.DEBUG
           file_mock.return_value = file_handler

           # Set up console mock
           console_mock.size = (80, 24)
           console_mock.options = Mock()
           console_mock.is_terminal = True

           # Set up root logger mock
           root_logger_mock = MagicMock()
           root_logger_mock.handlers = []
           root_logger_mock.addHandler = MagicMock(side_effect=lambda h: root_logger_mock.handlers.append(h))
           get_logger_mock.return_value = root_logger_mock

           yield progress_mock, file_mock, root_logger_mock
   ```

### Test Categories

1. **Log Setup Tests**
   - Directory creation and handling
   - Log file creation and writing
   - Log level configuration
   - Handler setup and configuration
   - Third-party logger configuration

2. **Summary Tests**
   - Table creation and formatting
   - Column and row content
   - Error display and formatting
   - Zero statistics handling
   - Separator row placement

### Test Execution

```bash
# Run log setup and summary tests
uv run pytest tests/unit/test_log_setup.py tests/unit/test_summary.py -v

# Run with coverage
uv run pytest --cov=consolidate_markdown.log_setup --cov=consolidate_markdown.output tests/unit/
```

### Test Documentation

Each test file includes:
- Purpose of test suite
- Required fixtures
- Test cases for different scenarios
- Mocking strategies for external dependencies
- Assertions for expected behavior

### Continuous Integration

The GitHub Actions workflow:
- Runs all unit tests
- Verifies test coverage
- Checks code formatting
- Validates documentation
