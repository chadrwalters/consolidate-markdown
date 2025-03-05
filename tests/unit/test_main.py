"""Unit tests for the main module."""

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from consolidate_markdown.__main__ import main, parse_args


class TestParseArgs:
    """Test suite for argument parsing."""

    def test_default_args(self):
        """Test default argument values."""
        with patch("sys.argv", ["consolidate_markdown"]):
            args = parse_args()
            assert args.config == Path("config.toml")
            assert not args.no_image
            assert not args.force
            assert not args.delete
            assert args.log_level == "INFO"
            assert args.verbosity == 1
            assert args.processor is None
            assert args.limit is None

    def test_custom_args(self):
        """Test custom argument values."""
        with patch(
            "sys.argv",
            [
                "consolidate_markdown",
                "--config",
                "custom_config.toml",
                "--no-image",
                "--force",
                "--delete",
                "--log-level",
                "DEBUG",
                "--verbosity",
                "2",
                "--processor",
                "bear",
                "--limit",
                "10",
            ],
        ):
            args = parse_args()
            assert args.config == Path("custom_config.toml")
            assert args.no_image
            assert args.force
            assert args.delete
            assert args.log_level == "DEBUG"
            assert args.verbosity == 2
            assert args.processor == "bear"
            assert args.limit == 10


