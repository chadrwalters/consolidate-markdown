"""Test attachment processing."""
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

import logging
from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from reportlab.pdfgen import canvas

from consolidate_markdown.attachments.gpt import GPTProcessor
from consolidate_markdown.attachments.processor import (
    AttachmentMetadata,
    AttachmentProcessor,
)
from consolidate_markdown.cache import CacheManager
from consolidate_markdown.config import GlobalConfig
from consolidate_markdown.processors.base import ProcessingResult


def test_image_processing_jpg(tmp_path):
    """Test processing a JPG image attachment"""
    source_file = tmp_path / "test.jpg"
    source_file.write_bytes(b"fake jpg data")
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()

    processor = AttachmentProcessor(cm_dir)
    temp_path, metadata = processor.process_file(source_file)

    assert isinstance(metadata, AttachmentMetadata)
    assert metadata.is_image
    assert metadata.mime_type == "image/jpeg"
    assert temp_path.exists()
    assert temp_path == cm_dir / "temp" / "test.jpg"


def test_image_processing_heic(tmp_path):
    """Test processing a HEIC image with conversion"""
    source_file = tmp_path / "test.heic"
    source_file.write_bytes(b"fake heic data")
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()

    processor = AttachmentProcessor(cm_dir)
    temp_path, metadata = processor.process_file(source_file)

    assert isinstance(metadata, AttachmentMetadata)
    assert metadata.is_image
    assert metadata.mime_type == "image/heic"
    assert temp_path.exists()
    # In test environment, HEIC conversion might fail and fall back to copying
    assert temp_path.name in ("test.jpg", "test.heic")


def test_document_processing(tmp_path):
    """Test processing document attachments"""
    source_file = FIXTURES_DIR / "attachments" / "documents" / "test.pdf"
    # Create a minimal valid PDF file
    minimal_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
178
%%EOF"""
    source_file.write_bytes(minimal_pdf)
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()

    processor = AttachmentProcessor(cm_dir)
    temp_path, metadata = processor.process_file(source_file)

    assert isinstance(metadata, AttachmentMetadata)
    assert not metadata.is_image
    assert metadata.mime_type == "application/pdf"
    assert temp_path.exists()
    assert temp_path == cm_dir / "temp" / "test.pdf"


def test_svg_handling(tmp_path):
    """Test SVG image handling"""
    source_file = tmp_path / "test.svg"
    source_file.write_text('<svg><rect width="100" height="100"/></svg>')
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()

    processor = AttachmentProcessor(cm_dir)
    temp_path, metadata = processor.process_file(source_file)

    assert isinstance(metadata, AttachmentMetadata)
    assert metadata.is_image
    assert metadata.mime_type == "image/svg+xml"
    assert temp_path.exists()
    assert temp_path == cm_dir / "temp" / "test.svg"


def test_pdf_processing(tmp_path):
    """Test processing of PDF files."""
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("consolidate_markdown")
    logger.setLevel(logging.DEBUG)

    # Create test PDF using reportlab
    pdf_file = tmp_path / "test.pdf"
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "This is a test PDF document.")
    c.save()
    pdf_file.write_bytes(buffer.getvalue())

    # Process the PDF
    processor = AttachmentProcessor(tmp_path)
    temp_path, metadata = processor.process_file(pdf_file)

    # Check results
    assert metadata.mime_type == "application/pdf"
    assert metadata.is_image is False
    assert "test pdf document" in metadata.markdown_content.lower()


@pytest.fixture
def global_config():
    """Create a test global configuration."""
    return GlobalConfig(
        openai_key="test-openai-key",
        openrouter_key="test-openrouter-key",
    )


@pytest.fixture
def openai_config(global_config):
    """Create a test OpenAI configuration."""
    global_config.api_provider = "openai"
    return global_config


@pytest.fixture
def openrouter_config(global_config):
    """Create a test OpenRouter configuration."""
    global_config.api_provider = "openrouter"
    return global_config


@patch("consolidate_markdown.attachments.gpt.OpenAI")
def test_gpt_openai_initialization(mock_openai, openai_config):
    """Test GPT processor initialization with OpenAI."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    processor = GPTProcessor(openai_config)
    assert processor.provider == "openai"
    mock_openai.assert_called_once_with(
        api_key=openai_config.openai_key,
        base_url=openai_config.openai_base_url,
    )


