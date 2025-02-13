"""Unit tests for ChatGPT processor."""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from consolidate_markdown.config import (
    DEFAULT_OPENAI_BASE_URL,
    Config,
    GlobalConfig,
    ModelsConfig,
    SourceConfig,
)
from consolidate_markdown.processors.chatgpt import ChatGPTProcessor

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """Create a test configuration."""
    return Config(
        global_config=GlobalConfig(
            api_provider="openrouter",
            openrouter_key="test-key",
            openai_base_url=DEFAULT_OPENAI_BASE_URL,
        ),
        sources=[
            SourceConfig(
                type="chatgpt",
                src_dir=tmp_path / "chatgpt_export",
                dest_dir=tmp_path / "output" / "chatgpt",
            )
        ],
    )


@pytest.fixture
def sample_conversation() -> Dict[str, Any]:
    """Create a sample conversation for testing."""
    return {
        "title": "Test Conversation",
        "create_time": 1677649200,  # 2023-03-01 00:00:00
        "update_time": 1677649200,
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
        ],
    }


@pytest.fixture
def sample_conversation_with_attachments() -> Dict[str, Any]:
    """Create a sample conversation with attachments."""
    return {
        "title": "Conversation With Attachments",
        "create_time": 1677649200,  # 2023-03-01 00:00:00
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": "Here's an image",
                "attachments": [
                    {
                        "type": "image",
                        "path": "path/to/image.jpg",
                        "size": 1024,
                        "dimensions": [800, 600],
                    }
                ],
            }
        ],
    }


@pytest.fixture
def sample_conversations() -> List[Dict[str, Any]]:
    """Sample conversations for testing."""
    return [
        {
            "title": "Test Conversation 1",
            "create_time": 1677649200,  # 2023-03-01 00:00:00
            "update_time": 1677649200,
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test message"}],
        },
        {
            "title": "Test Conversation 2",
            "create_time": 1677735600,  # 2023-03-02 00:00:00
            "update_time": 1677735600,
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Another test"}],
        },
        {
            "title": "Test Conversation 3",
            "create_time": 1677822000,  # 2023-03-03 00:00:00
            "update_time": 1677822000,
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Yet another test"}],
        },
    ]


@pytest.fixture
def temp_export_dir(tmp_path: Path, sample_conversations: List[Dict[str, Any]]) -> Path:
    """Create a temporary directory with sample export data."""
    export_dir = tmp_path / "chatgpt_export"
    export_dir.mkdir()

    # Create conversations.json
    conversations_file = export_dir / "conversations.json"
    conversations_file.write_text(json.dumps(sample_conversations), encoding="utf-8")

    return export_dir


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output" / "chatgpt"
    output_dir.mkdir(parents=True)
    return output_dir


def test_processor_initialization(config: Config):
    """Test processor initialization."""
    # Create source directory
    config.sources[0].src_dir.mkdir(parents=True)
    processor = ChatGPTProcessor(config.sources[0])
    assert processor.source_config.type == "chatgpt"
    assert processor is not None
    assert hasattr(processor, "_attachment_processor")
    assert hasattr(processor, "cache_manager")


def test_basic_conversation_processing(
    config: Config,
    temp_output_dir: Path,
    sample_conversation: Dict[str, Any],
):
    """Test basic conversation processing."""
    # Create output directory
    output_dir = config.sources[0].dest_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create markdown_chats directory
    markdown_dir = config.sources[0].src_dir / "markdown_chats"
    markdown_dir.mkdir(parents=True, exist_ok=True)

    # Update conversations.json with single conversation
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([sample_conversation]), encoding="utf-8")

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    # Verify the conversation was processed
    assert result.processed == 1
    assert result.errors == []

    # Verify output file exists and has correct content
    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 1
    content = output_files[0].read_text(encoding="utf-8")
    assert "Test Conversation" in content
    assert "Created: 2023-03-01" in content
    assert "Model: gpt-4" in content
    assert "## User" in content
    assert "Hello, how are you?" in content
    assert "## Assistant" in content
    assert "I'm doing well, thank you!" in content


