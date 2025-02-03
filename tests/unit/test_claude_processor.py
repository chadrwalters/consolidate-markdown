"""Unit tests for the Claude processor."""

import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Generator, List

import pytest

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
                "sender": "human",
                "created_at": "2024-01-31T12:00:00Z",
                "content": [{"type": "text", "text": "Hello, this is a test message"}],
            },
            {
                "uuid": "msg-2",
                "sender": "assistant",
                "created_at": "2024-01-31T12:01:00Z",
                "content": [
                    {
                        "type": "text",
                        "text": "<antThinking>Processing test message</antThinking>\nHello! I received your test message.",
                    }
                ],
            },
        ],
    }


@pytest.fixture
def source_config(tmp_path: Path) -> Generator[SourceConfig, None, None]:
    """Create a test source configuration."""
    src_dir = tmp_path / "claude_test_src"
    dest_dir = tmp_path / "claude_test_dest"
    src_dir.mkdir()
    dest_dir.mkdir()

    # Create required files with test-specific names
    conversations_file = src_dir / "conversations.json"
    conversations_file.write_text("[]")

    # Use pytest's built-in yield fixture for cleanup
    yield SourceConfig(type="claude", src_dir=src_dir, dest_dir=dest_dir)

    # Cleanup after test
    try:
        if conversations_file.exists():
            conversations_file.unlink()
        if src_dir.exists():
            src_dir.rmdir()
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
    except Exception:
        pass  # Best effort cleanup


@pytest.fixture
def global_config() -> GlobalConfig:
    """Create a test global configuration."""
    return GlobalConfig(force_generation=True)


def test_processor_initialization(source_config: SourceConfig):
    """Test processor initialization."""
    processor = ClaudeProcessor(source_config)
    assert processor is not None
    assert processor.source_config == source_config


def test_validate_missing_files(tmp_path: Path):
    """Test validation with missing required files."""
    src_dir = tmp_path / "src"
    dest_dir = tmp_path / "dest"
    src_dir.mkdir()
    dest_dir.mkdir()

    config = SourceConfig(type="claude", src_dir=src_dir, dest_dir=dest_dir)

    with pytest.raises(ValueError, match="conversations.json not found"):
        ClaudeProcessor(config).validate()


def test_json_loading(
    source_config: SourceConfig,
    global_config: GlobalConfig,
    sample_conversation: Dict[str, Any],
):
    """Test loading and parsing conversations.json."""
    # Write sample conversation
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([sample_conversation]))

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])
    processor.process(config)


def test_metadata_extraction(source_config: SourceConfig, global_config: GlobalConfig):
    """Test metadata extraction from conversations."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversations
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([]))

    processor.process(config)  # Just verify it doesn't raise exceptions


def test_conversation_validation(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test conversation validation."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversations
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([]))

    processor.process(config)


def test_sender_formatting(source_config: SourceConfig, global_config: GlobalConfig):
    """Test sender name formatting."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversations
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([]))

    processor.process(config)  # Just verify it doesn't raise exceptions


def test_timestamp_handling(source_config: SourceConfig, global_config: GlobalConfig):
    """Test handling of message timestamps."""
    conversation = {
        "uuid": "test-conv-123",
        "name": "Test Conversation",
        "created_at": "2024-01-31T12:00:00Z",
        "chat_messages": [
            {
                "uuid": "msg-1",
                "sender": "human",
                "created_at": "2024-01-31T12:00:00Z",
                "content": [{"type": "text", "text": "Test"}],
            },
            {
                "uuid": "msg-2",
                "sender": "assistant",
                # Test missing timestamp
                "content": [{"type": "text", "text": "Response"}],
            },
            {
                "uuid": "msg-3",
                "sender": "human",
                "created_at": "invalid-timestamp",
                "content": [{"type": "text", "text": "Invalid"}],
            },
        ],
    }

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversation
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]))

    processor.process(config)


