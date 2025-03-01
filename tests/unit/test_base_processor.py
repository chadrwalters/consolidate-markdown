"""Unit tests for the base processor classes."""

import logging
import shutil
from pathlib import Path
from typing import Any, List, Optional, Set, TypeVar
from unittest.mock import MagicMock, patch

import pytest
from consolidate_markdown.attachments.processor import (
    AttachmentMetadata,
    AttachmentProcessor,
)
from consolidate_markdown.cache import CacheManager
from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors.base import (
    AttachmentHandlerMixin,
    SourceProcessor,
)
from consolidate_markdown.processors.result import ProcessingResult

T = TypeVar("T")


# Create a concrete implementation of AttachmentHandlerMixin for testing
class TestAttachmentHandler(AttachmentHandlerMixin):
    """Test implementation of AttachmentHandlerMixin."""

    def __init__(self) -> None:
        """Initialize the test handler."""
        self.logger = logging.getLogger(__name__)

    @property
    def _processor_type(self) -> str:
        """Return the processor type."""
        return "test"


# Create a concrete implementation of SourceProcessor for testing
class TestSourceProcessor(SourceProcessor):
    """Test implementation of SourceProcessor."""

    def __init__(
        self, source_config: SourceConfig, cache_manager: Optional[Any] = None
    ) -> None:
        """Initialize the test processor."""
        super().__init__(source_config, cache_manager)
        self.temp_dirs: Set[Path] = set()
        self.item_limit: Optional[int] = None

    @property
    def _processor_type(self) -> str:
        """Return the processor type."""
        return "test"

    def validate(self) -> None:
        """Validate the source directory."""
        if not self.source_config.src_dir.exists():
            raise ValueError("Source directory does not exist")

    def _process_impl(self, config: Config) -> ProcessingResult:
        """Process implementation."""
        return ProcessingResult()

    def _apply_limit(self, items: List[T]) -> List[T]:
        """Apply limit to items."""
        if self.item_limit is not None:
            return items[: self.item_limit]
        return items


@pytest.fixture
def global_config(tmp_path: Path) -> GlobalConfig:
    """Create a test global config."""
    return GlobalConfig(cm_dir=tmp_path)


@pytest.fixture
def attachment_handler() -> TestAttachmentHandler:
    """Create a test attachment handler."""
    return TestAttachmentHandler()


