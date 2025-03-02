"""Unit tests for attachment logging."""

import logging
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest  # type: ignore

from consolidate_markdown.attachments.logging import (
    attachment_logger,
    log_dalle_processing,
    log_file_processing,
    log_file_search,
    log_media_processing_error,
    log_wav_processing,
    setup_attachment_logging,
)


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Create a mock logger for testing."""
    with patch("consolidate_markdown.attachments.logging.attachment_logger") as mock:
        yield mock


def test_setup_attachment_logging() -> None:
    """Test that attachment logging can be set up correctly."""
    # Save the original level
    original_level = attachment_logger.level

    try:
        # Test with DEBUG level
        setup_attachment_logging(logging.DEBUG)
        assert attachment_logger.level == logging.DEBUG

        # Test with INFO level
        setup_attachment_logging(logging.INFO)
        assert attachment_logger.level == logging.INFO

        # Test with string level
        setup_attachment_logging("WARNING")
        assert attachment_logger.level == logging.WARNING
    finally:
        # Restore the original level
        attachment_logger.setLevel(original_level)


def test_log_file_search(mock_logger: MagicMock) -> None:
    """Test the log_file_search function."""
    file_id = "test_file_id"
    search_dir = Path("/test/dir")
    matches = [Path("/test/dir/file1.jpg"), Path("/test/dir/file2.jpg")]

    log_file_search(file_id, search_dir, matches)

    # Verify debug calls - updated to match actual implementation
    assert mock_logger.debug.call_count == 4
    mock_logger.debug.assert_any_call(
        f"Searching for file ID: {file_id} in {search_dir}"
    )
    mock_logger.debug.assert_any_call(f"Directory exists: {search_dir.exists()}")
    mock_logger.debug.assert_any_call(f"Found {len(matches)} matches in {search_dir}")
    mock_logger.debug.assert_any_call(f"Matches: {[str(m) for m in matches]}")

    # Test with no matches
    mock_logger.reset_mock()
    log_file_search(file_id, search_dir, [])

    assert mock_logger.debug.call_count == 3
    mock_logger.debug.assert_any_call(f"No matches found in {search_dir}")


def test_log_file_processing(mock_logger: MagicMock) -> None:
    """Test the log_file_processing function."""
    file_path = Path("/test/dir/file.jpg")
    file_type = "image"

    # Test with file exists
    log_file_processing(file_path, file_type, True)

    assert mock_logger.debug.call_count == 2
    mock_logger.debug.assert_any_call(f"Processing {file_type} file: {file_path}")
    mock_logger.debug.assert_any_call("File exists: True")

    # Test with file does not exist
    mock_logger.reset_mock()
    log_file_processing(file_path, file_type, False)

    assert mock_logger.debug.call_count == 2
    assert mock_logger.warning.call_count == 1
    mock_logger.warning.assert_called_once_with(f"Image file not found: {file_path}")


def test_log_media_processing_error(mock_logger: MagicMock) -> None:
    """Test the log_media_processing_error function."""
    file_path = Path("/test/dir/file.jpg")
    error_msg = "Test error message"
    file_type = "image"

    log_media_processing_error(file_path, error_msg, file_type)

    assert mock_logger.error.call_count == 1
    mock_logger.error.assert_called_once_with(
        f"Error processing {file_type} file {file_path}: {error_msg}", exc_info=True
    )


def test_log_dalle_processing(mock_logger: MagicMock) -> None:
    """Test the log_dalle_processing function."""
    file_id = "test_file_id"
    dalle_dir = Path("/test/dir/dalle-generations")
    matches = [Path("/test/dir/dalle-generations/file1.jpg")]

    log_dalle_processing(file_id, dalle_dir, matches)

    # Updated to match actual implementation
    assert mock_logger.debug.call_count == 5
    mock_logger.debug.assert_any_call(f"Processing DALL-E image with ID: {file_id}")
    mock_logger.debug.assert_any_call(f"DALL-E directory: {dalle_dir}")
    mock_logger.debug.assert_any_call(f"DALL-E directory exists: {dalle_dir.exists()}")
    mock_logger.debug.assert_any_call(f"Found {len(matches)} DALL-E matches")
    mock_logger.debug.assert_any_call(f"DALL-E matches: {[str(m) for m in matches]}")

    # Test with no matches
    mock_logger.reset_mock()
    log_dalle_processing(file_id, dalle_dir, [])

    assert mock_logger.debug.call_count == 4
    mock_logger.debug.assert_any_call(f"No DALL-E matches found for ID: {file_id}")


def test_log_wav_processing(mock_logger: MagicMock) -> None:
    """Test the log_wav_processing function."""
    file_path = Path("/test/dir/file.wav")

    # Test successful processing
    log_wav_processing(file_path, True)

    assert mock_logger.debug.call_count == 2
    mock_logger.debug.assert_any_call(f"Processing WAV file: {file_path}")
    mock_logger.debug.assert_any_call(f"Successfully processed WAV file: {file_path}")

    # Test failed processing
    mock_logger.reset_mock()
    error_msg = "Test error message"
    log_wav_processing(file_path, False, error_msg)

    assert mock_logger.debug.call_count == 1
    assert mock_logger.error.call_count == 1
    mock_logger.debug.assert_called_once_with(f"Processing WAV file: {file_path}")
    mock_logger.error.assert_called_once_with(
        f"Failed to process WAV file {file_path}: {error_msg}", exc_info=True
    )