def test_content_block_processing(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test processing of different content block types."""
    conversation = {
        "uuid": "test-conv-123",
        "name": "Test Conversation",
        "created_at": "2024-01-31T12:00:00Z",
        "chat_messages": [
            {
                "uuid": "msg-1",
                "sender": "assistant",
                "created_at": "2024-01-31T12:00:00Z",
                "content": [
                    {"type": "text", "text": "Regular text"},
                    {
                        "type": "tool_use",
                        "name": "test_tool",
                        "input": {"param": "value"},
                    },
                    {
                        "type": "tool_result",
                        "name": "test_tool",
                        "content": {"result": "success"},
                        "is_error": False,
                    },
                    {"type": "unknown", "data": "ignored"},
                ],
            }
        ],
    }

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversation
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]))

    processor.process(config)


def test_antthinking_extraction(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test extraction and formatting of antThinking tags."""
    conversation = {
        "uuid": "test-conv-123",
        "name": "Test Conversation",
        "created_at": "2024-01-31T12:00:00Z",
        "chat_messages": [
            {
                "uuid": "msg-1",
                "sender": "assistant",
                "created_at": "2024-01-31T12:00:00Z",
                "content": [
                    {
                        "type": "text",
                        "text": "Before <antThinking>Processing the request</antThinking> After",
                    },
                    {
                        "type": "text",
                        "text": "<antThinking>Multiple\nLine\nThinking</antThinking>",
                    },
                    {"type": "text", "text": "No tags here"},
                ],
            }
        ],
    }

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversation
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]))

    processor.process(config)


def test_antartifact_extraction(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test extraction and formatting of antArtifact tags."""
    conversation = {
        "uuid": "test-conv-123",
        "name": "Test Conversation",
        "created_at": "2024-01-31T12:00:00Z",
        "chat_messages": [
            {
                "uuid": "msg-1",
                "sender": "assistant",
                "created_at": "2024-01-31T12:00:00Z",
                "content": [
                    {
                        "type": "text",
                        "text": "Before <antArtifact>Generated code\ndef test():\n    pass</antArtifact> After",
                    }
                ],
            }
        ],
    }

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversation
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]))

    processor.process(config)


def test_nested_tags(source_config: SourceConfig, global_config: GlobalConfig):
    """Test handling of nested XML tags."""
    conversation = {
        "uuid": "test-conv-123",
        "name": "Test Conversation",
        "created_at": "2024-01-31T12:00:00Z",
        "chat_messages": [
            {
                "uuid": "msg-1",
                "sender": "assistant",
                "created_at": "2024-01-31T12:00:00Z",
                "content": [
                    {
                        "type": "text",
                        "text": "<antThinking>Analyzing request\n<antArtifact>Initial plan:\n1. Step one\n2. Step two</antArtifact>\nContinuing analysis</antThinking>",
                    }
                ],
            }
        ],
    }

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversation
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]))

    processor.process(config)


def test_artifact_version_tracking(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test tracking of artifact versions."""
    conversation = {
        "uuid": "test-conv-123",
        "name": "Test Conversation",
        "created_at": "2024-01-31T12:00:00Z",
        "chat_messages": [
            {
                "uuid": "msg-1",
                "sender": "assistant",
                "created_at": "2024-01-31T12:00:00Z",
                "content": [
                    {
                        "type": "text",
                        "text": "<antArtifact>Version 1 of code\ndef test(): pass</antArtifact>",
                    }
                ],
            },
            {
                "uuid": "msg-2",
                "sender": "assistant",
                "created_at": "2024-01-31T12:01:00Z",
                "content": [
                    {
                        "type": "text",
                        "text": "<antArtifact>Version 1 of code\ndef test(): pass</antArtifact>",
                    }
                ],
            },
            {
                "uuid": "msg-3",
                "sender": "assistant",
                "created_at": "2024-01-31T12:02:00Z",
                "content": [
                    {
                        "type": "text",
                        "text": "<antArtifact>Version 2 of code\ndef test():\n    return True</antArtifact>",
                    }
                ],
            },
        ],
    }

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversation
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]))

    processor.process(config)


