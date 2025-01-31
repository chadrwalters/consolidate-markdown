"""Unit tests for logging system."""

import logging
from logging.handlers import RotatingFileHandler
from typing import cast

import pytest

from consolidate_markdown.config import Config, GlobalConfig
from consolidate_markdown.log_setup import SummaryLogger, setup_logging


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
        h
        for h in root_logger.handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, RotatingFileHandler)
    )
    assert console_handler.formatter is not None
    test_record = logging.LogRecord(
        "test", logging.INFO, "test.py", 1, "Test message", (), None
    )
    formatted_message = console_handler.formatter.format(test_record)
    assert formatted_message == "INFO: Test message"


def test_log_rotation(config):
    """Test log file rotation."""
    setup_logging(config)
    logger = logging.getLogger("test_rotation")

    # Write enough data to trigger rotation
    large_msg = "x" * 1024 * 1024  # 1MB message
    logger.info(large_msg)

    # Verify rotation occurred
    log_dir = config.global_config.cm_dir / "logs"
    log_files = list(log_dir.glob("consolidate_markdown.log*"))
    assert len(log_files) >= 1


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
    """Test suite for SummaryLogger class."""

    @pytest.fixture
    def summary_logger(self):
        """Create a SummaryLogger instance."""
        return SummaryLogger()

    def test_initialization(self, summary_logger):
        """Test SummaryLogger initialization."""
        expected_stats = {
            "processed": 0,
            "generated": 0,
            "from_cache": 0,
            "skipped": 0,
            "documents_processed": 0,
            "documents_generated": 0,
            "documents_from_cache": 0,
            "documents_skipped": 0,
            "images_processed": 0,
            "images_generated": 0,
            "images_from_cache": 0,
            "images_skipped": 0,
            "gpt_generated": 0,
            "gpt_from_cache": 0,
            "gpt_skipped": 0,
            "errors": [],
        }
        assert summary_logger.stats == expected_stats
        assert summary_logger.source_stats == {}

    def test_source_stats_initialization(self, summary_logger):
        """Test source statistics initialization."""
        summary_logger._init_source_stats("test_source")

        expected_stats = {
            "processed": 0,
            "generated": 0,
            "from_cache": 0,
            "skipped": 0,
            "documents_processed": 0,
            "documents_generated": 0,
            "documents_from_cache": 0,
            "documents_skipped": 0,
            "images_processed": 0,
            "images_generated": 0,
            "images_from_cache": 0,
            "images_skipped": 0,
            "gpt_generated": 0,
            "gpt_from_cache": 0,
            "gpt_skipped": 0,
            "errors": [],
        }
        assert summary_logger.source_stats["test_source"] == expected_stats

    def test_add_operations(self, summary_logger):
        """Test adding various operations to summary."""
        source = "test_source"

        # Add some operations
        summary_logger.add_generated(source)
        summary_logger.add_from_cache(source)
        summary_logger.add_skipped(source)

        # Verify source stats
        assert summary_logger.source_stats[source]["generated"] == 1
        assert summary_logger.source_stats[source]["from_cache"] == 1
        assert summary_logger.source_stats[source]["skipped"] == 1

        # Verify global stats
        assert summary_logger.stats["generated"] == 1
        assert summary_logger.stats["from_cache"] == 1
        assert summary_logger.stats["skipped"] == 1

    def test_add_image_operations(self, summary_logger):
        """Test adding image operations to summary."""
        source = "test_source"

        summary_logger.add_image_generated(source)
        summary_logger.add_image_from_cache(source)

        assert summary_logger.source_stats[source]["images_generated"] == 1
        assert summary_logger.source_stats[source]["images_from_cache"] == 1

    def test_add_document_operations(self, summary_logger):
        """Test adding document operations to summary."""
        source = "test_source"

        summary_logger.add_document_generated(source)
        summary_logger.add_document_from_cache(source)

        assert summary_logger.source_stats[source]["documents_generated"] == 1
        assert summary_logger.source_stats[source]["documents_from_cache"] == 1

    def test_add_gpt_operations(self, summary_logger):
        """Test adding GPT operations to summary."""
        source = "test_source"

        summary_logger.add_gpt_generated(source)
        summary_logger.add_gpt_from_cache(source)

        assert summary_logger.source_stats[source]["gpt_generated"] == 1
        assert summary_logger.source_stats[source]["gpt_from_cache"] == 1

    def test_add_errors(self, summary_logger):
        """Test adding errors to summary."""
        source = "test_source"
        error_msg = "Test error message"

        summary_logger.add_error(source, error_msg)

        assert len(summary_logger.errors) == 1
        assert error_msg in summary_logger.errors

    def test_get_summary(self, summary_logger):
        """Test getting formatted summary."""
        source = "test_source"

        # Add various operations
        summary_logger.add_generated(source)
        summary_logger.add_image_generated(source)
        summary_logger.add_document_generated(source)
        summary_logger.add_gpt_generated(source)
        summary_logger.add_error(source, "Test error")

        summary = summary_logger.get_summary()

        assert isinstance(summary, str)
        assert source.title() in summary
        assert "Generated:  1" in summary
        assert "Images" in summary
        assert "Documents" in summary
        assert "Test error" in summary


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
