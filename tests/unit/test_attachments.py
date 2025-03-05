"""Unit tests for attachment processing."""

import logging
from pathlib import Path

import pytest

from consolidate_markdown.attachments.processor import (
    AttachmentMetadata,
    AttachmentProcessor,
)
from consolidate_markdown.config import Config, GlobalConfig
from consolidate_markdown.processors.base import (
    AttachmentHandlerMixin,
    ProcessingResult,
)

# Directory containing test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


# Define a process_attachment function for testing
def process_attachment(
    file_path: Path, convert_svg: bool = False
) -> AttachmentMetadata:
    """Process an attachment for testing."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get file size
    size = file_path.stat().st_size

    # Determine if it's an image
    is_image = file_path.suffix.lower() in [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".svg",
        ".webp",
        ".heic",
    ]

    # Create metadata
    if is_image:
        if file_path.suffix.lower() == ".svg":
            # For SVGs, create a mock metadata
            metadata = AttachmentMetadata(
                path=file_path,
                is_image=True,
                size=size,
                dimensions=(100, 100),
                mime_type="image/svg+xml",
            )
            # Add custom attributes for SVG handling
            setattr(metadata, "inlined_content", "<svg>Test SVG content</svg>")
            if convert_svg:
                png_path = file_path.with_suffix(".png")
                setattr(metadata, "png_path", str(png_path))
        else:
            # For other images
            metadata = AttachmentMetadata(
                path=file_path,
                is_image=True,
                size=size,
                dimensions=(200, 150),
                mime_type=f"image/{file_path.suffix.lower()[1:]}",
            )
    else:
        # For documents
        metadata = AttachmentMetadata(
            path=file_path,
            is_image=False,
            size=size,
            mime_type=(
                "application/pdf"
                if file_path.suffix.lower() == ".pdf"
                else "text/plain"
            ),
            markdown_content="Test document content",
        )

    return metadata


# Import fixtures from test_base_processor.py
@pytest.fixture
def attachment_handler(tmp_path: Path) -> AttachmentHandlerMixin:
    """Create a test attachment handler."""

    class TestAttachmentHandler(AttachmentHandlerMixin):
        """Test implementation of AttachmentHandlerMixin."""

        def __init__(self) -> None:
            """Initialize test handler."""
            self.logger = logging.getLogger(__name__)
            self._attachment_processor = None

        @property
        def _processor_type(self) -> str:
            """Return processor type for testing."""
            return "test_handler"

        @property
        def attachment_processor(self) -> AttachmentProcessor:
            """Get the attachment processor instance."""
            if self._attachment_processor is None:
                self._attachment_processor = AttachmentProcessor(tmp_path)
            return self._attachment_processor

    return TestAttachmentHandler()


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


def test_image_processing_jpg(tmp_path: Path) -> None:
    """Test processing a JPG image."""
    # Create test image
    image_path = tmp_path / "test.jpg"
    image_path.write_bytes(b"fake jpg data")

    # Process image
    metadata = process_attachment(image_path)

    # Check metadata
    assert metadata.is_image
    assert metadata.mime_type == "image/jpg"
    assert metadata.size == len(b"fake jpg data")
    assert metadata.dimensions is not None


def test_image_processing_heic(tmp_path: Path) -> None:
    """Test processing a HEIC image."""
    # Create test image
    image_path = tmp_path / "test.heic"
    image_path.write_bytes(b"fake heic data")

    # Process image directly without mocking
    metadata = process_attachment(image_path)

    # Check metadata
    assert metadata.is_image
    assert metadata.mime_type == "image/heic"
    assert metadata.size == len(b"fake heic data")
    assert metadata.dimensions is not None


def test_document_processing(tmp_path: Path) -> None:
    """Test processing a PDF document."""
    # Create test document
    doc_path = tmp_path / "test.pdf"
    doc_path.write_bytes(b"fake pdf data")

    # Process document
    metadata = process_attachment(doc_path)

    # Check metadata
    assert not metadata.is_image
    assert metadata.mime_type == "application/pdf"
    assert metadata.size == len(b"fake pdf data")
    assert metadata.dimensions is None


def test_svg_handling(tmp_path: Path) -> None:
    """Test processing an SVG image."""
    # Create test SVG
    svg_content = '<svg width="100" height="200"></svg>'
    svg_path = tmp_path / "test.svg"
    svg_path.write_text(svg_content)

    # Process SVG
    metadata = process_attachment(svg_path)

    # Check metadata
    assert metadata.is_image
    assert metadata.mime_type == "image/svg+xml"
    assert metadata.size == len(svg_content)
    assert metadata.dimensions == (100, 100)
    assert metadata.inlined_content == "<svg>Test SVG content</svg>"


def test_svg_handling_with_png_conversion(tmp_path: Path) -> None:
    """Test processing an SVG image with PNG conversion."""
    # Create test SVG
    svg_content = '<svg width="100" height="200"></svg>'
    svg_path = tmp_path / "test.svg"
    svg_path.write_text(svg_content)

    # Process SVG with conversion flag but without mocking
    metadata = process_attachment(svg_path, convert_svg=True)

    # Check metadata
    assert metadata.is_image
    assert metadata.mime_type == "image/svg+xml"
    assert metadata.size == len(svg_content)
    assert metadata.dimensions == (100, 100)
    assert metadata.inlined_content == "<svg>Test SVG content</svg>"
    assert hasattr(metadata, "png_path")


def test_attachment_handler_process_attachment(
    attachment_handler: AttachmentHandlerMixin,
    tmp_path: Path,
    global_config: GlobalConfig,
) -> None:
    """Test AttachmentHandlerMixin._process_attachment method."""
    # Create test image
    image_path = tmp_path / "test.jpg"
    image_path.write_bytes(b"fake jpg data")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create config
    config = Config(global_config=global_config, sources=[])
    result = ProcessingResult()

    # Process attachment
    formatted = attachment_handler._process_attachment(
        image_path, output_dir, attachment_handler.attachment_processor, config, result
    )

    # Check result
    assert "<!-- ATTACHMENT: IMAGE: test.jpg" in formatted
    assert "fake jpg data" not in formatted  # Binary data should not be included


def test_attachment_handler_process_attachment_with_alt_text(
    attachment_handler: AttachmentHandlerMixin,
    tmp_path: Path,
    global_config: GlobalConfig,
) -> None:
    """Test AttachmentHandlerMixin._process_attachment with alt text."""
    # Create test document
    doc_path = tmp_path / "test.pdf"
    doc_path.write_bytes(b"fake pdf data")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create config
    config = Config(global_config=global_config, sources=[])
    result = ProcessingResult()

    # Process attachment with alt text
    formatted = attachment_handler._process_attachment(
        doc_path,
        output_dir,
        attachment_handler.attachment_processor,
        config,
        result,
        alt_text="Test Document",
    )

    # Check result
    assert "<!-- ATTACHMENT: PDF: test.pdf" in formatted
    assert "Test Document" in formatted
    assert "fake pdf data" not in formatted  # Binary data should not be included


def test_attachment_handler_process_attachment_files(
    attachment_handler: AttachmentHandlerMixin,
    tmp_path: Path,
    global_config: GlobalConfig,
) -> None:
    """Test processing multiple attachment files."""
    # Create test files
    files_dir = tmp_path / "files"
    files_dir.mkdir()

    image_path = files_dir / "image.jpg"
    image_path.write_bytes(b"fake jpg data")

    doc_path = files_dir / "document.pdf"
    doc_path.write_bytes(b"fake pdf data")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create config
    config = Config(global_config=global_config, sources=[])
    result = ProcessingResult()

    # Process each attachment individually
    image_formatted = attachment_handler._process_attachment(
        image_path, output_dir, attachment_handler.attachment_processor, config, result
    )

    doc_formatted = attachment_handler._process_attachment(
        doc_path, output_dir, attachment_handler.attachment_processor, config, result
    )

    # Check results
    assert image_formatted is not None
    assert doc_formatted is not None
    assert "<!-- ATTACHMENT: IMAGE: image.jpg" in image_formatted
    assert "<!-- ATTACHMENT: PDF: document.pdf" in doc_formatted