def test_artifact_relationship_mapping(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test mapping of relationships between artifacts."""
    conversations = [
        {
            "uuid": "conv-1",
            "name": "First Conversation",
            "created_at": "2024-01-31T12:00:00Z",
            "chat_messages": [
                {
                    "uuid": "msg-1",
                    "sender": "assistant",
                    "created_at": "2024-01-31T12:00:00Z",
                    "content": [
                        {
                            "type": "text",
                            "text": "<antArtifact>Artifact A</antArtifact>\n<antArtifact>Artifact B</antArtifact>",
                        }
                    ],
                }
            ],
        },
        {
            "uuid": "conv-2",
            "name": "Second Conversation",
            "created_at": "2024-01-31T12:01:00Z",
            "chat_messages": [
                {
                    "uuid": "msg-2",
                    "sender": "assistant",
                    "created_at": "2024-01-31T12:01:00Z",
                    "content": [
                        {
                            "type": "text",
                            "text": "<antArtifact>Artifact C</antArtifact>",
                        }
                    ],
                }
            ],
        },
    ]

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversations
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations))

    processor.process(config)


def test_artifact_id_generation(
    source_config: SourceConfig,
    global_config: GlobalConfig,
    caplog: pytest.LogCaptureFixture,
):
    """Test consistent generation of artifact IDs."""
    # Configure debug logging
    caplog.set_level(logging.DEBUG)

    # Test that same content gets same ID
    conversation1 = {
        "uuid": "conv-1",
        "name": "First Conversation",
        "created_at": "2024-01-31T12:00:00Z",
        "chat_messages": [
            {
                "uuid": "msg-1",
                "sender": "assistant",
                "created_at": "2024-01-31T12:00:00Z",
                "content": [
                    {"type": "text", "text": "<antArtifact>Test content</antArtifact>"}
                ],
            }
        ],
    }

    processor1 = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Process first conversation
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation1]))
    cache_file = processor1.cache_manager.cache_dir / "conversations.json"
    cache_file.write_text(json.dumps([conversation1]))
    processor1.process(config)

    # Get first artifact ID
    artifacts_dir = source_config.dest_dir / "artifacts"
    index_content = (artifacts_dir / "index.md").read_text()
    artifact_id1 = next(
        line[2:14] for line in index_content.split("\n") if line.startswith("- ")
    )
    print("\nArtifact 1 content:")
    print((artifacts_dir / f"{artifact_id1}.md").read_text())

    # Clean up and process second conversation with same content
    shutil.rmtree(artifacts_dir)
    conversation2 = {
        "uuid": "conv-2",
        "name": "Second Conversation",
        "created_at": "2024-01-31T12:01:00Z",
        "chat_messages": [
            {
                "uuid": "msg-2",
                "sender": "assistant",
                "created_at": "2024-01-31T12:01:00Z",
                "content": [
                    {"type": "text", "text": "<antArtifact>Test content</antArtifact>"}
                ],
            }
        ],
    }

    processor2 = ClaudeProcessor(source_config)
    conversations_file.write_text(json.dumps([conversation2]))
    cache_file = processor2.cache_manager.cache_dir / "conversations.json"
    cache_file.write_text(json.dumps([conversation2]))
    processor2.process(config)

    # Get second artifact ID
    index_content = (artifacts_dir / "index.md").read_text()
    artifact_id2 = next(
        line[2:14] for line in index_content.split("\n") if line.startswith("- ")
    )
    print("\nArtifact 2 content:")
    print((artifacts_dir / f"{artifact_id2}.md").read_text())

    # IDs should match for same content
    assert artifact_id1 == artifact_id2

    # Different content should get different ID
    conversation3 = {
        "uuid": "conv-3",
        "name": "Third Conversation",
        "created_at": "2024-01-31T12:02:00Z",
        "chat_messages": [
            {
                "uuid": "msg-3",
                "sender": "assistant",
                "created_at": "2024-01-31T12:02:00Z",
                "content": [
                    {
                        "type": "text",
                        "text": "<antArtifact>Different content</antArtifact>",
                    }
                ],
            }
        ],
    }

    processor3 = ClaudeProcessor(source_config)
    conversations_file.write_text(json.dumps([conversation3]))
    cache_file = processor3.cache_manager.cache_dir / "conversations.json"
    cache_file.write_text(json.dumps([conversation3]))
    processor3.process(config)

    # Get third artifact ID
    index_content = (artifacts_dir / "index.md").read_text()
    artifact_id3 = next(
        line[2:14] for line in index_content.split("\n") if line.startswith("- ")
    )
    print("\nArtifact 3 content:")
    print((artifacts_dir / f"{artifact_id3}.md").read_text())

    # ID should be different for different content
    assert artifact_id1 != artifact_id3


def test_index_date_grouping(source_config: SourceConfig, global_config: GlobalConfig):
    """Test date-based grouping in the index."""
    conversations = [
        {
            "uuid": "conv-1",
            "name": "January Conversation",
            "created_at": "2024-01-15T12:00:00Z",
            "chat_messages": [{"type": "text", "text": "Test"}],
        },
        {
            "uuid": "conv-2",
            "name": "Another January",
            "created_at": "2024-01-20T12:00:00Z",
            "chat_messages": [{"type": "text", "text": "Test"}],
        },
        {
            "uuid": "conv-3",
            "name": "February Conversation",
            "created_at": "2024-02-01T12:00:00Z",
            "chat_messages": [{"type": "text", "text": "Test"}],
        },
        {
            "uuid": "conv-4",
            "name": "Undated Conversation",
            "chat_messages": [{"type": "text", "text": "Test"}],
        },
    ]

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversations
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations))

    processor.process(config)


def test_index_link_generation(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test generation of links in the index."""
    conversations = [
        {
            "uuid": "conv-1",
            "name": "Test Conversation",
            "created_at": "2024-01-15T12:00:00Z",
            "chat_messages": [{"type": "text", "text": "Test"}],
        },
        {
            "uuid": "conv-2",
            "name": "Conversation with/special#chars",
            "created_at": "2024-01-20T12:00:00Z",
            "chat_messages": [{"type": "text", "text": "Test"}],
        },
    ]

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversations
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations))

    processor.process(config)


