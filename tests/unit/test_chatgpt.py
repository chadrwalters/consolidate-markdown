"""Unit tests for ChatGPT processor."""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from consolidate_markdown.attachments.processor import AttachmentProcessor
from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors import ChatGPTProcessor


@pytest.fixture
def sample_conversation() -> Dict[str, Any]:
    """Create a sample conversation for testing."""
    return {
        "title": "Test Conversation",
        "create_time": "2024-01-30T12:34:56Z",
        "update_time": "2024-01-30T13:45:00Z",
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you for asking!"},
        ],
    }


@pytest.fixture
def sample_conversation_with_attachments(config: Config) -> Dict[str, Any]:
    """Create a sample conversation with attachments for testing."""
    # Create test files in the source directory
    export_dir = config.sources[0].src_dir

    # Create test image
    image_dir = export_dir / "images"
    image_dir.mkdir(exist_ok=True)
    test_image = image_dir / "test.png"
    test_image.write_bytes(b"fake png data")

    # Create test document
    doc_dir = export_dir / "docs"
    doc_dir.mkdir(exist_ok=True)
    test_doc = doc_dir / "test.pdf"
    test_doc.write_bytes(b"fake pdf data")

    return {
        "title": "Conversation With Attachments",
        "create_time": "2024-02-01T12:00:00Z",
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Here's an image:"},
                    {"type": "image_url", "image_url": {"url": str(test_image)}},
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "I see the image. Here's a document:"},
                    {"type": "file", "file_url": {"url": str(test_doc)}},
                ],
            },
        ],
    }


@pytest.fixture
def sample_conversations() -> List[Dict[str, Any]]:
    """Create sample conversations for testing."""
    return [
        {
            "title": "First Conversation",
            "create_time": "2024-01-30T12:34:56Z",
            "update_time": "2024-01-30T13:45:00Z",
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "Hello, how are you?"},
                {
                    "role": "assistant",
                    "content": "I'm doing well, thank you for asking!",
                },
            ],
        },
        {
            "title": "Second Conversation",
            "create_time": "2024-02-15T09:00:00Z",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Another test"}],
        },
        {
            "title": "Third Conversation",
            "create_time": "2024-03-01T15:30:00Z",
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
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def config(temp_export_dir: Path, temp_output_dir: Path) -> Config:
    """Create a test configuration."""
    cm_dir = temp_output_dir / ".cm"
    cm_dir.mkdir(exist_ok=True)
    global_config = GlobalConfig(
        cm_dir=cm_dir,
        log_level="INFO",
        force_generation=False,
        no_image=True,  # Disable GPT for testing
        openai_key=None,
    )
    source_config = SourceConfig(
        type="chatgptexport",
        src_dir=temp_export_dir,
        dest_dir=temp_output_dir,
    )
    return Config(global_config=global_config, sources=[source_config])


def test_processor_initialization(config: Config):
    """Test processor initialization."""
    processor = ChatGPTProcessor(config.sources[0])
    assert processor is not None
    assert hasattr(processor, "_attachment_processor")
    assert hasattr(processor, "cache_manager")


def test_processor_validation_missing_conversations(tmp_path: Path):
    """Test validation fails when conversations.json is missing."""
    source_config = SourceConfig(
        type="chatgptexport",
        src_dir=tmp_path,
        dest_dir=tmp_path,
    )

    with pytest.raises(ValueError, match="conversations.json not found"):
        ChatGPTProcessor(source_config)


def test_basic_conversation_processing(
    config: Config,
    temp_output_dir: Path,
    sample_conversation: Dict[str, Any],
):
    """Test basic conversation processing."""
    # Update conversations.json with single conversation
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([sample_conversation]), encoding="utf-8")

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 1
    assert result.errors == []

    # Check output file exists
    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 1

    # Verify content
    content = output_files[0].read_text(encoding="utf-8")
    assert sample_conversation["title"] in content
    assert "Created: 2024-01-30" in content
    assert "Updated: 2024-01-30" in content
    assert "Model: gpt-4" in content
    assert "Hello, how are you?" in content
    assert "I'm doing well, thank you for asking!" in content


def test_conversation_with_attachments(
    config: Config,
    temp_output_dir: Path,
    sample_conversation_with_attachments: Dict[str, Any],
):
    """Test processing conversation with attachments."""
    # Update conversations.json with attachment test data
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(
        json.dumps([sample_conversation_with_attachments]), encoding="utf-8"
    )

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 1
    assert result.errors == []
    assert result.images_processed == 1
    assert result.documents_processed == 1

    # Check output file exists with correct format
    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 1
    assert output_files[0].name == "20240201 - Conversation_With_Attachments.md"

    # Verify content and format
    content = output_files[0].read_text(encoding="utf-8")

    # Check standard format elements
    assert "# Conversation With Attachments" in content
    assert "Created: 2024-02-01" in content
    assert "Model: gpt-4" in content

    # Check message content
    assert "## User" in content
    assert "Here's an image:" in content
    assert "## Assistant" in content
    assert "I see the image" in content

    # Check attachment formatting
    assert "<!-- EMBEDDED IMAGE: test.png -->" in content
    assert "<details>" in content
    assert "<summary>🖼️ test.png" in content
    assert "<!-- EMBEDDED DOCUMENT: test.pdf -->" in content
    assert "<summary>📄 test.pdf" in content


def test_cleanup(config: Config):
    """Test cleanup functionality."""
    processor = ChatGPTProcessor(config.sources[0])

    # Create test files that will trigger temp directory creation
    export_dir = config.sources[0].src_dir
    image_dir = export_dir / "images"
    image_dir.mkdir(exist_ok=True)
    test_image = image_dir / "test.png"
    test_image.write_bytes(b"fake png data")

    # Create test conversation with image
    conversations_file = export_dir / "conversations.json"
    conversations_file.write_text(
        json.dumps(
            [
                {
                    "title": "Test Cleanup",
                    "create_time": "2024-01-01T00:00:00Z",
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": str(test_image)},
                                }
                            ],
                        }
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    # Initialize temp directory and attachment processor
    temp_dir = config.global_config.cm_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    processor._temp_dir = temp_dir
    processor._attachment_processor = AttachmentProcessor(temp_dir)

    # Verify temp directory exists
    assert temp_dir.exists()

    # Call cleanup
    processor.cleanup()

    # Verify temp directory is cleaned up
    assert not temp_dir.exists()


def test_filename_format(config: Config, temp_output_dir: Path):
    """Test conversation filename format."""
    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 3
    assert result.errors == []

    # Check output files exist with correct format
    output_files = sorted(temp_output_dir.glob("*.md"))
    assert len(output_files) == 3

    # Verify filenames follow YYYYMMDD - Title.md format
    filenames = [f.name for f in output_files]
    assert "20240130 - First_Conversation.md" in filenames
    assert "20240215 - Second_Conversation.md" in filenames
    assert "20240301 - Third_Conversation.md" in filenames


def test_multiple_conversations(config: Config, temp_output_dir: Path):
    """Test processing multiple conversations."""
    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 3
    assert result.errors == []
    assert result.skipped == 0

    # Verify all conversations were processed
    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 3

    # Check content of each file
    for output_file in output_files:
        content = output_file.read_text(encoding="utf-8")
        assert "# " in content  # Has title
        assert "Created: " in content  # Has timestamp
        assert "Model: gpt-4" in content  # Has model info
        assert "## User" in content  # Has messages
