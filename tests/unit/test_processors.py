"""Test processors."""

from pathlib import Path
from unittest.mock import patch

import pytest

from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors.bear import BearProcessor
from consolidate_markdown.processors.xbookmarks import XBookmarksProcessor

# Constants
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_bear_basic_note(tmp_path):
    """Test processing a basic Bear note without attachments"""
    source_dir = tmp_path / "bear"
    source_dir.mkdir()
    note_path = source_dir / "basic_note.md"
    note_path.write_text("# Test Note\nThis is a basic note.")

    source_config = SourceConfig(
        type="bear", src_dir=source_dir, dest_dir=tmp_path / "output"
    )
    global_config = GlobalConfig(
        cm_dir=tmp_path / ".cm",
        no_image=True,  # Disable GPT for basic test
    )
    config = Config(global_config=global_config, sources=[source_config])

    processor = BearProcessor(source_config)
    result = processor.process(config)

    # Verify detailed stats
    assert result.processed == 1
    assert result.regenerated == 1
    assert result.from_cache == 0
    assert result.skipped == 0
    assert result.images_processed == 0
    assert result.documents_processed == 0
    assert result.errors == []
    assert (tmp_path / "output" / "basic_note.md").exists()
    assert "# Test Note" in (tmp_path / "output" / "basic_note.md").read_text()


def test_bear_note_with_attachments(tmp_path):
    """Test processing a Bear note with image and document attachments"""
    source_dir = tmp_path / "bear"
    source_dir.mkdir()

    # Create test attachments
    attachments_dir = source_dir / "note_with_attachments"
    attachments_dir.mkdir()

    # Image attachment
    test_image = attachments_dir / "test.png"
    # Create a minimal valid PNG file
    minimal_png = (
        b"\x89PNG\r\n\x1a\n"  # PNG signature
        b"\x00\x00\x00\x0d"  # IHDR chunk length
        b"IHDR"  # IHDR chunk type
        b"\x00\x00\x00\x01"  # Width: 1
        b"\x00\x00\x00\x01"  # Height: 1
        b"\x08\x06\x00\x00\x00"  # Bit depth, color type, compression, filter, interlace
        b"\x1f\x15\xc4\x89"  # CRC
        b"\x00\x00\x00\x00"  # IDAT chunk length
        b"IDAT"  # IDAT chunk type
        b"\x08\x1d\x3a\x7e"  # CRC
        b"\x00\x00\x00\x00"  # IEND chunk length
        b"IEND"  # IEND chunk type
        b"\xae\x42\x60\x82"  # CRC
    )
    test_image.write_bytes(minimal_png)

    # Document attachment
    test_doc = attachments_dir / "test.pdf"
    # Create a minimal valid PDF file
    minimal_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
178
%%EOF"""
    test_doc.write_bytes(minimal_pdf)

    note_path = source_dir / "note_with_attachments.md"
    note_path.write_text(
        f"""# Note with Attachments
