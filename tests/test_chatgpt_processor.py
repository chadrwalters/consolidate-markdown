"""Tests for the ChatGPT export processor."""

import json

import pytest

from consolidate_markdown.config import Config, GlobalConfig, ModelsConfig, SourceConfig
from consolidate_markdown.processors.chatgpt import ChatGPTProcessor

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for testing."""
    src_dir = tmp_path / "source"
    dest_dir = tmp_path / "dest"
    markdown_dir = src_dir / "markdown_chats"

    # Create directories
    for d in [src_dir, dest_dir, markdown_dir]:
        d.mkdir(parents=True)

    # Create test files
    (markdown_dir / "20250101_Test_Chat.md").write_text("Test content 1")
    (markdown_dir / "20250102_Another_Chat.md").write_text("Test content 2")

    return {
        "src_dir": src_dir,
        "dest_dir": dest_dir,
        "markdown_dir": markdown_dir,
    }


@pytest.fixture
def config(tmp_path) -> Config:
    """Create test configuration."""
    src_dir = tmp_path / "chatgpt_export"
    src_dir.mkdir(parents=True)

    # Create markdown_chats directory
    markdown_dir = src_dir / "markdown_chats"
    markdown_dir.mkdir(parents=True)

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


def test_successful_copy(temp_dirs, config):
    """Test successful copying of markdown files."""
    # Create test files in source directory
    markdown_dir = config.sources[0].src_dir / "markdown_chats"
    markdown_dir.mkdir(parents=True, exist_ok=True)

    (markdown_dir / "20250101_Test_Chat.md").write_text("Test content 1")
    (markdown_dir / "20250102_Another_Chat.md").write_text("Test content 2")

    # Create conversations.json with test conversations
    conversations = [
        {
            "title": "Test Chat",
            "create_time": "2025-01-01T00:00:00Z",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test content 1"}],
        },
        {
            "title": "Another Chat",
            "create_time": "2025-01-02T00:00:00Z",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test content 2"}],
        },
    ]
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations), encoding="utf-8")

    processor = ChatGPTProcessor(config.sources[0])
    processor.process(config)

    # Check files were copied
    assert (config.sources[0].dest_dir / "20250101_Test_Chat.md").exists()
    assert (config.sources[0].dest_dir / "20250102_Another_Chat.md").exists()
