"""Unit tests for ChatGPT processor."""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from consolidate_markdown.attachments.processor import AttachmentProcessor
from consolidate_markdown.config import (DEFAULT_OPENAI_BASE_URL,
                                         DEFAULT_OPENROUTER_BASE_URL, Config,
                                         GlobalConfig, ModelsConfig,
                                         SourceConfig)
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
def sample_conversation_with_attachments() -> Dict[str, Any]:
    """Create a sample conversation with attachments."""
    return {
        "title": "Conversation With Attachments",
        "create_time": "2024-02-01T12:00:00Z",
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": "Here's an image:", "type": "text"},
                    {"image": "test.png", "type": "image"},
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {"text": "I see the image. Here's a document:", "type": "text"},
                    {"file": "test.pdf", "type": "file"},
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
def config(temp_output_dir: Path) -> Config:
    """Create test configuration."""
    # Create required directories
    chatgpt_export_dir = temp_output_dir / "chatgpt_export"
    chatgpt_export_dir.mkdir(parents=True, exist_ok=True)
    cm_dir = temp_output_dir / ".cm"
    cm_dir.mkdir(parents=True, exist_ok=True)

    # Create empty conversations.json
    conversations_file = chatgpt_export_dir / "conversations.json"
    conversations_file.write_text("[]", encoding="utf-8")

    return Config(
        global_config=GlobalConfig(
            cm_dir=cm_dir,
            log_level="INFO",
            force_generation=False,
            no_image=True,  # Disable image processing for unit tests
            openai_key=None,
            api_provider="openrouter",
            openrouter_key="test-key",
            openai_base_url=DEFAULT_OPENAI_BASE_URL,
            openrouter_base_url=DEFAULT_OPENROUTER_BASE_URL,
            models=ModelsConfig(
                default_model="gpt-4o",
                alternate_models={
                    "gpt4": "gpt-4o",
                    "gemini": "google/gemini-pro-vision-1.0",
                    "yi": "yi/yi-vision-01",
                    "blip": "deepinfra/blip",
                    "llama": "meta/llama-3.2-90b-vision-instruct",
                },
            ),
        ),
        sources=[
            SourceConfig(
                type="chatgptexport",
                src_dir=chatgpt_export_dir,
                dest_dir=temp_output_dir,  # Use temp_output_dir directly
                index_filename="index.md",
            )
        ],
    )


def test_processor_initialization(config: Config):
    """Test processor initialization."""
    processor = ChatGPTProcessor(config.sources[0])
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

    # Update conversations.json with single conversation
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([sample_conversation]), encoding="utf-8")

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 1
    assert result.errors == []

    # Check output file exists
    output_files = list(output_dir.glob("*.md"))
    assert len(output_files) == 1

    # Verify content
    content = output_files[0].read_text(encoding="utf-8")
    assert sample_conversation["title"] in content
    assert "Created: 2024-01-30" in content
    assert "Model: gpt-4" in content
    assert "Hello, how are you?" in content
    assert "I'm doing well, thank you for asking!" in content


