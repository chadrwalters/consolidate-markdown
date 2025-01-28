from unittest.mock import Mock, patch

from consolidate_markdown.attachments.gpt import GPTProcessor
from consolidate_markdown.attachments.processor import (
    AttachmentMetadata,
    AttachmentProcessor,
)
from consolidate_markdown.cache import CacheManager
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
    assert (cm_dir / "temp" / "test.jpg").exists()


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
    assert (cm_dir / "temp" / "test.jpg").exists()


def test_document_processing(tmp_path):
    """Test processing document attachments"""
    source_file = tmp_path / "test.pdf"
    source_file.write_bytes(b"fake pdf data")
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()

    processor = AttachmentProcessor(cm_dir)
    temp_path, metadata = processor.process_file(source_file)

    assert isinstance(metadata, AttachmentMetadata)
    assert not metadata.is_image
    assert metadata.mime_type == "application/pdf"
    assert (cm_dir / "temp" / "test.pdf").exists()


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
    assert (cm_dir / "temp" / "test.svg").exists()


@patch("consolidate_markdown.attachments.gpt.OpenAI")
def test_gpt_image_analysis_with_cache(mock_openai, tmp_path):
    """Test GPT image analysis with caching"""
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
    processor = GPTProcessor("test_key", cache_manager)
    result = ProcessingResult()

    # First analysis - should generate new
    description1 = processor.describe_image(source_file, result)
    assert "test image description" in description1.lower()
    assert result.gpt_new_analyses == 1
    assert result.gpt_cache_hits == 0
    mock_client.chat.completions.create.assert_called_once()

    # Second analysis - should use cache
    mock_client.chat.completions.create.reset_mock()
    result2 = ProcessingResult()
    description2 = processor.describe_image(source_file, result2)
    assert description2 == description1
    assert result2.gpt_new_analyses == 0
    assert result2.gpt_cache_hits == 1
    mock_client.chat.completions.create.assert_not_called()


def test_gpt_disabled(tmp_path):
    """Test GPT processor when disabled"""
    source_file = tmp_path / "test.jpg"
    source_file.write_bytes(b"fake jpg data")
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()

    processor = GPTProcessor(
        "dummy-key", CacheManager(cm_dir)
    )  # Using dummy key disables GPT
    result = ProcessingResult()
    description = processor.get_placeholder(source_file, result)

    assert "[GPT image analysis skipped for test.jpg]" in description
    assert result.gpt_new_analyses == 0
    assert result.gpt_cache_hits == 0
    assert result.gpt_skipped == 1


@patch("consolidate_markdown.attachments.gpt.OpenAI")
def test_gpt_error_handling(mock_openai, tmp_path):
    """Test GPT error handling"""
    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    source_file = tmp_path / "test.jpg"
    source_file.write_bytes(b"fake jpg data")
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()

    processor = GPTProcessor("test_key", CacheManager(cm_dir))
    result = ProcessingResult()
    description = processor.describe_image(source_file, result)

    assert "[Error analyzing image]" in description
    assert result.gpt_new_analyses == 0
    assert result.gpt_cache_hits == 0
    assert result.gpt_skipped == 1