def test_index_sorting(source_config: SourceConfig, global_config: GlobalConfig):
    """Test sorting of conversations in the index."""
    conversations = [
        {
            "uuid": "conv-1",
            "name": "B Conversation",
            "created_at": "2024-01-15T12:00:00Z",
            "chat_messages": [{"type": "text", "text": "Test"}],
        },
        {
            "uuid": "conv-2",
            "name": "A Conversation",
            "created_at": "2024-01-15T13:00:00Z",
            "chat_messages": [{"type": "text", "text": "Test"}],
        },
        {
            "uuid": "conv-3",
            "name": "C Conversation",
            "created_at": "2024-01-15T11:00:00Z",
            "chat_messages": [{"type": "text", "text": "Test"}],
        },
    ]

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversations
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations))

    processor.process(config)


def test_index_empty_conversations(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test index generation with empty conversations list."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write empty conversations list
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text("[]")

    processor.process(config)


def test_invalid_xml_tags(source_config: SourceConfig, global_config: GlobalConfig):
    """Test handling of invalid XML tags."""
    conversation = {
        "uuid": "test-conv-123",
        "name": "Test Conversation",
        "created_at": "2024-01-31T12:00:00Z",
        "chat_messages": [
            {
                "uuid": "msg-1",
                "sender": "assistant",
                "created_at": "2024-01-31T12:00:00Z",
                "content": [
                    {
                        "type": "text",
                        "text": "Before <antThinking>Unclosed thinking tag\nNext <antArtifact>Nested but unclosed\nMore text",
                    },
                    {
                        "type": "text",
                        "text": "</antThinking>Closing without opening\n<antArtifact>Valid tag</antArtifact>",
                    },
                    {
                        "type": "text",
                        "text": "<antUnknown>Unknown tag type</antUnknown>",
                    },
                ],
            }
        ],
    }

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversation
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]))

    processor.process(config)