def test_conversation_with_attachments(
    config: Config,
    temp_output_dir: Path,
    sample_conversation_with_attachments: Dict[str, Any],
):
    """Test processing conversation with attachments."""
    # Create output directory and ensure it exists
    output_dir = config.sources[0].dest_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create test directories
    images_dir = config.sources[0].src_dir / "attachments"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Create attachments directory in output
    attachments_dir = output_dir / "attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)

    # Create test image file with valid PNG header
    image_path = images_dir / "test.png"
    image_path.write_bytes(
        bytes.fromhex("89504E470D0A1A0A0000000D49484452") + b"\x00" * 100
    )

    # Create test PDF file
    pdf_path = images_dir / "test.pdf"
    pdf_path.write_bytes(
        b"%PDF-1.4\n%\x93\x8c\x8b\x9e\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    )

    # Update sample conversation to include file paths
    sample_conversation_with_attachments["messages"][0]["attachments"] = [
        {"name": "test.png", "mime_type": "image/png", "file_path": str(image_path)},
        {
            "name": "test.pdf",
            "mime_type": "application/pdf",
            "file_path": str(pdf_path),
        },
    ]

    # Update conversations.json with attachment test data
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(
        json.dumps([sample_conversation_with_attachments], ensure_ascii=True),
        encoding="utf-8",
    )

    # Ensure image processing is disabled for unit tests
    config.global_config.no_image = True

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 1
    assert result.errors == []
    assert result.images_processed == 0  # No image processing in unit tests
    assert (
        result.documents_processed == 2
    )  # Both attachments are processed as documents

    # Check output file exists
    output_files = list(output_dir.glob("*.md"))
    assert len(output_files) == 1

    # Verify content
    content = output_files[0].read_text(encoding="utf-8")
    assert (
        "<!-- EMBEDDED PDF: test.png -->" in content
    )  # Image is treated as PDF when no_image is True
    assert "<!-- EMBEDDED PDF: test.pdf -->" in content


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
    # Create test conversations
    conversations = [
        {
            "title": "Test Conversation 1",
            "create_time": "2024-01-01T00:00:00Z",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        },
        {
            "title": "Test Conversation 2",
            "create_time": "2024-01-02T00:00:00Z",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hi"}],
        },
        {
            "title": "Test Conversation 3",
            "create_time": "2024-01-03T00:00:00Z",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hey"}],
        },
    ]

    # Write conversations to file
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations), encoding="utf-8")

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 3
    assert result.errors == []

    # Check output files exist with correct format
    output_files = sorted(list(temp_output_dir.glob("*.md")))
    assert len(output_files) == 3
    assert output_files[0].name == "20240101 - Test_Conversation_1.md"
    assert output_files[1].name == "20240102 - Test_Conversation_2.md"
    assert output_files[2].name == "20240103 - Test_Conversation_3.md"


def test_multiple_conversations(config: Config, temp_output_dir: Path):
    """Test processing multiple conversations."""
    # Create test conversations
    conversations = [
        {
            "title": "First Conversation",
            "create_time": "2024-01-01T00:00:00Z",
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        },
        {
            "title": "Second Conversation",
            "create_time": "2024-01-02T00:00:00Z",
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "How are you?"},
                {"role": "assistant", "content": "I'm doing well, thanks!"},
            ],
        },
        {
            "title": "Third Conversation",
            "create_time": "2024-01-03T00:00:00Z",
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

    # Check output files exist with correct format
    output_files = sorted(list(temp_output_dir.glob("*.md")))
    assert len(output_files) == 3

    # Verify content of each file
    for i, file in enumerate(output_files):
        content = file.read_text(encoding="utf-8")
        title = str(conversations[i]["title"])
        assert title in content
        assert "Created: 2024-01-0" in content
        assert "Model: gpt-4" in content
        assert "## User" in content
        assert "## Assistant" in content


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
    # Create test directories
    files_dir = config.sources[0].src_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    # Create test files
    test_files = {
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
        "archive.zip": b"PK\x03\x04\x14\x00\x00\x00\x08\x00",  # Minimal ZIP header
    }

    # Write test files
    for name, content in test_files.items():
        file_path = files_dir / name
        if isinstance(content, bytes):
            file_path.write_bytes(content)
        else:
            file_path.write_text(str(content), encoding="utf-8")

    return {
        "title": "Advanced File Types",
        "create_time": "2024-02-18T13:00:00Z",
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Here are some different types of files to process.",
                    },
                    {
                        "type": "file",
                        "file_path": str(files_dir / "script.py"),
                        "metadata": {"language": "python"},
                    },
                    {
                        "type": "file",
                        "file_path": str(files_dir / "config.yaml"),
                        "metadata": {"language": "yaml"},
                    },
                    {
                        "type": "file",
                        "file_path": str(files_dir / "data.json"),
                        "metadata": {"language": "json"},
                    },
                    {
                        "type": "file",
                        "file_path": str(files_dir / "archive.zip"),
                        "metadata": {"mime_type": "application/zip"},
                    },
                ],
            },
        ],
    }


def test_code_blocks(
    config: Config,
    temp_output_dir: Path,
    sample_code_block_conversation: Dict[str, Any],
):
    """Test processing conversation with code blocks."""
    # Create test conversation with code blocks
    conversation = {
        "title": "Code Examples",
        "create_time": "2024-02-15T10:00:00Z",
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": "Can you show me some Python code examples?",
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Here's a simple Python function that demonstrates timing:",
                    },
                    {
                        "type": "code",
                        "language": "python",
                        "text": """import time

def slow_function():
    time.sleep(1)
    print("Done!")

# Time the function
start = time.time()
slow_function()
end = time.time()
print(f"slow_function took {end - start:.2f} seconds")""",
                    },
                ],
            },
        ],
    }

    # Write conversation to file
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]), encoding="utf-8")

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 1
    assert result.errors == []

    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 1

    # Verify content
    content = output_files[0].read_text(encoding="utf-8")
    assert "# Code Examples" in content
    assert "Created: 2024-02-15" in content
    assert "Model: gpt-4" in content
    assert "## User" in content
    assert "Can you show me some Python code examples?" in content
    assert "## Assistant" in content
    assert "Here's a simple Python function that demonstrates timing:" in content
    assert "import time" in content
    assert "def slow_function():" in content


