import os
import pytest
from pathlib import Path
from typing import Generator
from unittest.mock import patch

@pytest.fixture
def test_config(tmp_path) -> Path:
    """Create a test configuration file."""
    config_file = tmp_path / "test_config.toml"
    config_file.write_text(f"""
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
""")
    return config_file

@pytest.fixture
def mock_openai() -> Generator:
    """Mock OpenAI API calls."""
    with patch('openai.OpenAI') as mock:
        mock_client = mock.return_value
        mock_response = mock_client.chat.completions.create.return_value
        mock_response.choices[0].message.content = "Test image description"
        yield mock

@pytest.fixture
def sample_docx(tmp_path) -> Path:
    """Create a sample DOCX file."""
    docx_path = tmp_path / "test.docx"
    docx_path.write_bytes(b'PK\x03\x04' + b'\x00' * 30)  # Minimal DOCX header
    return docx_path

@pytest.fixture
def sample_image(tmp_path) -> Path:
    """Create a sample image file."""
    from PIL import Image

    image_path = tmp_path / "test.jpg"
    img = Image.new('RGB', (100, 100), color='white')
    img.save(image_path)
    return image_path

@pytest.fixture
def sample_bear_note(tmp_path) -> Path:
    """Create a sample Bear note with attachments."""
    note_dir = tmp_path / "bear"
    note_dir.mkdir()

    # Create main note
    note_file = note_dir / "Test Note.md"
    note_file.write_text("""# Test Note

This is a test note with attachments:
![test image](Test Note/image.jpg)
[document](Test Note/document.docx)
""")

    # Create attachment folder
    attach_dir = note_dir / "Test Note"
    attach_dir.mkdir()

    # Add image attachment
    image_path = attach_dir / "image.jpg"
    img = Image.new('RGB', (100, 100), color='white')
    img.save(image_path)

    # Add document attachment
    doc_path = attach_dir / "document.docx"
    doc_path.write_bytes(b'PK\x03\x04' + b'\x00' * 30)

    return note_dir

@pytest.fixture
def sample_xbookmark(tmp_path) -> Path:
    """Create a sample X bookmark with media."""
    bookmark_dir = tmp_path / "xbookmarks" / "20240101_123456"
    bookmark_dir.mkdir(parents=True)

    # Create index.md
    index_file = bookmark_dir / "index.md"
    index_file.write_text("""**[User](https://x.com/user)**
Test tweet content
""")

    # Add media
    image_path = bookmark_dir / "media.jpg"
    img = Image.new('RGB', (100, 100), color='white')
    img.save(image_path)

    return bookmark_dir.parent
