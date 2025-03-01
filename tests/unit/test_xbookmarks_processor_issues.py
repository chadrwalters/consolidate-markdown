from pathlib import Path

import pytest

from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors.xbookmarks import XBookmarksProcessor


@pytest.fixture
def xbookmarks_config(tmp_path: Path) -> Config:
    """Create test configuration for XBookmarks processor."""
    src_dir = tmp_path / "xbookmarks_export"
    src_dir.mkdir(parents=True)

    dest_dir = tmp_path / "output"
    dest_dir.mkdir(parents=True)

    source_config = SourceConfig(
        type="xbookmarks",
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


def test_missing_index_file(xbookmarks_config: Config) -> None:
    """Test handling of missing index file in bookmark directory."""
    # Create a bookmark directory without an index file
    bookmark_dir = xbookmarks_config.sources[0].src_dir / "missing_index"
    bookmark_dir.mkdir(parents=True)

    # Create a file in the directory that is not an index file
    (bookmark_dir / "some_file.txt").write_text("This is not an index file")

    # Process the bookmarks
    processor = XBookmarksProcessor(xbookmarks_config.sources[0])
    result = processor.process(xbookmarks_config)

    # Check that the directory was skipped
    assert result.skipped == 1

    # Check that no output file was created
    output_files = list(xbookmarks_config.sources[0].dest_dir.glob("*.md"))
    assert len(output_files) == 0


def test_special_directories(xbookmarks_config: Config) -> None:
    """Test handling of special directories like 'images' and 'markitdown'."""
    # Create special directories
    special_dirs = ["images", "markitdown", "temp"]
    for dir_name in special_dirs:
        special_dir = xbookmarks_config.sources[0].src_dir / dir_name
        special_dir.mkdir(parents=True)

    # Create a valid bookmark directory with an index file
    valid_dir = xbookmarks_config.sources[0].src_dir / "valid_bookmark"
    valid_dir.mkdir(parents=True)
    (valid_dir / "index.md").write_text("# Valid Bookmark")

    # Process the bookmarks
    processor = XBookmarksProcessor(xbookmarks_config.sources[0])
    result = processor.process(xbookmarks_config)

    # Check that the special directories were not counted as skipped
    assert result.skipped == 0

    # Check that the valid bookmark was processed
    assert result.processed == 1

    # Check that the output file was created
    output_files = list(xbookmarks_config.sources[0].dest_dir.glob("*.md"))
    assert len(output_files) == 1


def test_empty_bookmark_directory(xbookmarks_config: Config) -> None:
    """Test handling of empty bookmark directory."""
    # Create an empty bookmark directory
    empty_dir = xbookmarks_config.sources[0].src_dir / "empty_bookmark"
    empty_dir.mkdir(parents=True)

    # Process the bookmarks
    processor = XBookmarksProcessor(xbookmarks_config.sources[0])
    result = processor.process(xbookmarks_config)

    # Check that the directory was skipped
    assert result.skipped == 1

    # Check that no output file was created
    output_files = list(xbookmarks_config.sources[0].dest_dir.glob("*.md"))
    assert len(output_files) == 0