def test_interactive_elements(
    config: Config,
    temp_output_dir: Path,
    sample_interactive_conversation: Dict[str, Any],
):
    """Test processing conversation with interactive elements."""
    # Create test conversation with interactive elements
    conversation = {
        "title": "Interactive Examples",
        "create_time": "2024-02-16T11:00:00Z",
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": "Can you explain recursion with an example?",
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Let me explain recursion using the Fibonacci sequence as an example.",
                    },
                    {
                        "type": "code",
                        "language": "python",
                        "text": """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)""",
                    },
                    {
                        "type": "text",
                        "text": """Here's how it works:
1. fibonacci(5) calls fibonacci(4) + fibonacci(3)
2. fibonacci(4) calls fibonacci(3) + fibonacci(2)
3. And so on...""",
                    },
                    {
                        "type": "mermaid",
                        "diagram": """graph TD
    A[fibonacci(5)] --> B[fibonacci(4)]
    A --> C[fibonacci(3)]
    B --> D[fibonacci(3)]
    B --> E[fibonacci(2)]""",
                    },
                ],
            },
        ],
    }

    # Write conversation to file
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]), encoding="utf-8")

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 1
    assert result.errors == []

    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 1

    # Verify content
    content = output_files[0].read_text(encoding="utf-8")
    assert "# Interactive Examples" in content
    assert "Created: 2024-02-16" in content
    assert "Model: gpt-4" in content
    assert "## User" in content
    assert "Can you explain recursion with an example?" in content
    assert "## Assistant" in content
    assert "Let me explain recursion using the Fibonacci sequence" in content
    assert "def fibonacci(n):" in content
    assert "return fibonacci(n-1) + fibonacci(n-2)" in content


def test_rich_content(
    config: Config,
    temp_output_dir: Path,
    sample_rich_content_conversation: Dict[str, Any],
):
    """Test processing conversation with rich content."""
    # Create test conversation with rich content
    conversation = {
        "title": "Rich Content Examples",
        "create_time": "2024-02-17T12:00:00Z",
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": "Can you show me different types of rich content?",
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Here are examples of different types of rich content:",
                    },
                    {
                        "type": "math",
                        "latex": "E = mc^2",
                    },
                    {
                        "type": "table",
                        "headers": ["Name", "Value"],
                        "rows": [
                            ["Alpha", 1],
                            ["Beta", 2],
                            ["Gamma", 3],
                        ],
                    },
                    {
                        "type": "mermaid",
                        "diagram": """flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B""",
                    },
                ],
            },
        ],
    }

    # Write conversation to file
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]), encoding="utf-8")

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 1
    assert result.errors == []

    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 1

    # Verify content
    content = output_files[0].read_text(encoding="utf-8")
    assert "# Rich Content Examples" in content
    assert "Created: 2024-02-17" in content
    assert "Model: gpt-4" in content
    assert "## User" in content
    assert "Can you show me different types of rich content?" in content
    assert "## Assistant" in content
    assert "Here are examples of different types of rich content:" in content
    assert "$$E = mc^2$$" in content
    assert "| Name | Value |" in content
    assert "| Alpha | 1 |" in content
    assert "```mermaid" in content
    assert "flowchart TD" in content
    assert "```" in content


