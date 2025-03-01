import json
import uuid

import pytest

from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors.claude import ClaudeProcessor


@pytest.fixture
def claude_config(tmp_path) -> Config:
    """Create test configuration for Claude processor."""
    src_dir = tmp_path / "claude_export"
    src_dir.mkdir(parents=True)

    dest_dir = tmp_path / "output"
    dest_dir.mkdir(parents=True)

    source_config = SourceConfig(
        type="claude",
        src_dir=src_dir,
        dest_dir=dest_dir,
        index_filename="index.md",
    )

    global_config = GlobalConfig(
        cm_dir=dest_dir,
        log_level="INFO",
        force_generation=False,
        no_image=True,
        api_provider="openrouter",
        openrouter_key="test-key",
    )

    return Config(global_config=global_config, sources=[source_config])


def test_invalid_text_attachment_missing_type(claude_config):
    """Test handling of invalid text attachment with missing type."""
    # Create a Claude export with an attachment missing the type field
    message_id = str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())

    conversation = {
        "uuid": conversation_id,
        "name": "Test Conversation",
        "created_at": "2025-01-01T00:00:00Z",
        "chat_messages": [
            {
                "uuid": message_id,
                "conversation_uuid": conversation_id,
                "sender": "human",
                "attachments": [
                    {
                        # Missing type field
                        "file_name": "test.txt",
                        "file_size": 1024,
                        "content": "Test content",
                    },
                ],
                "text": "Here's a document",
                "created_at": "2025-01-01T00:00:00Z",
            }
        ],
    }

    # Create the conversations.json file
    conversations_file = claude_config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]), encoding="utf-8")

    # Process the conversation
    processor = ClaudeProcessor(claude_config.sources[0])
    result = processor.process(claude_config)

    # Check that the warning was logged but processing continued
    assert result.processed == 1

    # Check that the output file was created
    output_files = list(claude_config.sources[0].dest_dir.glob("*.md"))
    assert len(output_files) == 1


def test_invalid_text_attachment_missing_name(claude_config):
    """Test handling of invalid text attachment with missing name."""
    # Create a Claude export with an attachment missing the name field
    message_id = str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())

    conversation = {
        "uuid": conversation_id,
        "name": "Test Conversation",
        "created_at": "2025-01-01T00:00:00Z",
        "chat_messages": [
            {
                "uuid": message_id,
                "conversation_uuid": conversation_id,
                "sender": "human",
                "attachments": [
                    {
                        "type": "file",
                        # Missing file_name field
                        "file_type": "text/plain",
                        "file_size": 1024,
                        "content": "Test content",
                    },
                ],
                "text": "Here's a document",
                "created_at": "2025-01-01T00:00:00Z",
            }
        ],
    }

    # Create the conversations.json file
    conversations_file = claude_config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]), encoding="utf-8")

    # Process the conversation
    processor = ClaudeProcessor(claude_config.sources[0])
    result = processor.process(claude_config)

    # Check that the warning was logged but processing continued
    assert result.processed == 1

    # Check that the output file was created
    output_files = list(claude_config.sources[0].dest_dir.glob("*.md"))
    assert len(output_files) == 1


def test_empty_conversation(claude_config):
    """Test handling of empty conversation with no messages."""
    # Create a Claude export with no messages
    conversation_id = str(uuid.uuid4())

    conversation = {
        "uuid": conversation_id,
        "name": "Untitled Conversation",
        "created_at": "2025-01-01T00:00:00Z",
        "chat_messages": [],
    }

    # Create the conversations.json file
    conversations_file = claude_config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]), encoding="utf-8")

    # Process the conversation
    processor = ClaudeProcessor(claude_config.sources[0])
    result = processor.process(claude_config)

    # Check that the conversation was skipped
    assert result.skipped == 1
