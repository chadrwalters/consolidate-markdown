import copy
import os
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from PIL import Image, ImageDraw

from consolidate_markdown.config import GlobalConfig, ModelsConfig


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-live-api",
        action="store_true",
        default=False,
        help="run tests that make live API calls",
    )


def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "live_api: mark test as requiring live API access"
    )


def pytest_collection_modifyitems(config, items):
    """Skip live API tests unless explicitly enabled."""
    if not config.getoption("--run-live-api"):
        skip_live = pytest.mark.skip(reason="need --run-live-api option to run")
        for item in items:
            if "live_api" in item.keywords:
                item.add_marker(skip_live)


@pytest.fixture
def test_config(tmp_path) -> Path:
    """Create a test configuration file."""
    config_file = tmp_path / "test_config.toml"
    config_file.write_text(
        f"""
[global]
cm_dir = "{tmp_path / '.cm'}"
log_level = "INFO"
force_generation = false
no_image = true
openai_key = "test-key"

[[sources]]
type = "bear"
srcDir = "{tmp_path / 'bear'}"
destDir = "{tmp_path / 'output/bear'}"

[[sources]]
type = "xbookmarks"
srcDir = "{tmp_path / 'xbookmarks'}"
destDir = "{tmp_path / 'output/xbookmarks'}"
"""
    )
    return config_file


@pytest.fixture
def mock_openai() -> Generator:
    """Mock OpenAI API calls."""
    with patch("openai.OpenAI") as mock:
        mock_client = mock.return_value
        mock_response = mock_client.chat.completions.create.return_value
        mock_response.choices[0].message.content = "Test image description"
        yield mock


@pytest.fixture
def sample_docx(tmp_path) -> Path:
    """Create a sample DOCX file."""
    docx_path = tmp_path / "test.docx"
    docx_path.write_bytes(b"PK\x03\x04" + b"\x00" * 30)  # Minimal DOCX header
    return docx_path


@pytest.fixture
def sample_image(tmp_path) -> Path:
    """Create a sample image file."""
    image_path = tmp_path / "test.jpg"
    img = Image.new("RGB", (100, 100), color="white")
    img.save(image_path)
    return image_path


@pytest.fixture
def sample_bear_note(tmp_path) -> Path:
    """Create a sample Bear note with attachments."""
    note_dir = tmp_path / "bear"
    note_dir.mkdir()

    # Create main note
    note_file = note_dir / "Test Note.md"
    note_file.write_text(
        """# Test Note

This is a test note with attachments:
![test image](Test Note/image.jpg)
[document](Test Note/document.docx)
"""
    )

    # Create attachment folder
    attach_dir = note_dir / "Test Note"
    attach_dir.mkdir()

    # Add image attachment
    image_path = attach_dir / "image.jpg"
    img = Image.new("RGB", (100, 100), color="white")
    img.save(image_path)

    # Add document attachment
    doc_path = attach_dir / "document.docx"
    doc_path.write_bytes(b"PK\x03\x04" + b"\x00" * 30)

    return note_dir


@pytest.fixture
def sample_xbookmark(tmp_path) -> Path:
    """Create a sample X bookmark with media."""
    bookmark_dir = tmp_path / "xbookmarks" / "20240101_123456"
    bookmark_dir.mkdir(parents=True)

    # Create index.md
    index_file = bookmark_dir / "index.md"
    index_file.write_text(
        """**[User](https://x.com/user)**
Test tweet content
"""
    )

    # Add media
    image_path = bookmark_dir / "media.jpg"
    img = Image.new("RGB", (100, 100), color="white")
    img.save(image_path)

    return bookmark_dir.parent


@pytest.fixture
def test_image(tmp_path) -> Path:
    """Create a small test image for API testing."""
    image_path = tmp_path / "test.jpg"
    # Create a simple 100x100 test image
    image = Image.new("RGB", (100, 100), color="white")
    # Add some simple shapes to make it interesting for GPT
    draw = ImageDraw.Draw(image)
    draw.rectangle((30, 30, 70, 70), fill="blue")
    draw.ellipse((20, 20, 80, 80), outline="red", width=2)
    image.save(image_path, "JPEG")
    return image_path


@pytest.fixture
def code_screenshot(tmp_path) -> Path:
    """Use the actual code screenshot from fixtures."""
    source_path = Path("tests/fixtures/code.png")
    target_path = tmp_path / "code.png"
    import shutil

    shutil.copy(source_path, target_path)
    return target_path


@pytest.fixture
def ui_screenshot(tmp_path) -> Path:
    """Use the actual UI screenshot from fixtures."""
    source_path = Path("tests/fixtures/ui.png")
    target_path = tmp_path / "ui.png"
    import shutil

    shutil.copy(source_path, target_path)
    return target_path


@pytest.fixture
def text_editor_screenshot(tmp_path) -> Path:
    """Create a test image simulating a text editor screenshot."""
    image_path = tmp_path / "editor.jpg"
    # Create an image for text editor
    image = Image.new("RGB", (800, 600), color="#FFFFFF")
    draw = ImageDraw.Draw(image)

    # Draw editor background
    draw.rectangle((0, 0, 800, 600), fill="#FFFFFF")

    # Draw some text lines with different styles
    lines = [
        ("# Model Comparison Guide", "#000000"),
        ("", "#000000"),
        (
            "This guide helps you choose the right model for your image analysis needs.",
            "#333333",
        ),
        ("", "#000000"),
        ("## Model Overview", "#000000"),
        ("", "#000000"),
        ("The tool supports multiple vision models through OpenRouter:", "#333333"),
    ]

    y = 40
    for text, color in lines:
        draw.text((40, y), text, fill=color)
        y += 30

    image.save(image_path, "JPEG", quality=95)
    return image_path


@pytest.fixture
def global_config() -> GlobalConfig:
    """Create a base GlobalConfig for testing."""
    config = GlobalConfig()
    config.cm_dir = Path(".cm")
    config.log_level = "INFO"
    config.force_generation = False
    config.no_image = False
    return config


@pytest.fixture
def openai_live_config(global_config) -> GlobalConfig:
    """Configure OpenAI with API key from environment."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")
    global_config.api_provider = "openai"
    global_config.openai_key = os.getenv("OPENAI_API_KEY")
    return global_config


@pytest.fixture
def openrouter_live_config(global_config) -> GlobalConfig:
    """Create a test configuration for OpenRouter."""
    config = copy.deepcopy(global_config)
    config.api_provider = "openrouter"
    config.openrouter_key = "test-key"
    config.models = ModelsConfig(
        default_model="gpt-4o",  # Start with GPT-4 as default
        alternate_models={
            "gpt4": "gpt-4o",
            "gemini": "google/gemini-pro-vision-1.0",
            "yi": "yi/yi-vision-01",
            "blip": "deepinfra/blip",
            "llama": "meta/llama-3.2-90b-vision-instruct",
        },
    )
    return config