def test_advanced_files(
    config: Config,
    temp_output_dir: Path,
    sample_advanced_files_conversation: Dict[str, Any],
):
    """Test processing conversation with advanced file types."""
    # Create test directories
    files_dir = config.sources[0].src_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    # Create test files
    test_files = {
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
        "archive.zip": b"PK\x03\x04\x14\x00\x00\x00\x08\x00",  # Minimal ZIP header
    }

    # Write test files
    for name, content in test_files.items():
        file_path = files_dir / name
        if isinstance(content, bytes):
            file_path.write_bytes(content)
        else:
            file_path.write_text(str(content), encoding="utf-8")

    # Create test conversation
    conversation = {
        "title": "Advanced File Types",
        "create_time": "2024-02-18T13:00:00Z",
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Here are some different types of files to process.",
                    },
                    {
                        "type": "file",
                        "file_path": str(files_dir / "script.py"),
                        "metadata": {"language": "python"},
                    },
                    {
                        "type": "file",
                        "file_path": str(files_dir / "config.yaml"),
                        "metadata": {"language": "yaml"},
                    },
                    {
                        "type": "file",
                        "file_path": str(files_dir / "data.json"),
                        "metadata": {"language": "json"},
                    },
                    {
                        "type": "file",
                        "file_path": str(files_dir / "archive.zip"),
                        "metadata": {"mime_type": "application/zip"},
                    },
                ],
            },
        ],
    }

    # Write conversation to file
    conversations_file = config.sources[0].src_dir / "conversations.json"
    conversations_file.write_text(json.dumps([conversation]), encoding="utf-8")

    processor = ChatGPTProcessor(config.sources[0])
    result = processor.process(config)

    assert result.processed == 1
    assert result.errors == []
    assert result.documents_processed == 4

    output_files = list(temp_output_dir.glob("*.md"))
    assert len(output_files) == 1

    # Verify content
    content = output_files[0].read_text(encoding="utf-8")
    assert "# Advanced File Types" in content
    assert "Created: 2024-02-18" in content
    assert "Model: gpt-4" in content
    assert "## User" in content
    assert "Here are some different types of files to process." in content

    # Check Python file content
    assert "```python" in content
    assert "def hello(name):" in content
    assert "```" in content

    # Check YAML file content
    assert "```yaml" in content
    assert "host: localhost" in content
    assert "```" in content

    # Check JSON file content
    assert "```json" in content
    assert '"name": "Alice"' in content
    assert "```" in content

    # Check ZIP file handling
    assert "[Archive: archive.zip]" in content


def test_process_conversation_with_attachments(tmp_path: Path) -> None:
    """Test processing a conversation with attachments."""
    # Create test conversation directory
    conv_dir = tmp_path / "conversation"
    conv_dir.mkdir(parents=True)

    # Create attachments directory in both source and output
    src_attachments_dir = conv_dir / "attachments"
    src_attachments_dir.mkdir()

    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)
    out_attachments_dir = output_dir / "attachments"
    out_attachments_dir.mkdir(parents=True)

    # Create test image with valid JPEG header
    test_jpg = src_attachments_dir / "test.jpg"
    test_jpg.write_bytes(
        bytes.fromhex("FFD8FFE000104A46494600010100000100010000FFDB004300")
        + b"\x00" * 100
    )

    # Create test document
    test_pdf = src_attachments_dir / "test.pdf"
    test_pdf.write_bytes(
        b"%PDF-1.4\n%\x93\x8c\x8b\x9e\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    )

    # Create conversations.json
    conversations = [
        {
            "title": "Test Conversation",
            "create_time": "2024-01-01T00:00:00Z",
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": "Here are some files",
                    "attachments": [
                        {
                            "name": "test.jpg",
                            "mime_type": "image/jpeg",
                            "file_path": str(test_jpg),
                        },
                        {
                            "name": "test.pdf",
                            "mime_type": "application/pdf",
                            "file_path": str(test_pdf),
                        },
                    ],
                }
            ],
        }
    ]

    conversations_file = conv_dir / "conversations.json"
    conversations_file.write_text(json.dumps(conversations), encoding="utf-8")

    # Create source config and processor
    source_config = SourceConfig(
        type="chatgptexport",
        src_dir=conv_dir,
        dest_dir=output_dir,
        index_filename="index.md",
    )

    # Create global config with image processing disabled
    global_config = GlobalConfig(
        cm_dir=tmp_path / ".cm",
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

    config = Config(global_config=global_config, sources=[source_config])
    processor = ChatGPTProcessor(source_config=source_config)
    result = processor.process(config)

    # Verify attachments were processed
    assert result.processed == 1
    assert result.errors == []
    assert result.images_processed == 0  # No image processing in unit tests
    assert (
        result.documents_processed == 2
    )  # Both attachments are processed as documents
    output_file = output_dir / "20240101 - Test_Conversation.md"
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")

    # Check for image attachment (treated as PDF when no_image is True)
    assert "<!-- EMBEDDED PDF: test.jpg -->" in content
    assert "<!-- EMBEDDED PDF: test.pdf -->" in content
