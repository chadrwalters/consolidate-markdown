"""Logging configuration."""

import logging  # Standard library
from logging.handlers import RotatingFileHandler  # Standard library
from pathlib import Path  # Standard library
from typing import Any, List, Optional  # Standard library

from rich.console import Console  # External dependency: rich
from rich.logging import RichHandler  # External dependency: rich
from rich.progress import Progress  # External dependency: rich

from .config import Config

logger = logging.getLogger(__name__)

# Global console instance for consistent styling
console = Console()

# Global progress instance for access by RichHandler
current_progress: Optional[Progress] = None


def set_progress(progress: Optional[Progress]) -> None:
    """Set the current progress instance for logging integration.

    Args:
        progress: The progress instance to use, or None to clear
    """
    global current_progress
    current_progress = progress


class ProgressAwareHandler(RichHandler):
    """A Rich logging handler that is aware of progress bars.

    This handler will temporarily pause progress bars when logging messages,
    then restore them afterward, to prevent the progress bars from being
    disrupted by log messages.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the handler.

        Args:
            *args: Positional arguments to pass to RichHandler
            **kwargs: Keyword arguments to pass to RichHandler
        """
        super().__init__(*args, **kwargs)
        self.console = console

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record.

        Args:
            record: The log record to emit
        """
        global current_progress

        # If we have a progress instance, temporarily use its console
        # This ensures logs don't disrupt the progress display
        try:
            if current_progress:
                # Store the original console
                original_console = self.console
                # Use the progress console for logging
                self.console = current_progress.console
                # Emit the log record
                super().emit(record)
                # Restore the original console
                self.console = original_console
            else:
                super().emit(record)
        except Exception:
            self.handleError(record)


class SummaryLogger:
    """A logger that collects messages for a summary.

    This class is used to collect log messages during processing,
    then display a summary at the end. It's useful for showing
    a clean summary of what happened during processing, without
    cluttering the console with detailed logs.
    """

    def __init__(self) -> None:
        """Initialize the summary logger."""
        self.messages: List[str] = []

    def add(self, message: str) -> None:
        """Add a message to the summary.

        Args:
            message: The message to add
        """
        self.messages.append(message)

    def display(self) -> None:
        """Display the summary."""
        if not self.messages:
            return

        console.print("\n[bold]Summary:[/bold]")
        for message in self.messages:
            console.print(f"  {message}")


def ensure_log_file(log_file: Path) -> None:
    """Ensure the log file exists and is writable.

    Args:
        log_file: The log file path
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)
    if not log_file.exists():
        log_file.touch()


def setup_logging(config: Config) -> None:
    """Set up logging configuration.

    Args:
        config: The configuration to use
    """
    # First, configure third-party loggers to prevent debug output
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("openai._base_client").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("httpcore").setLevel(logging.INFO)
    logging.getLogger("fitz").setLevel(logging.INFO)  # PyMuPDF
    logging.getLogger("PIL").setLevel(logging.INFO)  # Pillow

    # Create log directory if it doesn't exist
    log_dir = config.global_config.cm_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.global_config.log_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Configure file logging
    log_file = log_dir / "consolidate_markdown.log"
    ensure_log_file(log_file)

    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Configure Rich console logging with progress awareness
    # For lower verbosity levels, only show WARNING and above log messages
    # Handle the case where log_level might be a string (in tests) or int (in real usage)
    if (
        hasattr(config.global_config, "verbosity")
        and config.global_config.verbosity <= 1
    ):
        # Convert log_level to int if it's a string
        log_level_value = config.global_config.log_level
        if isinstance(log_level_value, str):
            log_level_value = getattr(logging, log_level_value)

        # Ensure we're comparing integers for log levels
        log_level_int: int = int(log_level_value)
        console_log_level = max(log_level_int, logging.WARNING)
    else:
        # Use the configured log level
        log_level_value = config.global_config.log_level
        if isinstance(log_level_value, str):
            console_log_level = getattr(logging, log_level_value)
        else:
            console_log_level = log_level_value

    console_handler = ProgressAwareHandler(
        console=console,
        rich_tracebacks=True,
        markup=True,
        show_path=False,
        level=console_log_level,
        show_time=False,  # Time is already in the message
        enable_link_path=False,  # Don't show file links
    )
    root_logger.addHandler(console_handler)

    # Set up attachment logging
    from .attachments.logging import setup_attachment_logging

    setup_attachment_logging(config.global_config.log_level)

    # Create a dedicated media processing log file
    media_log_file = log_dir / "media_processing.log"
    ensure_log_file(media_log_file)

    # Create a handler for the media processing log file
    media_file_handler = RotatingFileHandler(
        media_log_file, maxBytes=1024 * 1024, backupCount=5  # 1MB
    )
    media_file_handler.setFormatter(file_formatter)

    # Get the attachment logger and add the media file handler
    attachment_logger = logging.getLogger("consolidate_markdown.attachments")
    attachment_logger.addHandler(media_file_handler)

    logger.debug("Logging configured successfully")