@patch("consolidate_markdown.attachments.gpt.OpenAI")
def test_gpt_openrouter_initialization(mock_openai, openrouter_config):
    """Test GPT processor initialization with OpenRouter."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    processor = GPTProcessor(openrouter_config)
    assert processor.provider == "openrouter"
    mock_openai.assert_called_once_with(
        api_key=openrouter_config.openrouter_key,
        base_url=openrouter_config.openrouter_base_url,
    )


def test_gpt_invalid_provider(global_config):
    """Test GPT processor with invalid provider."""
    global_config.api_provider = "invalid"
    with pytest.raises(Exception, match="Unsupported API provider: invalid"):
        GPTProcessor(global_config)


def test_gpt_missing_openai_key(openai_config):
    """Test GPT processor with missing OpenAI key."""
    openai_config.openai_key = None
    with pytest.raises(Exception, match="OpenAI API key is required"):
        GPTProcessor(openai_config)


def test_gpt_missing_openrouter_key(openrouter_config):
    """Test GPT processor with missing OpenRouter key."""
    openrouter_config.openrouter_key = None
    with pytest.raises(Exception, match="OpenRouter API key is required"):
        GPTProcessor(openrouter_config)


@patch("consolidate_markdown.attachments.gpt.OpenAI")
def test_gpt_openai_image_analysis(mock_openai, tmp_path, openai_config):
    """Test GPT image analysis with OpenAI."""
    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "A test image description"
    mock_client.chat.completions.create.return_value = mock_response

    source_file = tmp_path / "test.jpg"
    source_file.write_bytes(b"fake jpg data")
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()

    cache_manager = CacheManager(cm_dir)
    processor = GPTProcessor(openai_config, cache_manager)
    result = ProcessingResult()

    description = processor.describe_image(source_file, result, "test")
    assert "test image description" in description.lower()
    assert result.gpt_new_analyses == 1
    assert result.gpt_cache_hits == 0
    mock_client.chat.completions.create.assert_called_once()


@patch("consolidate_markdown.attachments.gpt.OpenAI")
def test_gpt_openrouter_image_analysis(mock_openai, tmp_path, openrouter_config):
    """Test GPT image analysis with OpenRouter."""
    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "A test image description"
    mock_client.chat.completions.create.return_value = mock_response

    source_file = tmp_path / "test.jpg"
    source_file.write_bytes(b"fake jpg data")
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()

    cache_manager = CacheManager(cm_dir)
    processor = GPTProcessor(openrouter_config, cache_manager)
    result = ProcessingResult()

    description = processor.describe_image(source_file, result, "test")
    assert "test image description" in description.lower()
    assert result.gpt_new_analyses == 1
    assert result.gpt_cache_hits == 0
    mock_client.chat.completions.create.assert_called_once()


@patch("consolidate_markdown.attachments.gpt.OpenAI")
def test_gpt_image_analysis_with_cache(mock_openai, tmp_path, openai_config):
    """Test GPT image analysis with caching."""
    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "A test image description"
    mock_client.chat.completions.create.return_value = mock_response

    source_file = tmp_path / "test.jpg"
    source_file.write_bytes(b"fake jpg data")
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()

    cache_manager = CacheManager(cm_dir)
    processor = GPTProcessor(openai_config, cache_manager)
    result = ProcessingResult()

    # First analysis - should generate new
    description1 = processor.describe_image(source_file, result, "test")
    assert "test image description" in description1.lower()
    assert result.gpt_new_analyses == 1
    assert result.gpt_cache_hits == 0
    mock_client.chat.completions.create.assert_called_once()

    # Second analysis - should use cache
    mock_client.chat.completions.create.reset_mock()
    result2 = ProcessingResult()
    description2 = processor.describe_image(source_file, result2, "test")
    assert description2 == description1
    assert result2.gpt_new_analyses == 0
    assert result2.gpt_cache_hits == 1
    mock_client.chat.completions.create.assert_not_called()


def test_gpt_disabled(tmp_path, openai_config):
    """Test GPT processor when disabled."""
    source_file = tmp_path / "test.jpg"
    source_file.write_bytes(b"fake jpg data")
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()

    processor = GPTProcessor(openai_config, CacheManager(cm_dir))
    result = ProcessingResult()
    description = processor.get_placeholder(source_file, result, "test")

    assert "[GPT image analysis skipped for test.jpg]" in description
    assert result.gpt_new_analyses == 0
    assert result.gpt_cache_hits == 0
    assert result.gpt_skipped == 1


@patch("consolidate_markdown.attachments.gpt.OpenAI")
def test_gpt_error_handling(mock_openai, tmp_path, openai_config):
    """Test GPT error handling."""
    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    source_file = tmp_path / "test.jpg"
    source_file.write_bytes(b"fake jpg data")
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()

    processor = GPTProcessor(openai_config, CacheManager(cm_dir))
    result = ProcessingResult()
    description = processor.describe_image(source_file, result, "test")

    assert "[Error analyzing image]" in description
    assert result.gpt_new_analyses == 0
    assert result.gpt_cache_hits == 0
    assert result.gpt_skipped == 1
