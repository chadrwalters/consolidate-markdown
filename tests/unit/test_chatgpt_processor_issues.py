import json

import pytest

from consolidate_markdown.config import Config, GlobalConfig, ModelsConfig, SourceConfig
from consolidate_markdown.processors.chatgpt import ChatGPTProcessor

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


@pytest.fixture
def chatgpt_config(tmp_path) -> Config:
    """Create test configuration for ChatGPT processor."""
    src_dir = tmp_path / "chatgpt_export"
    src_dir.mkdir(parents=True)

    dest_dir = tmp_path / "output"
    dest_dir.mkdir(parents=True)

    source_config = SourceConfig(
        type="chatgpt",
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
        openai_base_url=DEFAULT_OPENAI_BASE_URL,
        openrouter_base_url=DEFAULT_OPENROUTER_BASE_URL,
        models=ModelsConfig(
            default_model="gpt-4o",
            alternate_models={
                "gpt4": "gpt-4o",
                "gemini": "google/gemini-pro-vision-1.0",
            },
        ),
    )

    return Config(global_config=global_config, sources=[source_config])


def test_none_title_in_conversation(chatgpt_config):
    """Test handling of None title in conversation.

    This test reproduces the 'NoneType' object has no attribute 'replace' error.
    """
    # Create conversations.json with a conversation that has None as title
    conversations = [
        {
            "title": None,  # This will cause the error
            "create_time": "2025-01-01T00:00:00Z",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test content"}],
        }
    ]

    conversations_file = chatgpt_config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations), encoding="utf-8")

    # Process the conversation
    processor = ChatGPTProcessor(chatgpt_config.sources[0])
    result = processor.process(chatgpt_config)

    # Check that the error was handled and no exception was raised
    assert (
        "Error processing conversation: 'NoneType' object has no attribute 'replace'"
        not in result.errors
    )

    # Check that the conversation was processed with a default title
    output_files = list(chatgpt_config.sources[0].dest_dir.glob("*.md"))
    assert len(output_files) == 1

    # The file should contain "# Untitled" as the title
    content = output_files[0].read_text(encoding="utf-8")
    assert "# Untitled" in content


def test_missing_content_in_message(chatgpt_config):
    """Test handling of missing content in message."""
    # Create conversations.json with a message that has no content field
    conversations = [
        {
            "title": "Test Chat",
            "create_time": "2025-01-01T00:00:00Z",
            "model": "gpt-4",
            "messages": [
                {"role": "user"},  # Missing content field
                {"role": "assistant", "content": "Response content"},
            ],
        }
    ]

    conversations_file = chatgpt_config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations), encoding="utf-8")

    # Process the conversation
    processor = ChatGPTProcessor(chatgpt_config.sources[0])
    result = processor.process(chatgpt_config)

    # Check that the error was handled and no exception was raised
    assert "Error processing conversation:" not in result.errors

    # Check that the conversation was processed
    output_files = list(chatgpt_config.sources[0].dest_dir.glob("*.md"))
    assert len(output_files) == 1


def test_none_content_in_message(chatgpt_config):
    """Test handling of None content in message."""
    # Create conversations.json with a message that has None as content
    conversations = [
        {
            "title": "Test Chat",
            "create_time": "2025-01-01T00:00:00Z",
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": None},  # None content
                {"role": "assistant", "content": "Response content"},
            ],
        }
    ]

    conversations_file = chatgpt_config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations), encoding="utf-8")

    # Process the conversation
    processor = ChatGPTProcessor(chatgpt_config.sources[0])
    result = processor.process(chatgpt_config)

    # Check that the error was handled and no exception was raised
    assert "Error processing conversation:" not in result.errors

    # Check that the conversation was processed
    output_files = list(chatgpt_config.sources[0].dest_dir.glob("*.md"))
    assert len(output_files) == 1


def test_float_timestamp_in_conversation(chatgpt_config):
    """Test handling of float timestamp in conversation.

    This test reproduces the 'float' object has no attribute 'replace' error.
    """
    # Create conversations.json with a conversation that has a float timestamp
    conversations = [
        {
            "title": "Float Timestamp Test",
            "create_time": 1677649200.5,  # Float timestamp (2023-03-01 00:00:00.5)
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test content"}],
        }
    ]

    conversations_file = chatgpt_config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations), encoding="utf-8")

    # Process the conversation
    processor = ChatGPTProcessor(chatgpt_config.sources[0])
    result = processor.process(chatgpt_config)

    # Check that the error was handled and no exception was raised
    assert (
        "Error processing conversation: 'float' object has no attribute 'replace'"
        not in result.errors
    )

    # Check that the conversation was processed
    output_files = list(chatgpt_config.sources[0].dest_dir.glob("*.md"))
    assert len(output_files) == 1

    # The file should contain the title and a date from 2023
    content = output_files[0].read_text(encoding="utf-8")
    assert "# Float Timestamp Test" in content
    assert "Created: 2023-03-01" in content
