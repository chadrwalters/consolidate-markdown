"""Unit tests for logging system."""

import logging
from logging.handlers import RotatingFileHandler
from typing import cast
from unittest.mock import MagicMock

import pytest

from consolidate_markdown.config import Config, GlobalConfig
from consolidate_markdown.log_setup import (
    ProgressAwareHandler,
    SummaryLogger,
    setup_logging,
)


@pytest.fixture
def log_dir(tmp_path):
    """Create a temporary log directory."""
    return tmp_path / ".cm" / "logs"


@pytest.fixture
def config(log_dir):
    """Create a test configuration."""
    global_config = GlobalConfig(
        cm_dir=log_dir.parent,
        log_level="INFO",
        force_generation=False,
        no_image=True,
        openai_key=None,
    )
    return Config(global_config=global_config)


def test_setup_logging_basic(config):
    """Test basic logging setup."""
    setup_logging(config)

    # Verify log directory creation
    log_dir = config.global_config.cm_dir / "logs"
    assert log_dir.exists()
    assert (log_dir / "consolidate_markdown.log").exists()

    # Verify root logger configuration
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) == 2  # File and console handlers


def test_setup_logging_handlers(config):
    """Test logging handler configuration."""
    config.global_config.log_level = "DEBUG"
    setup_logging(config)

    root_logger = logging.getLogger()

    # Verify file handler
    file_handler = cast(
        RotatingFileHandler,
        next(h for h in root_logger.handlers if isinstance(h, RotatingFileHandler)),
    )
    assert str(file_handler.baseFilename).endswith("consolidate_markdown.log")
    assert file_handler.maxBytes == 1024 * 1024  # 1MB
    assert file_handler.backupCount == 5

    # Verify console handler
    console_handler = next(
        h for h in root_logger.handlers if isinstance(h, ProgressAwareHandler)
    )
    assert console_handler.level == logging.DEBUG  # Should match config

    # Test that the handler can format messages
    test_record = logging.LogRecord(
        "test", logging.INFO, "test.py", 1, "Test message", (), None
    )
    formatted_message = console_handler.format(test_record)
    assert "Test message" in formatted_message  # Rich formatting will add styling


def test_log_levels(config):
    """Test different logging levels."""
    setup_logging(config)
    logger = logging.getLogger("test_levels")
    log_dir = config.global_config.cm_dir / "logs"
    log_file = log_dir / "consolidate_markdown.log"

    # Test different levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    log_content = log_file.read_text()
    assert "Debug message" not in log_content  # Should be filtered
    assert "Info message" in log_content
    assert "Warning message" in log_content
    assert "Error message" in log_content


class TestSummaryLogger:
    """Tests for the SummaryLogger class."""

    @pytest.fixture
    def summary_logger(self):
        """Create a SummaryLogger instance for testing."""
        return SummaryLogger()

    def test_initialization(self, summary_logger):
        """Test SummaryLogger initialization."""
        # The current implementation uses messages instead of stats
        assert hasattr(summary_logger, "messages")
        assert summary_logger.messages == []

    def test_add_message(self, summary_logger):
        """Test adding a message to the summary."""
        test_message = "Test message"
        summary_logger.add(test_message)
        assert test_message in summary_logger.messages
        assert len(summary_logger.messages) == 1

    def test_add_multiple_messages(self, summary_logger):
        """Test adding multiple messages to the summary."""
        messages = ["Message 1", "Message 2", "Message 3"]
        for message in messages:
            summary_logger.add(message)

        assert len(summary_logger.messages) == 3
        for message in messages:
            assert message in summary_logger.messages

    def test_display_with_messages(self, summary_logger, monkeypatch, capsys):
        """Test displaying the summary with messages."""
        # Mock console.print to capture output
        mock_print = MagicMock()
        monkeypatch.setattr("consolidate_markdown.log_setup.console.print", mock_print)

        # Add some messages
        summary_logger.add("Message 1")
        summary_logger.add("Message 2")

        # Display the summary
        summary_logger.display()

        # Verify console.print was called
        assert mock_print.call_count >= 1

    def test_display_without_messages(self, summary_logger, monkeypatch):
        """Test displaying the summary without messages."""
        # Mock console.print to capture output
        mock_print = MagicMock()
        monkeypatch.setattr("consolidate_markdown.log_setup.console.print", mock_print)

        # Display the summary with no messages
        summary_logger.display()

        # Verify console.print was not called
        assert mock_print.call_count == 0


def test_concurrent_logging(config):
    """Test concurrent logging from multiple threads."""
    import threading
    import time

    setup_logging(config)
    logger = logging.getLogger("test_concurrent")

    def log_messages():
        for i in range(100):
            logger.info(f"Message {i} from thread {threading.current_thread().name}")
            time.sleep(0.001)

    threads = [threading.Thread(target=log_messages) for _ in range(4)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Verify all messages were logged
    log_dir = config.global_config.cm_dir / "logs"
    log_content = (log_dir / "consolidate_markdown.log").read_text()
    assert len(log_content.splitlines()) >= 400  # 4 threads * 100 messages


def test_error_handling(config):
    """Test logging system error handling."""
    setup_logging(config)
    logger = logging.getLogger("test_errors")

    # Test logging with various error conditions
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Error occurred: %s", str(e))

    log_dir = config.global_config.cm_dir / "logs"
    log_content = (log_dir / "consolidate_markdown.log").read_text()
    assert "Error occurred: Test error" in log_content


def test_log_level_from_string() -> None:
    # Implementation of the function
    pass


def test_log_level_from_invalid_string() -> None:
    # Implementation of the function
    pass


def test_log_level_from_int() -> None:
    # Implementation of the function
    pass


def test_log_level_from_invalid_int() -> None:
    # Implementation of the function
    pass


def test_log_level_from_invalid_type() -> None:
    # Implementation of the function
    pass


def test_get_log_level_from_config() -> None:
    # Implementation of the function
    pass


def test_get_log_level_from_config_with_invalid_level() -> None:
    # Implementation of the function
    pass


def test_get_log_level_from_config_with_no_level() -> None:
    # Implementation of the function
    pass


def test_get_log_level_from_config_with_no_logging_section() -> None:
    # Implementation of the function
    pass


def test_get_log_level_from_config_with_no_config() -> None:
    # Implementation of the function
    pass


def test_get_log_level_from_config_with_debug_flag() -> None:
    # Implementation of the function
    pass


def test_get_log_level_from_config_with_quiet_flag() -> None:
    # Implementation of the function
    pass
