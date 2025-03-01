"""Unit tests for the base processor classes."""

import logging
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest

from consolidate_markdown.attachments.processor import (
    AttachmentMetadata,
    AttachmentProcessor,
)
from consolidate_markdown.cache import CacheManager
from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors.base import AttachmentHandlerMixin, SourceProcessor
from consolidate_markdown.processors.result import ProcessingResult


# Create a concrete implementation of AttachmentHandlerMixin for testing
class TestAttachmentHandler(AttachmentHandlerMixin):
    """Test implementation of AttachmentHandlerMixin."""

    def __init__(self):
        """Initialize test handler."""
        self.logger = logging.getLogger(__name__)

    @property
    def _processor_type(self) -> str:
        """Return processor type for testing."""
        return "test_handler"


# Create a concrete implementation of SourceProcessor for testing
class TestSourceProcessor(SourceProcessor):
    """Test implementation of SourceProcessor."""

    def __init__(
        self, source_config: SourceConfig, cache_manager: Optional[CacheManager] = None
    ):
        """Initialize the test source processor."""
        super().__init__(source_config, cache_manager)
        self.validate_called = False
        self.temp_dirs: List[Path] = []
        # Add limit attribute for testing
        self._limit = None

    def validate(self) -> None:
        """Validate source configuration."""
        self.validate_called = True
        # Check source directory exists and is readable
        if not self.source_config.src_dir.exists():
            raise ValueError(
                f"Source directory does not exist: {self.source_config.src_dir}"
            )

    def _process_impl(self, config: Config) -> ProcessingResult:
        """Process the source."""
        return ProcessingResult()

    def _apply_limit(self, items: List[Path]) -> List[Path]:
        """Apply limit to items."""
        if self._limit is None:
            return items
        return items[: self._limit]

    def _create_temp_dir(self, config: Config) -> Path:
        """Create a temporary directory."""
        temp_dir = super()._create_temp_dir(config)
        self.temp_dirs.append(temp_dir)
        return temp_dir

    def cleanup(self) -> None:
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            shutil.rmtree(temp_dir, ignore_errors=True)
        self.temp_dirs = []


@pytest.fixture
def attachment_handler() -> TestAttachmentHandler:
    """Create a test attachment handler."""
    return TestAttachmentHandler()


@pytest.fixture
def source_config(tmp_path: Path) -> SourceConfig:
    """Create a source configuration for testing."""
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True)

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir(parents=True)

    return SourceConfig(
        type="test",
        src_dir=src_dir,
        dest_dir=dest_dir,
        index_filename="index.md",
    )


@pytest.fixture
def global_config(tmp_path: Path) -> GlobalConfig:
    """Create a global configuration for testing."""
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir(parents=True, exist_ok=True)
    return GlobalConfig(
        cm_dir=cm_dir,
        log_level="INFO",
        force_generation=False,
        no_image=False,
        api_provider="openai",
        openai_key="test-key",
    )


@pytest.fixture
def cache_manager(tmp_path: Path) -> CacheManager:
    """Create a cache manager for testing."""
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir(parents=True, exist_ok=True)
    return CacheManager(cm_dir)


@pytest.fixture
def source_processor(
    source_config: SourceConfig, cache_manager: CacheManager
) -> TestSourceProcessor:
    """Create a test source processor."""
    return TestSourceProcessor(source_config, cache_manager)


def test_format_image_with_gpt(attachment_handler, tmp_path, global_config):
    """Test _format_image with GPT enabled."""
    # Create test image
    image_path = tmp_path / "test.jpg"
    image_path.write_bytes(b"fake image data")

    # Create metadata
    metadata = AttachmentMetadata(
        path=image_path,
        size=1024,
        dimensions=(100, 100),
        is_image=True,
    )

    # Create config with GPT enabled
    config = Config(global_config=global_config, sources=[])
    config.global_config.use_gpt = True
    result = ProcessingResult()

    # Mock GPT processor
    mock_gpt = MagicMock()
    mock_gpt.describe_image.return_value = "GPT description"

    # Format image
    with patch(
        "consolidate_markdown.processors.base.GPTProcessor", return_value=mock_gpt
    ):
        formatted = attachment_handler._format_image(
            image_path, metadata, config, result
        )

    # Check result
    assert "GPT description" in formatted
    assert "test.jpg" in formatted


