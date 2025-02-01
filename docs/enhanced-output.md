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
   def test_rich_handler_configuration():
       """Test RichHandler is properly configured with correct settings."""

   def test_log_level_propagation():
       """Test log levels are correctly propagated to Rich handler."""

   def test_color_scheme():
       """Test color scheme is applied correctly for different log levels."""

   def test_fallback_formatting():
       """Test fallback behavior when color support is not available."""

   def test_file_handler_persistence():
       """Ensure file logging still works alongside Rich console output."""
   ```

2. `tests/unit/test_runner.py`
   ```python
   def test_progress_bar_creation():
       """Test TQDM progress bars are created with correct settings."""

   def test_progress_bar_updates():
       """Test progress bars update correctly during processing."""

   def test_parallel_progress_tracking():
       """Test progress tracking works in parallel processing mode."""

   def test_nested_progress_bars():
       """Test nested progress bars (source + conversation) work correctly."""
   ```

3. `tests/unit/test_summary.py`
   ```python
   def test_summary_table_creation():
       """Test Rich table is created with correct columns and styling."""

   def test_summary_metrics():
       """Test all ProcessingResult metrics are included in summary."""

   def test_summary_formatting():
       """Test summary table formatting and style consistency."""

   def test_error_display():
       """Test error messages are properly formatted in summary."""
   ```

4. `tests/integration/test_console_output.py`
   ```python
   def test_end_to_end_output():
       """Test complete console output from start to finish."""

   def test_debug_mode_output():
       """Test additional output appears in debug mode."""

   def test_info_mode_output():
       """Test limited output appears in info mode."""

   def test_error_handling_display():
       """Test error scenarios are displayed correctly."""
   ```

### Testing Utilities

1. Create Mock Console
   ```python
   class MockConsole:
       """Mock Rich console for testing output without actual terminal."""
       def __init__(self, force_terminal: bool = True, color_system: str = "truecolor"):
           self.captured = []
           self.force_terminal = force_terminal
           self.color_system = color_system

       def print(self, *args, **kwargs):
           """Capture print calls for verification."""
           self.captured.append((args, kwargs))
   ```

2. Create Progress Capture
   ```python
   class ProgressCapture:
       """Capture TQDM progress updates for testing."""
       def __init__(self):
           self.updates = []
           self.desc = None
           self.total = None

       def update(self, n=1):
           """Record progress updates."""
           self.updates.append(n)
   ```

### Test Categories

1. **Unit Tests**
   - Rich handler configuration
   - Progress bar creation and updates
   - Summary table generation
   - Color scheme application
   - Metric tracking accuracy
   - Error message formatting

2. **Integration Tests**
   - Complete processing output
   - Log level effects
   - Terminal capability handling
   - Error scenario display
   - Progress bar nesting

3. **Visual Tests**
   - Color scheme consistency
   - Table alignment and borders
   - Progress bar appearance
   - Error highlighting
   - Debug vs Info mode differences

### Test Fixtures

1. **Console Configurations**
   ```python
   @pytest.fixture
   def mock_console():
       """Provide a mock console for output testing."""
       return MockConsole()

   @pytest.fixture
   def no_color_console():
       """Provide a console without color support."""
       return MockConsole(color_system=None)
   ```

2. **Sample Data**
   ```python
   @pytest.fixture
   def sample_processing_result():
       """Provide a ProcessingResult with known values for testing."""
       result = ProcessingResult()
       result.processed = 10
       result.from_cache = 5
       # ... set other metrics ...
       return result
   ```

### Test Environment Variables

```python
@pytest.fixture(autouse=True)
def test_env():
    """Set up test environment variables."""
    with mock.patch.dict(os.environ, {
        "TERM": "xterm-256color",
        "NO_COLOR": "",  # Test with and without color
        "FORCE_COLOR": "",  # Test forced color modes
    }):
        yield
```

### Test Execution

1. **Standard Tests**
   ```bash
   uv run python -m pytest tests/unit/test_log_setup.py tests/unit/test_runner.py tests/unit/test_summary.py
   ```

2. **Visual Tests**
   ```bash
   uv run python -m pytest tests/integration/test_console_output.py --capture=no
   ```

3. **Coverage Check**
   ```bash
   uv run python -m pytest --cov=consolidate_markdown.log_setup --cov=consolidate_markdown.runner
   ```

### Test Documentation

Each test file should include:
- Purpose of test suite
- Test coverage targets
- Required fixtures
- Example outputs
- Common failure scenarios

### Continuous Integration

Update GitHub Actions workflow to:
- Run all tests including visual tests
- Verify color output in different terminal types
- Check coverage requirements are met
- Test in both TTY and non-TTY environments