def test_missing_fields(source_config: SourceConfig, global_config: GlobalConfig):
    """Test handling of missing required and optional fields."""
    conversation = {
        # Missing uuid
        "name": "Test Conversation",
        # Missing created_at
        "chat_messages": [
            {
                # Missing uuid
                "sender": "assistant",
                # Missing created_at
                "content": [
                    {
                        # Missing type
                        "text": "Test message"
                    }
                ],
            },
            {
                "uuid": "msg-2",
                # Missing sender
                "created_at": "2024-01-31T12:00:00Z",
                # Missing content
            },
        ],
    }

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversation
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]))

    processor.process(config)


def test_malformed_data(source_config: SourceConfig, global_config: GlobalConfig):
    """Test handling of malformed data structures."""
    conversations: List[Any] = [
        None,  # Null conversation
        {},  # Empty conversation
        [],  # List instead of dict
        {"uuid": "test-1", "name": "Test 1", "chat_messages": None},  # Null messages
        {
            "uuid": "test-2",
            "name": "Test 2",
            "chat_messages": [None, {}],  # Invalid messages
        },
        {
            "uuid": "test-3",
            "name": "Test 3",
            "chat_messages": [
                {
                    "uuid": "msg-1",
                    "sender": "assistant",
                    "content": None,  # Null content
                },
                {
                    "uuid": "msg-2",
                    "sender": "assistant",
                    "content": [None, {}],  # Invalid content blocks
                },
            ],
        },
        "not a conversation",  # String instead of dict
    ]

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversations
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations))

    processor.process(config)


def test_empty_conversations(source_config: SourceConfig, global_config: GlobalConfig):
    """Test handling of various empty states."""
    conversations = [
        {"uuid": "test-1", "name": "Empty Messages", "chat_messages": []},
        {
            "uuid": "test-2",
            "name": "Empty Content",
            "chat_messages": [{"uuid": "msg-1", "sender": "assistant", "content": []}],
        },
        {
            "uuid": "test-3",
            "name": "Empty Text",
            "chat_messages": [
                {
                    "uuid": "msg-1",
                    "sender": "assistant",
                    "content": [{"type": "text", "text": ""}],
                }
            ],
        },
    ]

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversations
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations))

    processor.process(config)


def test_unicode_handling(source_config: SourceConfig, global_config: GlobalConfig):
    """Test handling of unicode characters in various fields."""
    conversation = {
        "uuid": "test-🔑",  # Unicode in UUID
        "name": "Test 📝 Conversation",  # Unicode in name
        "created_at": "2024-01-31T12:00:00Z",
        "chat_messages": [
            {
                "uuid": "msg-⭐",  # Unicode in message ID
                "sender": "👤 user",  # Unicode in sender
                "created_at": "2024-01-31T12:00:00Z",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello 🌍! <antThinking>思考中...</antThinking>",  # Unicode in content and tags
                    },
                    {
                        "type": "text",
                        "text": "<antArtifact>def test_emoji():\n    return '✅'</antArtifact>",  # Unicode in artifact
                    },
                ],
            }
        ],
    }

    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversation
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]))

    processor.process(config)


def test_format_file_size():
    """Test file size formatting."""
    config = SourceConfig(src_dir=Path(), dest_dir=Path("/tmp/test"), type="claude")

    # Create required files
    config.src_dir.mkdir(parents=True, exist_ok=True)
    (config.src_dir / "conversations.json").write_text("[]")
    (config.src_dir / "users.json").write_text("{}")

    processor = ClaudeProcessor(config)
    assert processor._format_file_size(500) == "500.0B"
    assert processor._format_file_size(1024) == "1.0KB"
    assert processor._format_file_size(1024 * 1024) == "1.0MB"
    assert processor._format_file_size(1024 * 1024 * 1024) == "1.0GB"


def test_get_attachment_icon():
    """Test file type icon selection."""
    config = SourceConfig(src_dir=Path(), dest_dir=Path("/tmp/test"), type="claude")

    # Create required files
    config.src_dir.mkdir(parents=True, exist_ok=True)
    (config.src_dir / "conversations.json").write_text("[]")
    (config.src_dir / "users.json").write_text("{}")

    processor = ClaudeProcessor(config)
    assert processor._get_attachment_icon("pdf") == "📄"
    assert processor._get_attachment_icon("application/pdf") == "📄"
    assert processor._get_attachment_icon("text/plain") == "📝"
    assert processor._get_attachment_icon("image/jpeg") == "🖼️"
    assert processor._get_attachment_icon("unknown") == "📎"