def test_format_image_svg_with_png(attachment_handler, tmp_path, global_config):
    """Test _format_image with SVG and PNG conversion."""
    # Create test SVG
    svg_path = tmp_path / "test.svg"
    svg_path.write_text("<svg></svg>")

    # Create PNG conversion
    png_path = tmp_path / "test.png"
    png_path.write_bytes(b"fake png data")

    # Create metadata
    metadata = AttachmentMetadata(
        path=svg_path,
        size=1024,
        dimensions=(100, 100),
        is_image=True,
    )

    # Set PNG path in metadata
    metadata.png_path = png_path

    # Create config
    config = Config(global_config=global_config, sources=[])
    result = ProcessingResult()

    # Format image
    formatted = attachment_handler._format_image(svg_path, metadata, config, result)

    # Check result
    assert "test.svg" in formatted


def test_format_image_no_gpt(attachment_handler, tmp_path, global_config):
    """Test _format_image with GPT disabled."""
    # Create test image
    image_path = tmp_path / "test.jpg"
    image_path.write_bytes(b"fake image data")

    # Create metadata
    metadata = AttachmentMetadata(
        path=image_path,
        size=1024,
        dimensions=(100, 100),
        is_image=True,
    )

    # Create config with GPT disabled
    config = Config(global_config=global_config, sources=[])
    config.global_config.no_image = True
    result = ProcessingResult()

    # Format image
    formatted = attachment_handler._format_image(image_path, metadata, config, result)

    # Check result
    assert "test.jpg" in formatted


def test_format_image_gpt_error(attachment_handler, tmp_path, global_config):
    """Test _format_image handling GPT errors."""
    # Create test image
    image_path = tmp_path / "test.jpg"
    image_path.write_bytes(b"fake image data")

    # Create metadata
    metadata = AttachmentMetadata(
        path=image_path,
        size=1024,
        dimensions=(100, 100),
        is_image=True,
    )

    # Create config with GPT enabled
    config = Config(global_config=global_config, sources=[])
    config.global_config.use_gpt = True
    result = ProcessingResult()

    # Mock GPT processor that raises an exception
    mock_gpt = MagicMock()
    mock_gpt.describe_image.side_effect = Exception("GPT error")
    mock_gpt.get_placeholder.return_value = "Placeholder description"

    # Format image
    with patch(
        "consolidate_markdown.processors.base.GPTProcessor", return_value=mock_gpt
    ):
        formatted = attachment_handler._format_image(
            image_path, metadata, config, result
        )

    # Check result
    assert "test.jpg" in formatted
    assert "Placeholder description" in formatted


def test_format_document(attachment_handler, tmp_path):
    """Test _format_document method."""
    # Create test document
    doc_path = tmp_path / "test.pdf"
    doc_path.write_bytes(b"fake pdf data")

    # Create metadata
    metadata = AttachmentMetadata(
        path=doc_path,
        size=2048,
        dimensions=None,
        is_image=False,
    )

    # Format document
    formatted = attachment_handler._format_document(
        doc_path, metadata, alt_text="Test document"
    )

    # Check result
    assert "Test document" in formatted
    assert doc_path.name in formatted


def test_format_document_no_alt_text(attachment_handler, tmp_path):
    """Test _format_document without alt text."""
    # Create test document
    doc_path = tmp_path / "test.txt"
    doc_path.write_bytes(b"fake text data")

    # Create metadata
    metadata = AttachmentMetadata(
        path=doc_path,
        size=512,
        dimensions=None,
        is_image=False,
    )

    # Format document
    formatted = attachment_handler._format_document(doc_path, metadata)

    # Check result
    assert doc_path.name in formatted


def test_process_attachment(attachment_handler, tmp_path, global_config):
    """Test _process_attachment method."""
    # Create test attachment
    attachment_path = tmp_path / "test.txt"
    attachment_path.write_text("Test content")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create mock attachment processor
    mock_processor = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.is_image = False
    mock_processor.process_file.return_value = (attachment_path, mock_metadata)

    # Create config and result
    config = Config(global_config=global_config, sources=[])
    result = ProcessingResult()

    # Mock _format_document
    with patch.object(
        attachment_handler, "_format_document", return_value="Formatted document"
    ):
        # Process attachment
        formatted = attachment_handler._process_attachment(
            attachment_path,
            output_dir,
            mock_processor,
            config,
            result,
            alt_text="Test document",
            is_image=False,
        )

    # Check result
    assert formatted == "Formatted document"
    assert result.documents_processed == 1


