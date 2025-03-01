"""Tests for XBookmarksProcessor media handling."""

from unittest.mock import MagicMock, patch

import pytest
from consolidate_markdown.processors.xbookmarks import XBookmarksProcessor


@pytest.fixture
def test_dirs(tmp_path):
    """Create test directories."""
    src_dir = tmp_path / "source"
    dest_dir = tmp_path / "dest"
    src_dir.mkdir()
    dest_dir.mkdir()

    # Create a bookmark directory with an index file
    bookmark_dir = src_dir / "test_bookmark"
    bookmark_dir.mkdir()
    index_file = bookmark_dir / "index.md"
    index_file.write_text("# Test Bookmark")

    # Create a media directory with test images
    media_dir = bookmark_dir / "media"
    media_dir.mkdir()

    # Create test image files
    test_image = media_dir / "test_image.jpg"
    test_image.write_text("test image content")

    # Create test document file
    test_doc = bookmark_dir / "test_doc.pdf"
    test_doc.write_text("test document content")

    return {
        "src_dir": src_dir,
        "dest_dir": dest_dir,
        "bookmark_dir": bookmark_dir,
        "media_dir": media_dir,
        "test_image": test_image,
        "test_doc": test_doc,
    }


@pytest.fixture
def mock_source_config(test_dirs):
    """Create a mock SourceConfig."""
    mock_config = MagicMock()
    mock_config.type = "xbookmarks"
    mock_config.src_dir = test_dirs["src_dir"]
    mock_config.dest_dir = test_dirs["dest_dir"]
    mock_config.index_filename = "index.md"
    return mock_config


@pytest.fixture
def processor(mock_source_config):
    """Create a XBookmarksProcessor instance with mocked dependencies."""
    with patch("consolidate_markdown.processors.xbookmarks.CacheManager") as mock_cache:
        # Return a mock cache manager instance
        mock_cache.return_value = MagicMock()

        # Create the processor with the mock source config
        processor = XBookmarksProcessor(mock_source_config)

        # Mock the attachment_processor property
        mock_attachment_processor = MagicMock()
        processor._attachment_processor = mock_attachment_processor

        return processor


@pytest.fixture
def mock_config():
    """Create a mock Config."""
    mock_config = MagicMock()
    mock_config.global_config.force_generation = True
    mock_config.global_config.no_image = True
    return mock_config


def test_process_media(processor, test_dirs, mock_config):
    """Test processing media files."""
    # Mock the _process_attachment method
    with patch.object(
        processor, "_process_attachment", return_value="Mocked image content"
    ) as mock_process:
        result = MagicMock()

        # Call the _process_media method
        content = processor._process_media(
            test_dirs["bookmark_dir"],
            mock_config,
            result,
        )

        # Verify the _process_attachment method was called with the correct arguments
        mock_process.assert_called_once()
        args, kwargs = mock_process.call_args
        assert args[0] == test_dirs["test_image"]
        assert kwargs["is_image"] is True

        # Verify the returned content
        assert content == "Mocked image content"


def test_process_attachments(processor, test_dirs, mock_config):
    """Test processing non-media attachments."""
    # Mock the _process_attachment method
    with patch.object(
        processor, "_process_attachment", return_value="Mocked document content"
    ) as mock_process:
        result = MagicMock()

        # Call the _process_attachments method
        content = processor._process_attachments(
            "Original content",
            test_dirs["bookmark_dir"],
            processor.attachment_processor,
            mock_config,
            result,
        )

        # Verify the _process_attachment method was called with the correct arguments
        mock_process.assert_called_once()
        args, kwargs = mock_process.call_args
        assert args[0] == test_dirs["test_doc"]
        assert kwargs["is_image"] is False

        # Verify the returned content
        assert content == "Mocked document content"


def test_process_impl_integration(processor, test_dirs, mock_config):
    """Test the _process_impl method with mocked attachment processing."""
    # Mock the _process_media and _process_attachments methods
    with (
        patch.object(
            processor, "_process_media", return_value="Media content"
        ) as mock_media,
        patch.object(
            processor, "_process_attachments", return_value="Attachment content"
        ) as mock_attachments,
        patch.object(processor, "cache_manager") as mock_cache_manager,
    ):
        # Mock the get_note_cache method
        mock_cache_manager.get_note_cache.return_value = None

        # Call the _process_impl method
        result = processor._process_impl(mock_config)

        # Verify the methods were called
        mock_media.assert_called_once()
        mock_attachments.assert_called_once()

        # Verify the result
        assert result is not None