def test_format_text_attachment():
    """Test attachment formatting with metadata."""
    config = SourceConfig(src_dir=Path(), dest_dir=Path("/tmp/test"), type="claude")

    # Create required files
    config.src_dir.mkdir(parents=True, exist_ok=True)
    (config.src_dir / "conversations.json").write_text("[]")
    (config.src_dir / "users.json").write_text("{}")

    processor = ClaudeProcessor(config)
    result = ProcessingResult()

    # Test PDF attachment
    pdf_attachment = {
        "file_type": "pdf",
        "file_name": "test.pdf",
        "file_size": 1024 * 1024,  # 1MB
        "content": "Extracted PDF content",
    }

    output = processor._format_text_attachment(pdf_attachment, "msg1", result)
    assert output is not None
    assert "<!-- CLAUDE EXPORT: Extracted content from test.pdf -->" in output
    assert "📄 test.pdf (1.0MB pdf)" in output
    assert "Extracted PDF content" in output
    assert result.documents_processed == 1


def test_format_text_attachment_missing_data():
    """Test attachment formatting with missing metadata."""
    config = SourceConfig(src_dir=Path(), dest_dir=Path("/tmp/test"), type="claude")

    # Create required files
    config.src_dir.mkdir(parents=True, exist_ok=True)
    (config.src_dir / "conversations.json").write_text("[]")
    (config.src_dir / "users.json").write_text("{}")

    processor = ClaudeProcessor(config)
    result = ProcessingResult()

    # Test missing file type
    invalid_attachment = {"file_name": "test.txt", "content": "content"}
    output = processor._format_text_attachment(invalid_attachment, "msg1", result)
    assert output is None
    assert result.documents_processed == 0

    # Test empty content - should show metadata
    no_content_attachment = {
        "file_type": "txt",
        "file_name": "empty.txt",
        "file_size": 1024,
    }
    output = processor._format_text_attachment(no_content_attachment, "msg1", result)
    assert output is not None
    assert "Empty Attachment" in output
    assert "1.0KB" in output
    assert "No content available in Claude export" in output
    assert result.documents_processed == 1


def test_format_text_attachment_various_types():
    """Test attachment formatting with different file types."""
    config = SourceConfig(src_dir=Path(), dest_dir=Path("/tmp/test"), type="claude")

    # Create required files
    config.src_dir.mkdir(parents=True, exist_ok=True)
    (config.src_dir / "conversations.json").write_text("[]")
    (config.src_dir / "users.json").write_text("{}")

    processor = ClaudeProcessor(config)
    result = ProcessingResult()

    attachments: List[Dict[str, Any]] = [
        {
            "file_type": "python",
            "file_name": "script.py",
            "file_size": 1000,
            "content": "print('Hello')",
        },
        {
            "file_type": "json",
            "file_name": "data.json",
            "file_size": 2048,
            "content": '{"key": "value"}',
        },
        {
            "file_type": "csv",
            "file_name": "data.csv",
            "file_size": 512,
            "content": "a,b,c\n1,2,3",
        },
    ]

    for attachment in attachments:
        output = processor._format_text_attachment(attachment, "msg1", result)
        assert output is not None
        assert (
            f"<!-- CLAUDE EXPORT: Extracted content from {attachment['file_name']} -->"
            in output
        )
        assert "Original File Information:" in output
        assert f"Type: {attachment['file_type']}" in output
        assert attachment["content"] in output

    assert result.documents_processed == len(attachments)


def test_process_conversations(
    source_config: SourceConfig, global_config: GlobalConfig
):
    """Test processing conversations."""
    processor = ClaudeProcessor(source_config)
    config = Config(global_config=global_config, sources=[source_config])

    # Write conversations
    conversations_file = source_config.src_dir / "conversations.json"
    conversations_file.write_text("[]")

    processor.process(config)  # Just verify it doesn't raise exceptions