class TestMain:
    """Test suite for the main function."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        mock_config = MagicMock()
        mock_config.global_config.cm_dir = Path("/tmp/cm_dir")
        mock_config.global_config.no_image = False
        mock_config.global_config.force_generation = False
        mock_config.global_config.log_level = logging.INFO

        # Create mock sources
        source1 = MagicMock()
        source1.dest_dir = Path("/tmp/dest_dir1")
        source2 = MagicMock()
        source2.dest_dir = Path("/tmp/dest_dir2")
        mock_config.sources = [source1, source2]

        return mock_config

    @pytest.fixture
    def mock_args(self):
        """Create mock command line arguments."""
        mock_args = MagicMock()
        mock_args.config = Path("config.toml")
        mock_args.no_image = False
        mock_args.force = False
        mock_args.delete = False
        mock_args.log_level = "INFO"
        mock_args.verbosity = 2
        mock_args.processor = None
        mock_args.limit = None
        return mock_args

    @patch("consolidate_markdown.__main__.parse_args")
    @patch("consolidate_markdown.__main__.load_config")
    @patch("consolidate_markdown.__main__.setup_logging")
    @patch("consolidate_markdown.__main__.Runner")
    @patch("consolidate_markdown.__main__.print_summary")
    @patch("consolidate_markdown.__main__.print_compact_summary")
    @patch("pathlib.Path.mkdir")
    def test_main_normal_execution(
        self,
        mock_mkdir,
        mock_print_compact_summary,
        mock_print_summary,
        mock_runner_class,
        mock_setup_logging,
        mock_load_config,
        mock_parse_args,
        mock_config,
        mock_args,
    ):
        """Test normal execution of the main function."""
        # Set up mocks
        mock_parse_args.return_value = mock_args

        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_result = MagicMock()
        mock_result.errors = []
        mock_runner.run.return_value = mock_result
        mock_runner_class.return_value = mock_runner

        # Call the function
        with patch.object(sys, "exit") as mock_exit:
            main()
            mock_exit.assert_not_called()

        # Verify the calls
        mock_parse_args.assert_called_once()
        mock_load_config.assert_called_once_with(Path("config.toml"))
        mock_setup_logging.assert_called_once_with(mock_config)
        mock_mkdir.assert_called()
        mock_runner_class.assert_called_once_with(mock_config)
        mock_runner.run.assert_called_once()
        # With verbosity=2, it should call print_summary
        mock_print_summary.assert_called_once_with(mock_result)
        # With verbosity=2, it should not call print_compact_summary
        mock_print_compact_summary.assert_not_called()

    @patch("consolidate_markdown.__main__.parse_args")
    @patch("consolidate_markdown.__main__.load_config")
    @patch("consolidate_markdown.__main__.setup_logging")
    @patch("consolidate_markdown.__main__.Runner")
    @patch("consolidate_markdown.__main__.print_summary")
    @patch("consolidate_markdown.__main__.print_compact_summary")
    @patch("pathlib.Path.mkdir")
    def test_main_with_processor_and_limit(
        self,
        mock_mkdir,
        mock_print_compact_summary,
        mock_print_summary,
        mock_runner_class,
        mock_setup_logging,
        mock_load_config,
        mock_parse_args,
        mock_config,
        mock_args,
    ):
        """Test main function with processor and limit arguments."""
        # Set up mocks
        mock_args.processor = "bear"
        mock_args.limit = 10
        mock_parse_args.return_value = mock_args

        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_result = MagicMock()
        mock_result.errors = []
        mock_runner.run.return_value = mock_result
        mock_runner_class.return_value = mock_runner

        # Call the function
        with patch.object(sys, "exit") as mock_exit:
            main()
            mock_exit.assert_not_called()

        # Verify the calls
        assert mock_runner.selected_processor == "bear"
        assert mock_runner.processing_limit == 10

    @patch("consolidate_markdown.__main__.parse_args")
    @patch("consolidate_markdown.__main__.load_config")
    @patch("consolidate_markdown.__main__.setup_logging")
    @patch("consolidate_markdown.__main__.Runner")
    @patch("consolidate_markdown.__main__.print_summary")
    @patch("consolidate_markdown.__main__.print_compact_summary")
    @patch("pathlib.Path.mkdir")
    def test_main_with_errors(
        self,
        mock_mkdir,
        mock_print_compact_summary,
        mock_print_summary,
        mock_runner_class,
        mock_setup_logging,
        mock_load_config,
        mock_parse_args,
        mock_config,
        mock_args,
    ):
        """Test main function when processing results in errors."""
        # Set up mocks
        mock_parse_args.return_value = mock_args

        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_result = MagicMock()
        mock_result.errors = ["Error 1", "Error 2"]
        mock_runner.run.return_value = mock_result
        mock_runner_class.return_value = mock_runner

        # Call the function
        with patch.object(sys, "exit") as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)

    @patch("consolidate_markdown.__main__.parse_args")
    @patch("consolidate_markdown.__main__.load_config")
    @patch("consolidate_markdown.__main__.setup_logging")
    @patch("consolidate_markdown.__main__.Runner")
    @patch("pathlib.Path.mkdir")
    def test_main_with_exception(
        self,
        mock_mkdir,
        mock_runner_class,
        mock_setup_logging,
        mock_load_config,
        mock_parse_args,
        mock_config,
        mock_args,
    ):
        """Test main function when an exception occurs during processing."""
        # Set up mocks
        mock_parse_args.return_value = mock_args

        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_runner.run.side_effect = Exception("Test exception")
        mock_runner_class.return_value = mock_runner

        # Call the function
        with patch.object(sys, "exit") as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)

    @patch("consolidate_markdown.__main__.parse_args")
    @patch("consolidate_markdown.__main__.load_config")
    @patch("consolidate_markdown.__main__.logger.error")
    def test_main_with_config_error(
        self,
        mock_logger_error,
        mock_load_config,
        mock_parse_args,
        mock_args,
    ):
        """Test main function when config loading fails."""
        # Set up mocks
        mock_parse_args.return_value = mock_args
        mock_load_config.side_effect = Exception("Config error")

        # Call the function and expect SystemExit
        with pytest.raises(SystemExit) as excinfo:
            main()

        # Verify exit code is 1
        assert excinfo.value.code == 1

        # Verify that the error was logged
        mock_logger_error.assert_called_once()
        assert "Failed to load config" in mock_logger_error.call_args[0][0]

    @patch("consolidate_markdown.__main__.parse_args")
    @patch("consolidate_markdown.__main__.load_config")
    @patch("consolidate_markdown.__main__.setup_logging")
    @patch("consolidate_markdown.__main__.Runner")
    @patch("consolidate_markdown.__main__.print_summary")
    @patch("consolidate_markdown.__main__.print_compact_summary")
    @patch("consolidate_markdown.__main__.print_deletion_message")
    @patch("consolidate_markdown.__main__.shutil.rmtree")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_main_with_delete_flag(
        self,
        mock_exists,
        mock_mkdir,
        mock_rmtree,
        mock_print_deletion,
        mock_print_compact_summary,
        mock_print_summary,
        mock_runner_class,
        mock_setup_logging,
        mock_load_config,
        mock_parse_args,
        mock_config,
        mock_args,
    ):
        """Test main function with delete flag."""
        # Set up mocks
        mock_args.delete = True
        mock_parse_args.return_value = mock_args

        mock_load_config.return_value = mock_config
        mock_exists.return_value = True

        mock_runner = MagicMock()
        mock_result = MagicMock()
        mock_result.errors = []
        mock_runner.run.return_value = mock_result
        mock_runner_class.return_value = mock_runner

        # Call the function
        with patch.object(sys, "exit") as mock_exit:
            main()
            mock_exit.assert_not_called()

        # Verify the calls
        assert mock_rmtree.call_count == 3  # cm_dir and 2 dest_dirs
        assert mock_print_deletion.call_count == 3