def test_process_attachment_image(attachment_handler, tmp_path, global_config):
    """Test _process_attachment with image."""
    # Create test image
    attachment_path = tmp_path / "test.jpg"
    attachment_path.write_bytes(b"fake image data")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create mock attachment processor
    mock_processor = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.is_image = True
    mock_processor.process_file.return_value = (attachment_path, mock_metadata)

    # Create config and result
    config = Config(global_config=global_config, sources=[])
    result = ProcessingResult()

    # Mock _format_image
    with patch.object(
        attachment_handler, "_format_image", return_value="Formatted image"
    ):
        # Process attachment
        formatted = attachment_handler._process_attachment(
            attachment_path,
            output_dir,
            mock_processor,
            config,
            result,
            is_image=True,
        )

    # Check result
    assert formatted == "Formatted image"
    assert result.images_processed == 1


def test_process_attachment_nonexistent(attachment_handler, tmp_path, global_config):
    """Test _process_attachment with nonexistent file."""
    # Nonexistent attachment
    attachment_path = tmp_path / "nonexistent.txt"

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create config and result
    config = Config(global_config=global_config, sources=[])
    result = ProcessingResult()

    # Process attachment
    formatted = attachment_handler._process_attachment(
        attachment_path,
        output_dir,
        MagicMock(),
        config,
        result,
        is_image=False,
    )

    # Check result
    assert formatted is None


def test_process_attachment_exception(attachment_handler, tmp_path, global_config):
    """Test _process_attachment handling exceptions."""
    # Create test attachment
    attachment_path = tmp_path / "test.txt"
    attachment_path.write_text("Test content")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create mock attachment processor that raises exception
    mock_processor = MagicMock()
    mock_processor.process_file.side_effect = Exception("Processing error")

    # Create config and result
    config = Config(global_config=global_config, sources=[])
    result = ProcessingResult()

    # Process attachment
    formatted = attachment_handler._process_attachment(
        attachment_path,
        output_dir,
        mock_processor,
        config,
        result,
        is_image=False,
    )

    # Check result
    assert formatted is None
    assert result.documents_skipped == 1


def test_process_attachment_with_progress(attachment_handler, tmp_path, global_config):
    """Test _process_attachment with progress tracking."""
    # Create test attachment
    attachment_path = tmp_path / "test.txt"
    attachment_path.write_text("Test content")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create mock attachment processor
    mock_processor = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.is_image = False
    mock_processor.process_file.return_value = (attachment_path, mock_metadata)

    # Create config and result
    config = Config(global_config=global_config, sources=[])
    result = ProcessingResult()

    # Create mock progress
    mock_progress = MagicMock()
    mock_task_id = 1

    # Mock _format_document
    with patch.object(
        attachment_handler, "_format_document", return_value="Formatted document"
    ):
        # Process attachment with progress
        formatted = attachment_handler._process_attachment(
            attachment_path,
            output_dir,
            mock_processor,
            config,
            result,
            alt_text="Test document",
            is_image=False,
            progress=mock_progress,
            task_id=mock_task_id,
        )

    # Check result
    assert formatted == "Formatted document"
    mock_progress.advance.assert_called_once_with(mock_task_id)


def test_source_processor_initialization(source_config, cache_manager):
    """Test SourceProcessor initialization."""
    processor = TestSourceProcessor(source_config, cache_manager)

    # Check properties
    assert processor.source_config == source_config
    assert processor.cache_manager == cache_manager
    assert processor._attachment_processor is None


def test_source_processor_attachment_processor(source_processor):
    """Test attachment_processor property."""
    # First access should create the processor
    processor = source_processor.attachment_processor
    assert processor is not None
    assert isinstance(processor, AttachmentProcessor)

    # Second access should return the same instance
    assert source_processor.attachment_processor is processor


def test_source_processor_set_progress(source_processor):
    """Test set_progress method."""
    mock_progress = MagicMock()
    mock_task_id = 1

    # Set progress
    source_processor.set_progress(mock_progress, mock_task_id)

    # Check properties
    assert source_processor._progress == mock_progress
    assert source_processor._task_id == mock_task_id


def test_source_processor_processor_type(source_processor):
    """Test _processor_type property."""
    assert source_processor._processor_type == "test"


def test_source_processor_validate(source_processor):
    """Test validate method."""
    # Should not raise any exceptions
    source_processor.validate()

    # Create a temporary directory that doesn't exist
    nonexistent_dir = Path("/tmp/nonexistent_" + str(uuid.uuid4()))

    # Test with invalid source_config
    invalid_config = SourceConfig(
        type="invalid",
        src_dir=nonexistent_dir,
        dest_dir=nonexistent_dir,
    )

    # Create a new processor instance without calling validate
    processor = TestSourceProcessor.__new__(TestSourceProcessor)
    processor.source_config = invalid_config
    processor.validate_called = False
    processor.temp_dirs = []

    # Now manually trigger validation to check the error
    with pytest.raises(ValueError, match="Source directory does not exist"):
        processor.validate()


