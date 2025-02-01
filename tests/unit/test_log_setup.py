import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from consolidate_markdown.config import Config, GlobalConfig
from consolidate_markdown.log_setup import setup_logging


class TestLogSetup(TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)

    def test_setup_logging_creates_directory(self):
        """Test that setup_logging creates the log directory if it doesn't exist."""
        # Create a test config with a non-existent directory
        config = Config(
            global_config=GlobalConfig(
                cm_dir=self.temp_path / ".cm",
                log_level="INFO",
                no_image=False,
                force_generation=False,
                openai_key="dummy",
            ),
            sources=[],
        )

        # Verify directory doesn't exist yet
        log_dir = config.global_config.cm_dir / "logs"
        self.assertFalse(log_dir.exists())

        # Set up logging
        setup_logging(config)

        # Verify directory was created
        self.assertTrue(log_dir.exists())
        self.assertTrue(log_dir.is_dir())

        # Verify log file was created
        log_file = log_dir / "consolidate_markdown.log"
        self.assertTrue(log_file.exists())
        self.assertTrue(log_file.is_file())

    def test_setup_logging_handles_existing_directory(self):
        """Test that setup_logging works with an existing log directory."""
        # Create the directory structure first
        log_dir = self.temp_path / ".cm" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        config = Config(
            global_config=GlobalConfig(
                cm_dir=self.temp_path / ".cm",
                log_level="INFO",
                no_image=False,
                force_generation=False,
                openai_key="dummy",
            ),
            sources=[],
        )

        # Set up logging
        setup_logging(config)

        # Verify log file was created
        log_file = log_dir / "consolidate_markdown.log"
        self.assertTrue(log_file.exists())
        self.assertTrue(log_file.is_file())

    def test_logging_writes_successfully(self):
        """Test that logging actually writes to the file without errors."""
        config = Config(
            global_config=GlobalConfig(
                cm_dir=self.temp_path / ".cm",
                log_level="DEBUG",
                no_image=False,
                force_generation=False,
                openai_key="dummy",
            ),
            sources=[],
        )

        # Set up logging
        setup_logging(config)

        # Get the log file path
        log_file = config.global_config.cm_dir / "logs" / "consolidate_markdown.log"

        # Write some test log messages
        test_logger = logging.getLogger("test")
        test_logger.debug("Test debug message")
        test_logger.info("Test info message")
        test_logger.warning("Test warning message")

        # Verify the log file exists and has content
        self.assertTrue(log_file.exists())
        content = log_file.read_text()
        self.assertIn("Test debug message", content)
        self.assertIn("Test info message", content)
        self.assertIn("Test warning message", content)