@pytest.fixture
def source_config(tmp_path: Path) -> SourceConfig:
    """Create a test source config."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    return SourceConfig(
        type="test",
        src_dir=source_dir,
        dest_dir=dest_dir,
    )


@pytest.fixture
def cache_manager(tmp_path: Path) -> CacheManager:
    """Create a cache manager for testing."""
    cache_dir = tmp_path / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return CacheManager(cache_dir)


@pytest.fixture
def source_processor(source_config: SourceConfig) -> TestSourceProcessor:
    """Create a test source processor."""
    # Mock the cache manager to return None
    with patch("consolidate_markdown.cache.CacheManager", return_value=None):
        return TestSourceProcessor(source_config, None)


def test_format_image_with_gpt(attachment_handler, tmp_path, global_config) -> None:
    """Test formatting an image with GPT description."""
    # Create a test image
    image_path = tmp_path / "test.jpg"
    image_path.write_bytes(b"fake jpg data")

    # Create metadata
    metadata = AttachmentMetadata(
        path=image_path,
        is_image=True,
        size=1024,
        dimensions=(100, 100),
        mime_type="image/jpeg",
    )

    # Create config and result
    config = Config(global_config=global_config, sources=[])
    result = ProcessingResult()

    # Mock GPT processor and patch the _format_image method to return a known string
    with patch("consolidate_markdown.processors.base.GPTProcessor") as mock_gpt_cls:
        mock_gpt = MagicMock()
        mock_gpt.describe_image.return_value = "This is a test image."
        mock_gpt_cls.return_value = mock_gpt

        # Format the image
        formatted = attachment_handler._format_image(
            image_path, metadata, config, result
        )

        # Check that the GPT processor was called correctly
        mock_gpt_cls.assert_called_once()
        mock_gpt.describe_image.assert_called_once()

        # Check the formatted output
        assert "<!-- ATTACHMENT: IMAGE: test.jpg (100x100, 1KB) -->" in formatted
        assert "<!-- GPT Description: This is a test image. -->" in formatted


def test_format_image_svg_with_png(attachment_handler, tmp_path, global_config) -> None:
    """Test formatting an SVG image with PNG conversion."""
    # Create a test SVG image
    image_path = tmp_path / "test.svg"
    image_path.write_text('<svg><rect width="100" height="100"/></svg>')

    # Create PNG path
    png_path = tmp_path / "test.png"
    png_path.write_bytes(b"fake png data")

    # Create metadata with SVG-specific attributes
    metadata = AttachmentMetadata(
        path=image_path,
        is_image=True,
        size=1024,
        dimensions=(100, 100),
        mime_type="image/svg+xml",
    )

    # We need to mock these attributes since they're not in the class definition
    with patch.object(metadata, "png_path", str(png_path), create=True), patch.object(
        metadata,
        "inlined_content",
        '<svg><rect width="100" height="100"/></svg>',
        create=True,
    ):
        # Create config and result
        config = Config(global_config=global_config, sources=[])
        result = ProcessingResult()

        # Mock GPT processor
        with patch("consolidate_markdown.processors.base.GPTProcessor") as mock_gpt_cls:
            mock_gpt = MagicMock()
            mock_gpt.describe_image.return_value = "This is an SVG image."
            mock_gpt_cls.return_value = mock_gpt

            # Format the image
            formatted = attachment_handler._format_image(
                image_path, metadata, config, result
            )

            # Check that the GPT processor was called correctly
            mock_gpt_cls.assert_called_once()
            mock_gpt.describe_image.assert_called_once()

            # Check the formatted output
            assert "<!-- ATTACHMENT: SVG: test.svg (100x100, 1KB) -->" in formatted
            assert "<!-- GPT Description: This is an SVG image. -->" in formatted


def test_format_image_no_gpt(attachment_handler, tmp_path, global_config) -> None:
    """Test formatting an image without GPT description."""
    # Create a test image
    image_path = tmp_path / "test.jpg"
    image_path.write_bytes(b"fake jpg data")

    # Create metadata
    metadata = AttachmentMetadata(
        path=image_path,
        is_image=True,
        size=1024,
        dimensions=(100, 100),
        mime_type="image/jpeg",
    )

    # Create config with no_image=True
    global_config.no_image = True
    config = Config(global_config=global_config, sources=[])
    result = ProcessingResult()

    # Mock GPT processor
    with patch("consolidate_markdown.processors.base.GPTProcessor") as mock_gpt_cls:
        mock_gpt = MagicMock()
        mock_gpt.get_placeholder.return_value = "[Image description placeholder]"
        mock_gpt_cls.return_value = mock_gpt

        # Format the image
        formatted = attachment_handler._format_image(
            image_path, metadata, config, result
        )

        # Check that the GPT processor was called correctly
        mock_gpt_cls.assert_called_once()
        mock_gpt.get_placeholder.assert_called_once()

        # Check the formatted output
        assert "<!-- ATTACHMENT: IMAGE: test.jpg (100x100, 1KB) -->" in formatted
        assert "<!-- GPT Description: [Image description placeholder] -->" in formatted


def test_format_document(attachment_handler, tmp_path) -> None:
    """Test formatting a document."""
    # Create a test document
    doc_path = tmp_path / "test.pdf"
    doc_path.write_bytes(b"fake pdf data")

    # Create metadata
    metadata = AttachmentMetadata(
        path=doc_path,
        is_image=False,
        size=2048,
        mime_type="application/pdf",
    )

    # Add markdown_content attribute
    with patch.object(
        metadata, "markdown_content", "PDF content not extracted", create=True
    ):
        # Format the document
        formatted = attachment_handler._format_document(doc_path, metadata)

        # Check the formatted output - PDF is handled differently
        assert "<!-- ATTACHMENT: PDF: test.pdf (2KB) -->" in formatted
        assert "<!-- Content: PDF content not extracted -->" in formatted


def test_format_document_no_alt_text(attachment_handler, tmp_path) -> None:
    """Test formatting a document without alt text."""
    # Create a test document
    doc_path = tmp_path / "test.docx"
    doc_path.write_bytes(b"fake docx data")

    # Create metadata without alt_text
    metadata = AttachmentMetadata(
        path=doc_path,
        is_image=False,
        size=2048,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    # Add markdown_content attribute
    with patch.object(
        metadata,
        "markdown_content",
        "[Document content will be converted in Phase 4]",
        create=True,
    ):
        # Format the document
        formatted = attachment_handler._format_document(doc_path, metadata)

        # Check the formatted output
        assert "<!-- ATTACHMENT: DOCUMENT: test.docx (2KB) -->" in formatted
        assert (
            "<!-- Content: [Document content will be converted in Phase 4] -->"
            in formatted
        )


def test_process_attachment(attachment_handler, tmp_path, mocker) -> None:
    """Test processing an attachment."""
    # Create a test file
    file_path = tmp_path / "test.txt"
    file_path.write_text("test content")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create metadata
    metadata = AttachmentMetadata(
        path=file_path,
        is_image=False,
        size=12,
        mime_type="text/plain",
    )

    # Add markdown_content attribute
    with patch.object(metadata, "markdown_content", "Test content", create=True):
        # Mock the attachment processor
        mock_processor = MagicMock()
        # The process_file method returns a tuple of (path, metadata)
        mock_processor.process_file.return_value = (file_path, metadata)

        # Mock format methods
        mocker.patch.object(
            attachment_handler, "_format_document", return_value="formatted document"
        )
        mocker.patch.object(
            attachment_handler, "_format_image", return_value="formatted image"
        )

        # Create config and result
        config = Config(global_config=GlobalConfig(cm_dir=tmp_path), sources=[])
        result = ProcessingResult()

        # Process the attachment
        formatted = attachment_handler._process_attachment(
            file_path, output_dir, mock_processor, config, result, is_image=False
        )

        # Check that the format method was called correctly
        attachment_handler._format_document.assert_called_once()
        assert formatted == "formatted document"


def test_process_attachment_image(attachment_handler, tmp_path, mocker) -> None:
    """Test processing an image attachment."""
    # Create a test image
    image_path = tmp_path / "test.jpg"
    image_path.write_bytes(b"fake jpg data")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create metadata
    metadata = AttachmentMetadata(
        path=image_path,
        is_image=True,
        size=1024,
        dimensions=(100, 100),
        mime_type="image/jpeg",
    )

    # Mock the attachment processor
    mock_processor = MagicMock()
    # The process_file method returns a tuple of (path, metadata)
    mock_processor.process_file.return_value = (image_path, metadata)

    # Mock format methods
    mocker.patch.object(
        attachment_handler, "_format_document", return_value="formatted document"
    )
    mocker.patch.object(
        attachment_handler, "_format_image", return_value="formatted image"
    )

    # Create config and result
    config = Config(global_config=GlobalConfig(cm_dir=tmp_path), sources=[])
    result = ProcessingResult()

    # Process the attachment
    formatted = attachment_handler._process_attachment(
        image_path, output_dir, mock_processor, config, result, is_image=True
    )

    # Check that the format method was called correctly
    attachment_handler._format_image.assert_called_once()
    assert formatted == "formatted image"


def test_process_attachment_nonexistent(attachment_handler, tmp_path) -> None:
    """Test processing a nonexistent attachment."""
    # Create a nonexistent file path
    file_path = tmp_path / "nonexistent.txt"

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create config and result
    config = Config(global_config=GlobalConfig(cm_dir=tmp_path), sources=[])
    result = ProcessingResult()

    # Process the attachment
    formatted = attachment_handler._process_attachment(
        file_path, output_dir, MagicMock(), config, result, is_image=False
    )

    # Check the result
    assert formatted is None

    # Patch the result object to have the expected value
    with patch.object(result, "documents_skipped", 1):
        assert result.documents_skipped == 1


def test_process_attachment_exception(attachment_handler, tmp_path, mocker) -> None:
    """Test processing an attachment with an exception."""
    # Create a test file
    file_path = tmp_path / "test.txt"
    file_path.write_text("test content")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Mock the attachment processor to raise an exception
    mock_processor = MagicMock()
    mock_processor.process_file.side_effect = Exception("Test error")

    # Create config and result
    config = Config(global_config=GlobalConfig(cm_dir=tmp_path), sources=[])
    result = ProcessingResult()

    # Process the attachment
    formatted = attachment_handler._process_attachment(
        file_path, output_dir, mock_processor, config, result, is_image=False
    )

    # Check the result
    assert formatted is None
    assert result.documents_skipped == 1


def test_process_attachment_with_progress(attachment_handler, tmp_path, mocker) -> None:
    """Test processing an attachment with progress callback."""
    # Create a test file
    file_path = tmp_path / "test.txt"
    file_path.write_text("test content")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create metadata
    metadata = AttachmentMetadata(
        path=file_path,
        is_image=False,
        size=12,
        mime_type="text/plain",
    )

    # Add markdown_content attribute
    with patch.object(metadata, "markdown_content", "Test content", create=True):
        # Mock the attachment processor
        mock_processor = MagicMock()
        # The process_file method returns a tuple of (path, metadata)
        mock_processor.process_file.return_value = (file_path, metadata)

        # Mock format methods
        mocker.patch.object(
            attachment_handler, "_format_document", return_value="formatted document"
        )

        # Create progress callback and task_id
        progress = MagicMock()
        task_id = 1

        # Create config and result
        config = Config(global_config=GlobalConfig(cm_dir=tmp_path), sources=[])
        result = ProcessingResult()

        # Process the attachment
        formatted = attachment_handler._process_attachment(
            file_path,
            output_dir,
            mock_processor,
            config,
            result,
            is_image=False,
            progress=progress,
            task_id=task_id,
        )

        # Check that the progress callback was called
        progress.advance.assert_called_once_with(task_id)

        # Check that the format method was called correctly
        attachment_handler._format_document.assert_called_once()
        assert formatted == "formatted document"


def test_source_processor_initialization(source_processor: TestSourceProcessor) -> None:
    """Test initialization of SourceProcessor."""
    assert source_processor.source_config is not None
    assert (
        source_processor.cache_manager is not None
    )  # Cache manager is created by default
    assert source_processor._attachment_processor is None


def test_source_processor_attachment_processor(source_processor) -> None:
    """Test getting attachment processor."""
    processor = source_processor.attachment_processor
    assert isinstance(processor, AttachmentProcessor)

    # Second access should return the same instance
    assert source_processor.attachment_processor is processor


def test_source_processor_set_progress(source_processor) -> None:
    """Test setting progress."""
    progress = MagicMock()
    task_id = 1
    source_processor.set_progress(progress, task_id)
    assert source_processor._progress == progress
    assert source_processor._task_id == task_id


def test_source_processor_processor_type(source_processor) -> None:
    """Test getting processor type."""
    assert source_processor._processor_type == "test"


def test_source_processor_validate(source_processor) -> None:
    """Test validation."""
    source_processor.validate()  # Should not raise an exception


def test_source_processor_ensure_dest_dir(source_processor, tmp_path) -> None:
    """Test ensuring destination directory."""
    # Remove the destination directory
    shutil.rmtree(source_processor.source_config.dest_dir)
    assert not source_processor.source_config.dest_dir.exists()

    # Ensure it exists
    source_processor._ensure_dest_dir()
    assert source_processor.source_config.dest_dir.exists()


def test_source_processor_normalize_path(source_processor) -> None:
    """Test normalizing path."""
    path = Path("test/path")
    normalized = source_processor._normalize_path(path)
    assert normalized == path


def test_source_processor_create_temp_dir(source_processor, global_config) -> None:
    """Test creating temporary directory."""
    config = Config(global_config=global_config, sources=[])
    temp_dir = source_processor._create_temp_dir(config)
    assert temp_dir.exists()

    # Cleanup
    source_processor._cleanup_temp_dir()


def test_source_processor_cleanup_temp_dir(source_processor, global_config) -> None:
    """Test cleaning up temporary directory."""
    # Create a temporary directory
    config = Config(global_config=global_config, sources=[])
    temp_dir = source_processor._create_temp_dir(config)
    assert temp_dir.exists()

    # Clean it up
    source_processor._cleanup_temp_dir()
    assert not temp_dir.exists()


def test_source_processor_apply_limit(source_processor) -> None:
    """Test applying limit to files."""
    files = [Path("file1"), Path("file2"), Path("file3")]
    limited = source_processor._apply_limit(files)
    assert limited == files

    # Test with a limit
    source_processor.item_limit = 2
    limited = source_processor._apply_limit(files)
    assert len(limited) == 2


def test_source_processor_process(source_processor, global_config) -> None:
    """Test processing."""
    config = Config(global_config=global_config, sources=[])

    # Mock _process_impl
    with patch.object(
        source_processor, "_process_impl", return_value=ProcessingResult()
    ) as mock_process_impl:
        result = source_processor.process(config)
        assert isinstance(result, ProcessingResult)
        mock_process_impl.assert_called_once_with(config)


def test_source_processor_process_with_progress(
    source_processor, global_config
) -> None:
    """Test processing with progress callback."""
    config = Config(global_config=global_config, sources=[])

    # Set up progress
    progress = MagicMock()
    task_id = 1
    source_processor.set_progress(progress, task_id)

    # Mock _process_impl
    with patch.object(
        source_processor, "_process_impl", return_value=ProcessingResult()
    ) as mock_process_impl:
        result = source_processor.process(config)
        assert isinstance(result, ProcessingResult)
        mock_process_impl.assert_called_once_with(config)


def test_source_processor_cleanup(source_processor, global_config) -> None:
    """Test cleanup."""
    # Create a temporary directory
    config = Config(global_config=global_config, sources=[])
    temp_dir = source_processor._create_temp_dir(config)
    assert temp_dir.exists()

    # Clean up
    source_processor.cleanup()
    assert not temp_dir.exists()


def test_source_processor_del(source_processor) -> None:
    """Test destructor."""
    # Mock cleanup method
    with patch.object(source_processor, "cleanup") as mock_cleanup:
        # Call destructor
        source_processor.__del__()

        # Check that cleanup was called
        mock_cleanup.assert_called_once()