def test_source_processor_ensure_dest_dir(source_processor):
    """Test _ensure_dest_dir method."""
    # Remove dest_dir
    shutil.rmtree(source_processor.source_config.dest_dir)
    assert not source_processor.source_config.dest_dir.exists()

    # Ensure dest_dir
    source_processor._ensure_dest_dir()

    # Check that dest_dir was created
    assert source_processor.source_config.dest_dir.exists()
    assert source_processor.source_config.dest_dir.is_dir()


def test_source_processor_normalize_path(source_processor):
    """Test _normalize_path method."""
    # Test with absolute path
    path = Path("/absolute/path")
    normalized = source_processor._normalize_path(path)
    assert normalized == path

    # Test with relative path
    path = Path("relative/path")
    normalized = source_processor._normalize_path(path)
    assert normalized == path


def test_source_processor_create_temp_dir(source_processor, global_config):
    """Test _create_temp_dir method."""
    config = Config(global_config=global_config, sources=[])

    # Create temp dir
    temp_dir = source_processor._create_temp_dir(config)

    # Check that temp dir was created
    assert temp_dir.exists()
    assert temp_dir.is_dir()
    assert temp_dir.name == "temp"

    # Cleanup
    source_processor._cleanup_temp_dir()


def test_source_processor_cleanup_temp_dir(source_processor, global_config):
    """Test _cleanup_temp_dir method."""
    config = Config(global_config=global_config, sources=[])

    # Create temp dir
    temp_dir = source_processor._create_temp_dir(config)
    assert temp_dir.exists()

    # Cleanup
    source_processor._cleanup_temp_dir()

    # Check that temp dir was removed
    assert not temp_dir.exists()


def test_source_processor_apply_limit(source_processor):
    """Test _apply_limit method."""
    # Create test items
    items = [Path(f"item_{i}") for i in range(10)]

    # Test with no limit
    source_processor._limit = None
    limited_items = source_processor._apply_limit(items)
    assert limited_items == items

    # Test with limit
    source_processor._limit = 5
    limited_items = source_processor._apply_limit(items)
    assert len(limited_items) == 5
    assert all(item in items for item in limited_items)


def test_source_processor_process(source_processor, global_config):
    """Test process method."""
    config = Config(global_config=global_config, sources=[])

    # Mock _process_impl
    with patch.object(
        source_processor, "_process_impl", return_value=ProcessingResult()
    ) as mock_process_impl:
        # Process
        result = source_processor.process(config)

        # Check that _process_impl was called
        mock_process_impl.assert_called_once_with(config)

        # Check result
        assert isinstance(result, ProcessingResult)


def test_source_processor_process_with_progress(source_processor, global_config):
    """Test process method with progress tracking."""
    config = Config(global_config=global_config, sources=[])

    # Create mock progress
    mock_progress = MagicMock()
    mock_task_id = 1
    source_processor.set_progress(mock_progress, mock_task_id)

    # Define a side effect that advances progress
    def process_impl_with_progress(config):
        source_processor._progress.advance(source_processor._task_id)
        return ProcessingResult()

    # Mock _process_impl
    with patch.object(
        source_processor, "_process_impl", side_effect=process_impl_with_progress
    ) as mock_process_impl:
        # Process
        source_processor.process(config)

        # Check that _process_impl was called
        mock_process_impl.assert_called_once_with(config)

        # Check that progress was advanced
        mock_progress.advance.assert_called_once_with(mock_task_id)


def test_source_processor_cleanup(source_processor, global_config):
    """Test cleanup method."""
    config = Config(global_config=global_config, sources=[])

    # Create temp dir
    temp_dir = source_processor._create_temp_dir(config)
    assert temp_dir.exists()

    # Mock shutil.rmtree to avoid actually removing the directory
    with patch("shutil.rmtree") as mock_rmtree:
        # Cleanup
        source_processor.cleanup()

        # Check that rmtree was called with the temp dir
        mock_rmtree.assert_called_once_with(temp_dir, ignore_errors=True)


def test_source_processor_del(source_processor, global_config):
    """Test __del__ method."""
    config = Config(global_config=global_config, sources=[])

    # Create temp dir
    temp_dir = source_processor._create_temp_dir(config)
    assert temp_dir.exists()

    # Mock cleanup method
    with patch.object(source_processor, "cleanup") as mock_cleanup:
        # Call __del__
        source_processor.__del__()

        # Check that cleanup was called
        mock_cleanup.assert_called_once()