def test_filename_format(config: Config, temp_output_dir: Path):
    """Test conversation filename format."""
    # Create markdown_chats directory
    markdown_dir = config.sources[0].src_dir / "markdown_chats"
    markdown_dir.mkdir(parents=True, exist_ok=True)

    # Create test conversations
    conversations = [
        {
            "title": "Test Conversation 1",
            "create_time": 1677649200,  # 2023-03-01 00:00:00
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test message"}],
        },
        {
            "title": "Test Conversation 2",
            "create_time": 1677735600,  # 2023-03-02 00:00:00
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Another test"}],
        },
        {
            "title": "Test Conversation 3",
            "create_time": 1677822000,  # 2023-03-03 00:00:00
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Yet another test"}],
        },
    ]

    # Write conversations to file
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations), encoding="utf-8")

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 3
    assert result.errors == []

    # Verify output files exist with correct filenames
    output_files = sorted(temp_output_dir.glob("*.md"))
    assert len(output_files) == 3
    assert output_files[0].name == "20230301 - Test_Conversation_1.md"
    assert output_files[1].name == "20230302 - Test_Conversation_2.md"
    assert output_files[2].name == "20230303 - Test_Conversation_3.md"


def test_multiple_conversations(config: Config, temp_output_dir: Path):
    """Test processing multiple conversations."""
    # Create markdown_chats directory
    markdown_dir = config.sources[0].src_dir / "markdown_chats"
    markdown_dir.mkdir(parents=True, exist_ok=True)

    # Create test conversations
    conversations = [
        {
            "title": "First Conversation",
            "create_time": 1677649200,  # 2023-03-01 00:00:00
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        },
        {
            "title": "Second Conversation",
            "create_time": 1677735600,  # 2023-03-02 00:00:00
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "How are you?"},
                {"role": "assistant", "content": "I'm doing well, thanks!"},
            ],
        },
        {
            "title": "Third Conversation",
            "create_time": 1677822000,  # 2023-03-03 00:00:00
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "What's new?"},
                {"role": "assistant", "content": "Not much, just helping you!"},
            ],
        },
    ]

    # Write conversations to file
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations), encoding="utf-8")

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 3
    assert result.errors == []

    # Verify output files exist with correct content
    output_files = sorted(temp_output_dir.glob("*.md"))
    assert len(output_files) == 3

    # Check first conversation
    content = output_files[0].read_text(encoding="utf-8")
    assert "First Conversation" in content
    assert "Created: 2023-03-01" in content
    assert "Hello" in content
    assert "Hi there!" in content

    # Check second conversation
    content = output_files[1].read_text(encoding="utf-8")
    assert "Second Conversation" in content
    assert "Created: 2023-03-02" in content
    assert "How are you?" in content
    assert "I'm doing well, thanks!" in content

    # Check third conversation
    content = output_files[2].read_text(encoding="utf-8")
    assert "Third Conversation" in content
    assert "Created: 2023-03-03" in content
    assert "What's new?" in content
    assert "Not much, just helping you!" in content


def test_content_types(config: Config, temp_output_dir: Path):
    """Test processing of various content types."""
    # Create markdown_chats directory
    markdown_dir = config.sources[0].src_dir / "markdown_chats"
    markdown_dir.mkdir(parents=True, exist_ok=True)

    processor = ChatGPTProcessor(config.sources[0])

    # Create test conversation with different content types
    conversation = {
        "title": "Content Types",
        "create_time": 1677649200,  # 2023-03-01 00:00:00
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Hello!"},
                    {"type": "code", "language": "python", "text": "print('Hello')"},
                    {"type": "quote", "text": "Famous quote"},
                ],
            },
        ],
    }

    # Write conversation to file
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]), encoding="utf-8")

    result = processor.process(config)
    assert result.processed == 1
    assert result.errors == []

    # Verify output file exists with correct content
    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 1
    content = output_files[0].read_text(encoding="utf-8")
    assert "Content Types" in content
    assert "Created: 2023-03-01" in content
    assert "Hello!" in content
    assert "```python" in content
    assert "print('Hello')" in content
    assert "```" in content
    assert "Famous quote" in content
