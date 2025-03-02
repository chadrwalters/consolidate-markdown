"""Additional unit tests for the Claude processor to improve coverage."""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest

from consolidate_markdown.attachments.processor import AttachmentProcessor
from consolidate_markdown.cache import CacheManager
from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors.claude import ClaudeProcessor
from consolidate_markdown.processors.result import ProcessingResult


@pytest.fixture
def sample_conversation() -> Dict[str, Any]:
    """Return a sample conversation for testing."""
    return {
        "uuid": "test-conv-123",
        "name": "Test Conversation",
        "created_at": "2024-01-31T12:00:00Z",
        "updated_at": "2024-01-31T13:00:00Z",
        "chat_messages": [
            {
                "uuid": "msg-1",
                "created_at": "2024-01-31T12:00:00Z",
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello, this is a test message",
                    }
                ],
            },
            {
                "uuid": "msg-2",
                "created_at": "2024-01-31T12:01:00Z",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello! This is a response from Claude.",
                    }
                ],
            },
        ],
    }


@pytest.fixture
def source_config(tmp_path: Path) -> Generator[SourceConfig, None, None]:
    """Create a source configuration for testing."""
    src_dir = tmp_path / "claude_export"
    src_dir.mkdir(parents=True)

    dest_dir = tmp_path / "output"
    dest_dir.mkdir(parents=True)

    config = SourceConfig(
        type="claude",
        src_dir=src_dir,
        dest_dir=dest_dir,
        index_filename="index.md",
    )

    yield config

    # Cleanup
    if dest_dir.exists():
        shutil.rmtree(dest_dir)


@pytest.fixture
def global_config(tmp_path: Path) -> GlobalConfig:
    """Create a global configuration for testing."""
    return GlobalConfig(
        cm_dir=tmp_path / ".cm",
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


def test_validate_method(source_config: SourceConfig):
    """Test the validate method."""
    processor = ClaudeProcessor(source_config)

    # Should not raise any exceptions
    processor.validate()

    # Test with invalid source_config
    invalid_config = SourceConfig(
        type="invalid",
        src_dir=Path("/tmp/nonexistent"),
        dest_dir=Path("/tmp/nonexistent"),
    )

    # Should raise ValueError
    with pytest.raises(ValueError):
        processor = ClaudeProcessor(invalid_config, cache_manager=None)


def test_attachment_processor_property(source_config: SourceConfig):
    """Test the attachment_processor property."""
    processor = ClaudeProcessor(source_config)

    # First access should create the attachment processor
    attachment_processor = processor.attachment_processor
    assert attachment_processor is not None
    assert isinstance(attachment_processor, AttachmentProcessor)

    # Second access should return the same instance
    assert processor.attachment_processor is attachment_processor


def test_process_impl_missing_conversations_file(
    source_config: SourceConfig, global_config: GlobalConfig
) -> None:
    """Test _process_impl with missing conversations.json file."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Process without creating conversations.json
    result = processor._process_impl(config)

    # The current implementation doesn't add an error for missing conversations.json
    # It just returns an empty result
    assert len(result.errors) == 0
    assert result.processed == 0
    assert result.regenerated == 0
    assert result.from_cache == 0
    assert result.skipped == 0


def test_process_impl_invalid_json(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test _process_impl with invalid JSON in conversations.json."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Create invalid conversations.json
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text("invalid json", encoding="utf-8")

    # Process
    result = processor._process_impl(config)

    # Should have an error
    assert len(result.errors) == 1
    assert "Error reading conversations file" in result.errors[0]


def test_process_impl_invalid_format(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test _process_impl with invalid format in conversations.json."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Create conversations.json with invalid format (not a dict or list)
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text('"string instead of object"', encoding="utf-8")

    # Process
    result = processor._process_impl(config)

    # Should have an error
    assert len(result.errors) == 1
    assert "Invalid conversations format" in result.errors[0]


def test_process_impl_conversation_exception(
    source_config: SourceConfig,
    global_config: GlobalConfig,
    sample_conversation: Dict[str, Any],
):
    """Test _process_impl handling exceptions during conversation processing."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Create conversations.json
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([sample_conversation]), encoding="utf-8")

    # Mock _process_conversation to raise an exception
    with patch.object(
        processor, "_process_conversation", side_effect=Exception("Test exception")
    ):
        result = processor._process_impl(config)

    # Should have an error and a skipped conversation
    assert len(result.errors) == 1
    # The current error format is "conversation_0"
    assert "conversation_0" in result.errors[0]


