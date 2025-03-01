import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors.bear import BearProcessor


@pytest.fixture
def image_config(tmp_path) -> Config:
    """Create test configuration for image processing."""
    src_dir = tmp_path / "bear_notes"
    src_dir.mkdir(parents=True)

    dest_dir = tmp_path / "output"
    dest_dir.mkdir(parents=True)

    source_config = SourceConfig(
        type="bear",
        src_dir=src_dir,
        dest_dir=dest_dir,
        index_filename="index.md",
    )

    global_config = GlobalConfig(
        cm_dir=dest_dir,
        log_level="INFO",
        force_generation=False,
        no_image=False,  # Enable image processing
        api_provider="openrouter",
        openrouter_key="test-key",
    )

    return Config(global_config=global_config, sources=[source_config])


@pytest.fixture
def gif_image(tmp_path) -> Path:
    """Create a sample GIF image file."""
    # Create a minimal GIF file
    gif_path = tmp_path / "test.gif"

    # Write a minimal GIF header
    with open(gif_path, "wb") as f:
        # GIF header
        f.write(b"GIF89a")
        # Logical Screen Descriptor
        f.write(b"\x01\x00\x01\x00\x00\x00\x00")
        # Global Color Table
        f.write(b"\xff\xff\xff\x00\x00\x00")
        # Trailer
        f.write(b";")

    return gif_path


def test_gif_image_processing(image_config, gif_image, tmp_path):
    """Test handling of GIF image format."""
    # Create a Bear note with a GIF attachment
    bear_notes_dir = tmp_path / "bear_notes"
    bear_notes_dir.mkdir(parents=True, exist_ok=True)

    # Create the note file directly in the bear_notes directory
    note_file = bear_notes_dir / "test_note.md"
    note_file.write_text(
        "# Test Note\n\nThis is a test note with a GIF attachment.\n\n![GIF](test_note/unknown.gif)"
    )

    # Create the attachment directory
    attachment_dir = bear_notes_dir / "test_note"
    attachment_dir.mkdir(parents=True, exist_ok=True)

    # Copy the GIF to the attachment directory
    attachment_path = attachment_dir / "unknown.gif"
    shutil.copy(gif_image, attachment_path)

    # Update the source directory in the config to point to the bear_notes directory
    image_config.sources[0].src_dir = bear_notes_dir
    print(f"Source directory: {image_config.sources[0].src_dir}")
    print(
        f"Files in source directory: {list(image_config.sources[0].src_dir.glob('*'))}"
    )
    print(f"Note file exists: {note_file.exists()}")
    print(f"Attachment directory exists: {attachment_dir.exists()}")
    print(f"Attachment file exists: {attachment_path.exists()}")

    # Mock the API call for image description
    with patch(
        "consolidate_markdown.attachments.gpt.GPTProcessor.describe_image"
    ) as mock_process:
        mock_process.return_value = "This is a GIF image"

        # Process the note
        processor = BearProcessor(image_config.sources[0])

        # Process the note
        result = processor.process(image_config)

        # Check that the note was processed
        assert result.processed == 1
        assert result.errors == []

        # Check that the output file exists
        output_file = image_config.sources[0].dest_dir / "test_note.md"
        assert output_file.exists()

        # With the new behavior, attachments are not copied to an attachments directory
        # but instead referenced in comments in the markdown file
        content = output_file.read_text()

        # Check for image comment reference
        assert "<!-- ATTACHMENT: IMAGE: unknown.gif" in content
        assert "This is a GIF image" in content  # GPT description should be included

        # The attachments directory should not exist anymore
        attachments_dir = image_config.sources[0].dest_dir / "attachments"
        assert not attachments_dir.exists()


def test_missing_attachment(image_config, tmp_path):
    """Test handling of missing attachment."""
    # Create a Bear note with a reference to a missing attachment
    bear_notes_dir = tmp_path / "bear_notes"
    bear_notes_dir.mkdir(parents=True, exist_ok=True)

    # Create the note file directly in the bear_notes directory
    note_file = bear_notes_dir / "test_note.md"
    note_file.write_text(
        "# Test Note\n\nThis is a test note with a missing attachment: ![missing](missing.pdf)"
    )

    # Update the source directory in the config to point to the bear_notes directory
    image_config.sources[0].src_dir = bear_notes_dir

    # Process the note
    processor = BearProcessor(image_config.sources[0])
    result = processor.process(image_config)

    # Check that the note was processed
    assert result.processed == 1

    # Check that the output file exists
    output_file = image_config.sources[0].dest_dir / "test_note.md"
    assert output_file.exists()

    # Check that the output file contains a warning about the missing attachment
    content = output_file.read_text()
    assert "missing.pdf" in content
    assert "not found" in content.lower() or "missing" in content.lower()


def test_unsupported_image_format(image_config, tmp_path):
    """Test handling of unsupported image format."""
    # Create a Bear note with an unsupported file type
    bear_notes_dir = tmp_path / "bear_notes"
    bear_notes_dir.mkdir(parents=True, exist_ok=True)

    # Create the note file directly in the bear_notes directory
    note_file = bear_notes_dir / "test_note.md"
    note_file.write_text(
        "# Test Note\n\nThis is a test note with an unsupported file: [file](test.xyz)"
    )

    # Create the attachment directory
    attachment_dir = bear_notes_dir / "test_note"
    attachment_dir.mkdir(parents=True, exist_ok=True)

    # Create a dummy unsupported file
    unsupported_file = attachment_dir / "test.xyz"
    unsupported_file.write_text("This is a test file with an unsupported extension")

    # Update the source directory in the config to point to the bear_notes directory
    image_config.sources[0].src_dir = bear_notes_dir

    # Process the note
    processor = BearProcessor(image_config.sources[0])
    result = processor.process(image_config)

    # Check that the note was processed
    assert result.processed == 1

    # Check that the output file exists
    output_file = image_config.sources[0].dest_dir / "test_note.md"
    assert output_file.exists()

    # With the new behavior, attachments are not copied to an attachments directory
    # but instead referenced in comments in the markdown file

    # Check that the output file contains a reference to the attachment
    content = output_file.read_text()
    assert "test.xyz" in content

    # The attachments directory should not exist anymore
    attachments_dir = image_config.sources[0].dest_dir / "attachments"
    assert not attachments_dir.exists()
