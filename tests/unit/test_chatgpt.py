"""Unit tests for ChatGPT processor."""

import json
from pathlib import Path
from typing import Any, Dict, List, Union

import pytest

from consolidate_markdown.attachments.processor import AttachmentProcessor
from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors.chatgpt import ChatGPTProcessor


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


@pytest.fixture
def sample_code_block_conversation() -> Dict[str, Any]:
    """Create a sample conversation with code blocks."""
    return {
        "title": "Code Examples",
        "create_time": "2024-02-15T10:00:00Z",
        "model": "gpt-4",
        "mapping": {
            "msg1": {
                "id": "msg1",
                "message": {
                    "author": {"role": "user"},
                    "content": "Show me a Python example of a decorator.",
                    "parent": None,
                },
            },
            "msg2": {
                "id": "msg2",
                "message": {
                    "author": {"role": "assistant"},
                    "content": [
                        {
                            "type": "text",
                            "text": "Here's an example of a timing decorator in Python:",
                        },
                        {
                            "type": "code",
                            "language": "python",
                            "text": """import functools
import time

def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)
    return "Done!"
""",
                        },
                        {"type": "text", "text": "And here's how you would use it:"},
                        {
                            "type": "code",
                            "language": "python",
                            "text": """result = slow_function()
print(result)  # Output: slow_function took 1.00 seconds\\nDone!""",
                        },
                    ],
                    "parent": "msg1",
                },
            },
        },
        "current_node": "msg2",
    }


@pytest.fixture
def sample_interactive_conversation() -> Dict[str, Any]:
    """Create a sample conversation with interactive elements."""
    return {
        "title": "Interactive Features",
        "create_time": "2024-02-16T11:00:00Z",
        "model": "gpt-4",
        "mapping": {
            "msg1": {
                "id": "msg1",
                "message": {
                    "author": {"role": "system"},
                    "content": "You are in Python REPL mode. Show step-by-step execution.",
                    "parent": None,
                },
            },
            "msg2": {
                "id": "msg2",
                "message": {
                    "author": {"role": "user"},
                    "content": "Calculate fibonacci(5)",
                    "parent": "msg1",
                },
            },
            "msg3": {
                "id": "msg3",
                "message": {
                    "author": {"role": "assistant"},
                    "content": [
                        {
                            "type": "tool_use",
                            "tool": "python_repl",
                            "input": "def fibonacci(n):\\n    if n <= 1:\\n        return n\\n    return fibonacci(n-1) + fibonacci(n-2)\\n\\nprint(fibonacci(5))",
                        },
                        {"type": "tool_result", "output": "5"},
                        {
                            "type": "text",
                            "text": "Let's break down the execution steps:\n1. fibonacci(5) calls fibonacci(4) + fibonacci(3)\n2. fibonacci(4) calls fibonacci(3) + fibonacci(2)\n3. And so on...",
                        },
                    ],
                    "parent": "msg2",
                },
            },
        },
        "current_node": "msg3",
    }


@pytest.fixture
def sample_rich_content_conversation() -> Dict[str, Any]:
    """Create a sample conversation with rich content types."""
    return {
        "title": "Rich Content Examples",
        "create_time": "2024-02-17T12:00:00Z",
        "model": "gpt-4",
        "mapping": {
            "msg1": {
                "id": "msg1",
                "message": {
                    "author": {"role": "user"},
                    "content": "Show me examples of tables, math equations, and diagrams.",
                    "parent": None,
                },
            },
            "msg2": {
                "id": "msg2",
                "message": {
                    "author": {"role": "assistant"},
                    "content": [
                        {"type": "text", "text": "Here's a comparison table:"},
                        {
                            "type": "table",
                            "headers": [
                                "Algorithm",
                                "Time Complexity",
                                "Space Complexity",
                            ],
                            "rows": [
                                ["Bubble Sort", "O(n²)", "O(1)"],
                                ["Quick Sort", "O(n log n)", "O(log n)"],
                                ["Merge Sort", "O(n log n)", "O(n)"],
                            ],
                        },
                        {"type": "text", "text": "Here's the quadratic formula:"},
                        {
                            "type": "math",
                            "latex": "x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}",
                        },
                        {"type": "text", "text": "And here's a simple flowchart:"},
                        {
                            "type": "mermaid",
                            "diagram": """graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B""",
                        },
                    ],
                    "parent": "msg1",
                },
            },
        },
        "current_node": "msg2",
    }


