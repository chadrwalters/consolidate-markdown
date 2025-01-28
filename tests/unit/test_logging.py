"""Unit tests for logging system."""

import logging

import pytest

from consolidate_markdown.logging import SummaryLogger, setup_logging


@pytest.fixture
def log_dir(tmp_path):
    """Create a temporary log directory."""
    return tmp_path / ".cm" / "logs"


def test_setup_logging_basic(log_dir):
    """Test basic logging setup."""
    setup_logging(log_dir.parent, "INFO")

    # Verify log directory creation
    assert log_dir.exists()
    assert (log_dir / "consolidate.log").exists()

    # Verify root logger configuration
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) == 2  # File and console handlers


def test_setup_logging_handlers(log_dir):
    """Test logging handler configuration."""
    setup_logging(log_dir.parent, "DEBUG")

    root_logger = logging.getLogger()
    handlers = root_logger.handlers

    # Verify file handler
    file_handler = next(
        h for h in handlers if isinstance(h, logging.handlers.RotatingFileHandler)
    )
    assert file_handler.baseFilename.endswith("consolidate.log")
    assert file_handler.maxBytes == 1024 * 1024  # 1MB
    assert file_handler.backupCount == 5

    # Verify console handler
    console_handler = next(h for h in handlers if isinstance(h, logging.StreamHandler))
    assert console_handler.formatter._fmt == "%(levelname)s: %(message)s"


def test_log_rotation(log_dir):
    """Test log file rotation."""
    setup_logging(log_dir.parent, "INFO")
    logger = logging.getLogger("test_rotation")

    # Write enough data to trigger rotation
    large_msg = "x" * 1024 * 1024  # 1MB message
    logger.info(large_msg)

    # Verify rotation occurred
    log_files = list(log_dir.glob("consolidate.log*"))
    assert len(log_files) > 1


def test_log_levels(log_dir):
    """Test different logging levels."""
    setup_logging(log_dir.parent, "INFO")
    logger = logging.getLogger("test_levels")
    log_file = log_dir / "consolidate.log"

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
        assert summary_logger.stats == {
            "processed": 0,
            "generated": 0,
            "from_cache": 0,
            "skipped": 0,
        }
        assert summary_logger.source_stats == {}
        assert summary_logger.errors == []

    def test_source_stats_initialization(self, summary_logger):
        """Test source statistics initialization."""
        summary_logger._init_source_stats("test_source")

        expected_stats = {
            "processed": 0,
            "generated": 0,
            "from_cache": 0,
            "skipped": 0,
            "images": {"processed": 0, "generated": 0, "from_cache": 0, "skipped": 0},
            "documents": {
                "processed": 0,
                "generated": 0,
                "from_cache": 0,
                "skipped": 0,
            },
            "gpt": {"from_cache": 0, "generated": 0},
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

        assert summary_logger.source_stats[source]["images"]["generated"] == 1
        assert summary_logger.source_stats[source]["images"]["from_cache"] == 1

    def test_add_document_operations(self, summary_logger):
        """Test adding document operations to summary."""
        source = "test_source"

        summary_logger.add_document_generated(source)
        summary_logger.add_document_from_cache(source)

        assert summary_logger.source_stats[source]["documents"]["generated"] == 1
        assert summary_logger.source_stats[source]["documents"]["from_cache"] == 1

    def test_add_gpt_operations(self, summary_logger):
        """Test adding GPT operations to summary."""
        source = "test_source"

        summary_logger.add_gpt_generated(source)
        summary_logger.add_gpt_from_cache(source)

        assert summary_logger.source_stats[source]["gpt"]["generated"] == 1
        assert summary_logger.source_stats[source]["gpt"]["from_cache"] == 1

    def test_add_errors(self, summary_logger):
        """Test adding errors to summary."""
        source = "test_source"
        error_msg = "Test error message"

        summary_logger.add_error(source, error_msg)

        assert len(summary_logger.errors) == 1
        assert summary_logger.errors[0]["source"] == source
        assert summary_logger.errors[0]["message"] == error_msg

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
        assert "test_source" in summary
        assert "Generated: 1" in summary
        assert "Images Generated: 1" in summary
        assert "Documents Generated: 1" in summary
        assert "GPT Generated: 1" in summary
        assert "Test error" in summary


def test_concurrent_logging(log_dir):
    """Test concurrent logging from multiple threads."""
    import threading
    import time

    setup_logging(log_dir.parent, "INFO")
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
    log_content = (log_dir / "consolidate.log").read_text()
    assert len(log_content.splitlines()) >= 400  # 4 threads * 100 messages


def test_error_handling(log_dir):
    """Test logging system error handling."""
    setup_logging(log_dir.parent, "INFO")
    logger = logging.getLogger("test_errors")

    # Test logging with various error conditions
    logger.error("Test error", exc_info=True)
    logger.exception("Test exception")

    log_content = (log_dir / "consolidate.log").read_text()
    assert "Test error" in log_content
    assert "Test exception" in log_content
    assert "Traceback" in log_content
