import pytest

from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors.bear import BearProcessor
from consolidate_markdown.processors.xbookmarks import XBookmarksProcessor


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
        cm_dir=tmp_path / ".cm", no_image=True  # Disable GPT for basic test
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
    test_image.write_bytes(b"fake png data")

    # Document attachment
    test_doc = attachments_dir / "test.pdf"
    test_doc.write_bytes(b"fake pdf data")

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
        cm_dir=tmp_path / ".cm", no_image=True  # Disable GPT for basic test
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
    assert (tmp_path / "output" / "note_with_attachments.md").exists()
    assert (tmp_path / "output" / "attachments" / "test.png").exists()
    assert (tmp_path / "output" / "attachments" / "test.pdf").exists()


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
        cm_dir=tmp_path / ".cm", no_image=True, force_generation=False  # Enable caching
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
        cm_dir=tmp_path / ".cm", no_image=True  # Disable GPT for basic test
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
    index_path.write_text(f"# Media Bookmark\n![screenshot]({test_image})")

    source_config = SourceConfig(
        type="xbookmarks", src_dir=source_dir, dest_dir=tmp_path / "output"
    )
    global_config = GlobalConfig(
        cm_dir=tmp_path / ".cm", no_image=True  # Disable GPT for basic test
    )
    config = Config(global_config=global_config, sources=[source_config])

    processor = XBookmarksProcessor(source_config)
    result = processor.process(config)

    assert result.processed == 1
    assert result.images_processed == 1
    assert result.errors == []
    assert (tmp_path / "output" / "media_bookmark.md").exists()
    assert (tmp_path / "output" / "media" / "screenshot.png").exists()


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
        cm_dir=tmp_path / ".cm", no_image=True  # Disable GPT for test
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