@pytest.fixture
def sample_advanced_files_conversation(config: Config) -> Dict[str, Any]:
    """Create a sample conversation with advanced file types."""
    # Create test files in the source directory
    export_dir = config.sources[0].src_dir
    files_dir = export_dir / "files"
    files_dir.mkdir(exist_ok=True)

    # Create test files with proper type hints
    test_files: Dict[str, Union[str, bytes]] = {
        "script.py": """def hello(name):
    print(f"Hello, {name}!")""",
        "config.yaml": """server:
  host: localhost
  port: 8080
  debug: true""",
        "data.json": """{
  "users": [
    {"name": "Alice", "role": "admin"},
    {"name": "Bob", "role": "user"}
  ]
}""",
        "archive.zip": b"fake zip data",  # Using bytes literal for binary data
    }

    for name, content in test_files.items():
        file_path = files_dir / name
        if isinstance(content, bytes):
            file_path.write_bytes(content)  # For binary data
        else:
            file_path.write_text(content)  # For text data

    return {
        "title": "Advanced File Types",
        "create_time": "2024-02-18T13:00:00Z",
        "model": "gpt-4",
        "mapping": {
            "msg1": {
                "id": "msg1",
                "message": {
                    "author": {"role": "user"},
                    "content": "Here are some different types of files to process.",
                    "parent": None,
                },
            },
            "msg2": {
                "id": "msg2",
                "message": {
                    "author": {"role": "assistant"},
                    "content": [
                        {"type": "text", "text": "I'll analyze each file:"},
                        {
                            "type": "file",
                            "file_url": {"url": str(files_dir / "script.py")},
                            "metadata": {"language": "python"},
                        },
                        {
                            "type": "file",
                            "file_url": {"url": str(files_dir / "config.yaml")},
                            "metadata": {"language": "yaml"},
                        },
                        {
                            "type": "file",
                            "file_url": {"url": str(files_dir / "data.json")},
                            "metadata": {"language": "json"},
                        },
                        {
                            "type": "file",
                            "file_url": {"url": str(files_dir / "archive.zip")},
                            "metadata": {"type": "archive"},
                        },
                    ],
                    "parent": "msg1",
                },
            },
        },
        "current_node": "msg2",
    }


def test_code_blocks(
    config: Config,
    temp_output_dir: Path,
    sample_code_block_conversation: Dict[str, Any],
):
    """Test processing conversation with code blocks."""
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(
        json.dumps([sample_code_block_conversation]), encoding="utf-8"
    )

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 1
    assert result.errors == []

    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 1
    content = output_files[0].read_text(encoding="utf-8")

    # Check code block formatting
    assert "```python" in content
    assert "def timer(func):" in content
    assert "```" in content
    assert "And here's how you would use it:" in content


def test_interactive_elements(
    config: Config,
    temp_output_dir: Path,
    sample_interactive_conversation: Dict[str, Any],
):
    """Test processing conversation with interactive elements."""
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(
        json.dumps([sample_interactive_conversation]), encoding="utf-8"
    )

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 1
    assert result.errors == []

    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 1
    content = output_files[0].read_text(encoding="utf-8")

    # Check interactive elements
    assert "## System" in content
    assert "Python REPL mode" in content
    assert "Tool: python_repl" in content
    assert "Output: 5" in content


def test_rich_content(
    config: Config,
    temp_output_dir: Path,
    sample_rich_content_conversation: Dict[str, Any],
):
    """Test processing conversation with rich content."""
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(
        json.dumps([sample_rich_content_conversation]), encoding="utf-8"
    )

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 1
    assert result.errors == []

    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 1
    content = output_files[0].read_text(encoding="utf-8")

    # Check rich content formatting
    assert "| Algorithm | Time Complexity | Space Complexity |" in content
    assert "x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}" in content
    assert "```mermaid" in content
    assert "graph TD" in content


def test_advanced_files(
    config: Config,
    temp_output_dir: Path,
    sample_advanced_files_conversation: Dict[str, Any],
):
    """Test processing conversation with advanced file types."""
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(
        json.dumps([sample_advanced_files_conversation]), encoding="utf-8"
    )

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 1
    assert result.errors == []
    assert result.documents_processed == 4

    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 1
    content = output_files[0].read_text(encoding="utf-8")

    # Check file handling
    assert "```python" in content
    assert "def hello(name):" in content
    assert "```yaml" in content
    assert "host: localhost" in content
    assert "```json" in content
    assert '"users":' in content
    assert "[Archive: archive.zip]" in content


def test_process_conversation_with_attachments(tmp_path: Path) -> None:
    """Test processing a conversation with attachments."""
    # Create test conversation directory
    conv_dir = tmp_path / "conversation"
    conv_dir.mkdir(parents=True)

    # Create attachments directory
    attachments_dir = conv_dir / "attachments"
    attachments_dir.mkdir()

    # Create test image
    test_jpg = attachments_dir / "test.jpg"
    test_jpg.write_bytes(b"fake jpg data")

    # Create test document
    test_pdf = attachments_dir / "test.pdf"
    test_pdf.write_bytes(b"fake pdf data")

    # Create conversations.json
    conversations = [
        {
            "title": "Test Conversation",
            "messages": [
                {
                    "role": "user",
                    "content": "Here are some files",
                    "attachments": [
                        {"name": "test.jpg", "mime_type": "image/jpeg"},
                        {"name": "test.pdf", "mime_type": "application/pdf"},
                    ],
                }
            ],
        }
    ]

    conversations_file = conv_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations))

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)

    # Create processor and process
    source_config = SourceConfig(
        type="chatgptexport",
        src_dir=conv_dir,
        dest_dir=output_dir,
        index_filename="index.md",
    )
    config = Config(
        global_config=GlobalConfig(
            cm_dir=tmp_path / ".cm",
            log_level="INFO",
            force_generation=False,
            no_image=True,
            openai_key=None,
        ),
        sources=[source_config],
    )
    processor = ChatGPTProcessor(source_config=source_config)
    result = processor.process(config)

    # Verify attachments were processed
    assert result.processed == 1
    output_file = output_dir / "00000000 - Test_Conversation.md"
    content = output_file.read_text()

    # Check for image attachment
    assert "<!-- EMBEDDED IMAGE: test.jpg -->" in content
    assert "![test.jpg](attachments/test.jpg)" in content

    # Check for PDF attachment
    assert "<!-- EMBEDDED PDF: test.pdf -->" in content
    assert "[View PDF](attachments/test.pdf)" in content