def test_process_conversation_invalid(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test _process_conversation with invalid conversation."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])
    result = ProcessingResult()

    # Create an invalid conversation
    invalid_conversation = {
        "uuid": "invalid",
        "name": "Invalid",
    }  # Missing chat_messages

    # Process
    processor._process_conversation(invalid_conversation, config, result)

    # Should be skipped
    assert result.skipped == 1
    assert result.processed == 0


def test_process_conversation_from_cache(
    source_config: SourceConfig,
    global_config: GlobalConfig,
    sample_conversation: Dict[str, Any],
):
    """Test _process_conversation with cached result."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])
    result = ProcessingResult()

    # Create the output file first to simulate a cached result
    output_file = processor._get_output_path(
        sample_conversation["name"], sample_conversation["created_at"]
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("Cached content", encoding="utf-8")

    # Process
    processor._process_conversation(sample_conversation, config, result)

    # Should use cache
    assert result.from_cache == 1
    assert result.processed == 0


def test_process_conversation_conversion_error(
    source_config: SourceConfig,
    global_config: GlobalConfig,
    sample_conversation: Dict[str, Any],
):
    """Test _process_conversation handling conversion errors."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])
    result = ProcessingResult()

    # Mock _convert_to_markdown to return None (conversion error)
    with patch.object(processor, "_convert_to_markdown", return_value=None):
        processor._process_conversation(sample_conversation, config, result)

    # Should be skipped
    assert result.skipped == 1
    assert result.processed == 0


def test_process_conversation_type_error(
    source_config: SourceConfig,
    global_config: GlobalConfig,
    sample_conversation: Dict[str, Any],
):
    """Test _process_conversation handling TypeError."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])
    result = ProcessingResult()

    # Mock _convert_to_markdown to raise TypeError
    with patch.object(
        processor, "_convert_to_markdown", side_effect=TypeError("Test error")
    ):
        processor._process_conversation(sample_conversation, config, result)

    # Should have an error and be skipped
    assert len(result.errors) == 1
    assert "Error converting conversation to markdown" in result.errors[0]


def test_convert_to_markdown_exception(
    source_config: SourceConfig,
    global_config: GlobalConfig,
    sample_conversation: Dict[str, Any],
):
    """Test _convert_to_markdown handling exceptions."""
    processor = ClaudeProcessor(source_config)
    result = ProcessingResult()
    config = Config(global_config=global_config, sources=[source_config])

    # Modify the conversation to cause an exception
    broken_conversation = sample_conversation.copy()
    broken_conversation["chat_messages"] = "not a list"

    # Convert
    markdown = processor._convert_to_markdown(broken_conversation, config, result)

    # Should return None and add an error
    assert markdown is None
    assert len(result.errors) == 0  # This method logs a warning, not an error


def test_process_message_content_with_tool_use(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test _process_message_content with tool_use block."""
    processor = ClaudeProcessor(source_config)
    result = ProcessingResult()

    # Create a message with tool_use block
    message = {
        "uuid": "msg-1",
        "content": [
            {
                "type": "tool_use",
                "name": "calculator",
                "input": {"expression": "2+2"},
                "text": "Using calculator to compute 2+2",
            }
        ],
    }

    # Process
    content = processor._process_message_content(message, result)

    # Should include tool usage section
    assert any("🛠️ **Tool Usage:**" in line for line in content)
    assert any("Tool: calculator" in line for line in content)
    assert any("```tool-use" in line for line in content)


def test_process_message_content_with_tool_result(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test _process_message_content with tool_result block."""
    processor = ClaudeProcessor(source_config)
    result = ProcessingResult()

    # Create a message with tool_result block
    message = {
        "uuid": "msg-1",
        "content": [
            {
                "type": "tool_result",
                "is_error": False,
                "output": "4",
                "text": "Result: 4",
            }
        ],
    }

    # Process
    content = processor._process_message_content(message, result)

    # Should include tool result section
    assert any("📋 **Tool Result:**" in line for line in content)
    assert any("Status: SUCCESS" in line for line in content)
    assert any("```" in line for line in content)
    assert any("4" in line for line in content)


def test_process_message_content_with_tool_result_error(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test _process_message_content with tool_result error block."""
    processor = ClaudeProcessor(source_config)
    result = ProcessingResult()

    # Create a message with tool_result error block
    message = {
        "uuid": "msg-1",
        "content": [
            {
                "type": "tool_result",
                "is_error": True,
                "output": "Error: Division by zero",
                "text": "Error: Division by zero",
            }
        ],
    }

    # Process
    content = processor._process_message_content(message, result)

    # Should include tool result section with error
    assert any("📋 **Tool Result:**" in line for line in content)
    assert any("Status: ERROR" in line for line in content)


# Note: We're not testing _process_message_content with attachment blocks
# because it requires complex mocking of internal methods and the attachment
# handling is already tested in other tests.


def test_process_message_content_with_invalid_blocks(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test _process_message_content with invalid blocks."""
    processor = ClaudeProcessor(source_config)
    result = ProcessingResult()

    # Create a message with invalid blocks
    message = {
        "uuid": "msg-1",
        "content": [
            "not a dict",  # Invalid block
            {},  # Missing type
            {"type": "text"},  # Missing text
            {"type": "unknown", "text": "Unknown type"},  # Unknown type
        ],
    }

    # Process
    content = processor._process_message_content(message, result)

    # Should handle gracefully
    assert len(content) == 0


def test_process_attachment(
    source_config: SourceConfig, global_config: GlobalConfig, tmp_path: Path
):
    """Test _process_attachment method."""
    processor = ClaudeProcessor(source_config)
    result = ProcessingResult()
    config = Config(global_config=global_config, sources=[source_config])

    # Create a test attachment
    attachment_path = tmp_path / "test.txt"
    attachment_path.write_text("Test content", encoding="utf-8")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)

    # Mock AttachmentProcessor
    mock_attachment_processor = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.is_image = False
    mock_attachment_processor.process_file.return_value = (
        attachment_path,
        mock_metadata,
    )

    # Mock shutil.copy to avoid the "same file" error
    with patch("shutil.copy", return_value=output_dir / attachment_path.name):
        # Mock _format_document
        with patch.object(
            processor, "_format_document", return_value="Formatted document"
        ):
            # Process attachment
            formatted = processor._process_attachment(
                attachment_path,
                output_dir,
                mock_attachment_processor,
                config,
                result,
                alt_text="Alt text",
                is_image=False,
            )

    # Should return formatted document
    assert formatted == "Formatted document"


def test_process_attachment_image(
    source_config: SourceConfig, global_config: GlobalConfig, tmp_path: Path
):
    """Test _process_attachment method with image."""
    processor = ClaudeProcessor(source_config)
    result = ProcessingResult()
    config = Config(global_config=global_config, sources=[source_config])

    # Create a test image
    attachment_path = tmp_path / "test.jpg"
    attachment_path.write_bytes(b"Fake image data")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)

    # Mock AttachmentProcessor
    mock_attachment_processor = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.is_image = True
    mock_attachment_processor.process_file.return_value = (
        attachment_path,
        mock_metadata,
    )

    # Mock shutil.copy to avoid the "same file" error
    with patch("shutil.copy", return_value=output_dir / attachment_path.name):
        # Mock _format_image
        with patch.object(processor, "_format_image", return_value="Formatted image"):
            # Process attachment
            formatted = processor._process_attachment(
                attachment_path,
                output_dir,
                mock_attachment_processor,
                config,
                result,
                is_image=True,
            )

    # Should return formatted image
    assert formatted == "Formatted image"


def test_process_attachment_nonexistent(
    source_config: SourceConfig, global_config: GlobalConfig, tmp_path: Path
):
    """Test _process_attachment with nonexistent file."""
    processor = ClaudeProcessor(source_config)
    result = ProcessingResult()
    config = Config(global_config=global_config, sources=[source_config])

    # Nonexistent attachment
    attachment_path = tmp_path / "nonexistent.txt"

    # Process
    formatted = processor._process_attachment(
        attachment_path,
        tmp_path,
        MagicMock(),
        config,
        result,
        is_image=False,
    )

    # Should return None
    assert formatted is None


def test_process_attachment_exception(
    source_config: SourceConfig, global_config: GlobalConfig, tmp_path: Path
):
    """Test _process_attachment handling exceptions."""
    processor = ClaudeProcessor(source_config)
    result = ProcessingResult()
    config = Config(global_config=global_config, sources=[source_config])

    # Create a test attachment
    attachment_path = tmp_path / "test.txt"
    attachment_path.write_text("Test content", encoding="utf-8")

    # Mock AttachmentProcessor to raise exception
    mock_attachment_processor = MagicMock()
    mock_attachment_processor.process_file.side_effect = Exception("Test exception")

    # Process
    formatted = processor._process_attachment(
        attachment_path,
        tmp_path,
        mock_attachment_processor,
        config,
        result,
        is_image=False,
    )

    # Should return None and skip document
    assert formatted is None
    assert result.documents_skipped == 1


def test_process_attachment_with_progress(
    source_config: SourceConfig, global_config: GlobalConfig, tmp_path: Path
):
    """Test _process_attachment with progress tracking."""
    processor = ClaudeProcessor(source_config)
    result = ProcessingResult()
    config = Config(global_config=global_config, sources=[source_config])

    # Create a test attachment
    attachment_path = tmp_path / "test.txt"
    attachment_path.write_text("Test content", encoding="utf-8")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)

    # Mock AttachmentProcessor
    mock_attachment_processor = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.is_image = False
    mock_attachment_processor.process_file.return_value = (
        attachment_path,
        mock_metadata,
    )

    # Mock Progress
    mock_progress = MagicMock()
    mock_task_id = 1

    # Mock shutil.copy to avoid the "same file" error
    with patch("shutil.copy", return_value=output_dir / attachment_path.name):
        # Mock _format_document
        with patch.object(
            processor, "_format_document", return_value="Formatted document"
        ):
            # Process attachment with progress
            formatted = processor._process_attachment(
                attachment_path,
                output_dir,
                mock_attachment_processor,
                config,
                result,
                is_image=False,
                progress=mock_progress,
                task_id=mock_task_id,
            )

    # Should advance progress
    mock_progress.advance.assert_called_once_with(mock_task_id)
    assert formatted == "Formatted document"


def test_process_text_block_empty(source_config: SourceConfig):
    """Test _process_text_block with empty text."""
    processor = ClaudeProcessor(source_config)

    # Process empty text
    lines = processor._process_text_block("")

    # Should return empty list
    assert lines == []


def test_process_text_block_with_antthinking(source_config: SourceConfig):
    """Test _process_text_block with antThinking tags."""
    processor = ClaudeProcessor(source_config)

    # Process text with antThinking tags
    text = "This is <antThinking>a thinking process</antThinking> with tags."
    lines = processor._process_text_block(text)

    # Should replace tags
    assert lines == ["This is _Thinking: a thinking process_ with tags."]


def test_process_text_block_multiline(source_config: SourceConfig):
    """Test _process_text_block with multiline text."""
    processor = ClaudeProcessor(source_config)

    # Process multiline text
    text = "Line 1\nLine 2\nLine 3"
    lines = processor._process_text_block(text)

    # Should split into lines
    assert lines == ["Line 1", "Line 2", "Line 3"]