![test image]({test_image})
[test doc]({test_doc})<!-- {{"embed":"true"}} -->"""
    )

    source_config = SourceConfig(
        type="bear", src_dir=source_dir, dest_dir=tmp_path / "output"
    )
    global_config = GlobalConfig(
        cm_dir=tmp_path / ".cm",
        no_image=True,  # Disable GPT for basic test
        api_provider="openrouter",  # Use OpenRouter as provider
        openrouter_key="test-key",  # Add test key
    )
    config = Config(global_config=global_config, sources=[source_config])

    processor = BearProcessor(source_config)
    result = processor.process(config)

    # Verify detailed stats
    assert result.processed == 1
    assert result.regenerated == 1
    assert result.from_cache == 0
    assert result.skipped == 0
    assert result.images_processed == 1
    assert result.images_generated == 1
    assert result.documents_processed == 1
    assert result.documents_generated == 1
    assert result.errors == []

    # Verify output files
    output_file = tmp_path / "output" / "note_with_attachments.md"
    assert output_file.exists()

    # With the new behavior, attachments are not copied to an attachments directory
    # but instead referenced in comments in the markdown file
    content = output_file.read_text()

    # Check for image comment reference
    assert "<!-- ATTACHMENT: IMAGE: test.png" in content

    # Check for document comment reference
    assert (
        "<!-- ATTACHMENT: PDF: test.pdf" in content
        or "<!-- ATTACHMENT: DOCUMENT: test.pdf" in content
    )

    # The attachments directory should not exist anymore
    attachments_dir = tmp_path / "output" / "attachments"
    assert not attachments_dir.exists()


def test_bear_note_caching(tmp_path):
    """Test Bear note processing with caching"""
    source_dir = tmp_path / "bear"
    source_dir.mkdir()
    note_path = source_dir / "cached_note.md"
    note_path.write_text("# Cached Note\nThis will be cached.")

    source_config = SourceConfig(
        type="bear", src_dir=source_dir, dest_dir=tmp_path / "output"
    )
    global_config = GlobalConfig(
        cm_dir=tmp_path / ".cm",
        no_image=True,
        force_generation=False,  # Enable caching
    )
    config = Config(global_config=global_config, sources=[source_config])

    # First run - should generate
    processor = BearProcessor(source_config)
    result1 = processor.process(config)
    assert result1.processed == 1
    assert result1.regenerated == 1
    assert result1.from_cache == 0

    # Second run - should use cache
    result2 = processor.process(config)
    assert result2.processed == 1
    assert result2.regenerated == 0
    assert result2.from_cache == 1

    # Force regeneration
    config.global_config.force_generation = True
    result3 = processor.process(config)
    assert result3.processed == 1
    assert result3.regenerated == 1
    assert result3.from_cache == 0


def test_xbookmarks_basic(tmp_path):
    """Test processing a basic X Bookmarks entry"""
    source_dir = tmp_path / "xbookmarks"
    source_dir.mkdir()
    bookmark_dir = source_dir / "sample_bookmark"
    bookmark_dir.mkdir()

    index_path = bookmark_dir / "index.md"
    index_path.write_text("# Sample Bookmark\nA test bookmark.")

    source_config = SourceConfig(
        type="xbookmarks", src_dir=source_dir, dest_dir=tmp_path / "output"
    )
    global_config = GlobalConfig(
        cm_dir=tmp_path / ".cm",
        no_image=True,  # Disable GPT for basic test
    )
    config = Config(global_config=global_config, sources=[source_config])

    processor = XBookmarksProcessor(source_config)
    result = processor.process(config)

    # Verify detailed stats
    assert result.processed == 1
    assert result.regenerated == 1
    assert result.from_cache == 0
    assert result.skipped == 0
    assert result.images_processed == 0
    assert result.documents_processed == 0
    assert result.errors == []
    assert (tmp_path / "output" / "sample_bookmark.md").exists()
    assert (
        "# Sample Bookmark" in (tmp_path / "output" / "sample_bookmark.md").read_text()
    )


def test_xbookmarks_with_media(tmp_path):
    """Test processing X Bookmarks with media files"""
    source_dir = tmp_path / "xbookmarks"
    source_dir.mkdir()
    bookmark_dir = source_dir / "media_bookmark"
    bookmark_dir.mkdir()

    # Create media files
    media_dir = bookmark_dir / "media"
    media_dir.mkdir()
    test_image = media_dir / "screenshot.png"
    test_image.write_bytes(b"fake png data")

    index_path = bookmark_dir / "index.md"
    index_path.write_text("# Media Bookmark\n![screenshot](media/screenshot.png)")

    source_config = SourceConfig(
        type="xbookmarks", src_dir=source_dir, dest_dir=tmp_path / "output"
    )
    global_config = GlobalConfig(
        cm_dir=tmp_path / ".cm",
        no_image=True,  # Disable GPT for basic test
    )
    config = Config(global_config=global_config, sources=[source_config])

    processor = XBookmarksProcessor(source_config)

    # Mock the _process_attachment method to return a comment-based reference
    with patch.object(processor, "_process_attachment") as mock_process:

        def side_effect(
            attachment_path, output_dir, attachment_processor, config, result, **kwargs
        ):
            # Update the result object
            result.add_image_generated(processor._processor_type)
            return "<!-- ATTACHMENT: IMAGE: screenshot.png (0x0, 0KB) -->\n<!-- GPT Description: This is a test image -->\n![This is a test image]()"

        mock_process.side_effect = side_effect

        result = processor.process(config)

    assert result.processed == 1
    assert result.images_processed == 2
    assert result.errors == []
    assert (tmp_path / "output" / "media_bookmark.md").exists()

    # With the new behavior, media files are not copied to a media directory
    # but instead referenced in comments in the markdown file
    content = (tmp_path / "output" / "media_bookmark.md").read_text()

    # Check for image comment reference
    assert "<!-- ATTACHMENT: IMAGE: screenshot.png" in content

    # The media directory should not exist anymore
    media_output_dir = tmp_path / "output" / "media"
    assert not media_output_dir.exists()


def test_source_validation(tmp_path):
    """Test source directory validation"""
    source_dir = tmp_path / "nonexistent"
    source_config = SourceConfig(
        type="bear", src_dir=source_dir, dest_dir=tmp_path / "output"
    )

    with pytest.raises(ValueError, match="Source directory does not exist"):
        BearProcessor(source_config)

    source_config.type = "xbookmarks"
    with pytest.raises(ValueError, match="Source directory does not exist"):
        XBookmarksProcessor(source_config)


def test_summary_stats_multiple_files(tmp_path):
    """Test summary statistics when processing multiple files"""
    # Create test directories
    source_dir = tmp_path / "test_source"
    source_dir.mkdir()

    # Create multiple test files
    for i in range(3):
        note_dir = source_dir / f"note_{i}"
        note_dir.mkdir()

        # Create main note
        note_file = note_dir / "index.md"
        note_file.write_text(f"# Test Note {i}\nThis is test note {i}")

        # Add an image to each note
        image_file = note_dir / "image.jpg"
        image_file.write_bytes(b"fake jpg data")

    source_config = SourceConfig(
        type="xbookmarks", src_dir=source_dir, dest_dir=tmp_path / "output"
    )
    global_config = GlobalConfig(
        cm_dir=tmp_path / ".cm",
        no_image=True,  # Disable GPT for test
    )
    config = Config(global_config=global_config, sources=[source_config])

    # First run - should generate all files
    processor = XBookmarksProcessor(source_config)
    result = processor.process(config)

    # Verify stats
    assert result.processed == 3
    assert result.regenerated == 3
    assert result.from_cache == 0
    assert result.skipped == 0

    # Second run - should use cache
    result = processor.process(config)
    assert result.processed == 3
    assert result.regenerated == 0
    assert result.from_cache == 3
    assert result.skipped == 0

    # Force regeneration
    config.global_config.force_generation = True
    result = processor.process(config)
    assert result.processed == 3
    assert result.regenerated == 3
    assert result.from_cache == 0
    assert result.skipped == 0
