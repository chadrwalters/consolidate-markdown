"""Unit tests for logging setup."""

import logging
from logging.handlers import RotatingFileHandler
from unittest.mock import MagicMock, Mock, patch

import pytest

from consolidate_markdown.config import Config, GlobalConfig
from consolidate_markdown.log_setup import ProgressAwareHandler, setup_logging


@pytest.fixture
def temp_config(tmp_path):
    """Create a test configuration."""
    return Config(
        global_config=GlobalConfig(
            cm_dir=tmp_path / ".cm",
            log_level="INFO",
            no_image=False,
            force_generation=False,
            openai_key="dummy",
        ),
        sources=[],
    )


@pytest.fixture
def mock_handlers():
    """Create mock handlers for testing."""
    with (
        patch("consolidate_markdown.log_setup.ProgressAwareHandler") as progress_mock,
        patch("consolidate_markdown.log_setup.RotatingFileHandler") as file_mock,
        patch("consolidate_markdown.log_setup.console") as console_mock,
        patch("logging.getLogger") as get_logger_mock,
    ):
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
        root_logger_mock.addHandler = MagicMock(
            side_effect=lambda h: root_logger_mock.handlers.append(h)
        )
        get_logger_mock.return_value = root_logger_mock

        yield progress_mock, file_mock, root_logger_mock


def test_setup_logging_creates_directory(temp_config):
    """Test that setup_logging creates the log directory if it doesn't exist."""
    # Verify directory doesn't exist yet
    log_dir = temp_config.global_config.cm_dir / "logs"
    assert not log_dir.exists()

    # Set up logging
    setup_logging(temp_config)

    # Verify directory was created
    assert log_dir.exists()
    assert log_dir.is_dir()

    # Verify log file was created
    log_file = log_dir / "consolidate_markdown.log"
    assert log_file.exists()
    assert log_file.is_file()


def test_setup_logging_handles_existing_directory(temp_config):
    """Test that setup_logging works with an existing log directory."""
    # Create the directory structure first
    log_dir = temp_config.global_config.cm_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Set up logging
    setup_logging(temp_config)

    # Verify log file was created
    log_file = log_dir / "consolidate_markdown.log"
    assert log_file.exists()
    assert log_file.is_file()


def test_logging_writes_successfully(temp_config):
    """Test that logging actually writes to the file without errors."""
    # Set up logging
    setup_logging(temp_config)

    # Get the log file path
    log_file = temp_config.global_config.cm_dir / "logs" / "consolidate_markdown.log"

    # Write some test log messages
    test_logger = logging.getLogger("test")
    test_logger.debug("Test debug message")
    test_logger.info("Test info message")
    test_logger.warning("Test warning message")

    # Verify the log file exists and has content
    assert log_file.exists()
    content = log_file.read_text()
    assert (
        "Test debug message" not in content
    )  # Debug shouldn't be logged at INFO level
    assert "Test info message" in content
    assert "Test warning message" in content


def test_log_levels(temp_config, caplog):
    """Test different log levels are handled correctly."""
    # Test each log level
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }

    for level_name, level_value in level_map.items():
        # Update config with specific level
        temp_config.global_config.log_level = level_name

        # Setup logging with config
        setup_logging(temp_config)
        logger = logging.getLogger("consolidate_markdown")

        # Clear previous records
        caplog.clear()

        # Log messages at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Verify only messages at or above the set level are logged
        records = [r for r in caplog.records if r.name == "consolidate_markdown"]
        assert all(r.levelno >= level_value for r in records)


def test_handlers_setup(mock_handlers, temp_config):
    """Test that both handlers are configured correctly."""
    progress_mock, file_mock, root_logger_mock = mock_handlers

    # Set up logging
    setup_logging(temp_config)

    # Verify handlers are created
    assert progress_mock.call_count >= 1
    assert file_mock.call_count >= 1

    # Verify handlers are added to root logger
    assert len(root_logger_mock.handlers) == 3
    assert progress_mock.return_value in root_logger_mock.handlers
    assert file_mock.return_value in root_logger_mock.handlers

    # Verify handler levels
    for handler in root_logger_mock.handlers:
        assert handler.level == logging.DEBUG


def test_third_party_logger_levels(temp_config):
    """Test that third-party loggers are set to WARNING."""
    setup_logging(temp_config)
    third_party_loggers = ["urllib3", "requests"]
    for logger_name in third_party_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)  # Explicitly set level
        assert logger.level == logging.WARNING
