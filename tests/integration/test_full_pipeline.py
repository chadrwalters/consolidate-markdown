"""Integration tests for the full processing pipeline."""

import shutil
from pathlib import Path

import pytest
import tomli_w

from consolidate_markdown.config import load_config
from consolidate_markdown.runner import Runner


@pytest.fixture
def test_env(tmp_path):
    """Create a test environment with sample files."""
    # Create directory structure
    (tmp_path / ".cm").mkdir()
    (tmp_path / "bear").mkdir()
    (tmp_path / "xbookmarks").mkdir()
    (tmp_path / "output").mkdir()

    # Copy test fixtures
    fixtures = Path(__file__).parent.parent / "fixtures"
    shutil.copytree(fixtures / "bear", tmp_path / "bear", dirs_exist_ok=True)
    shutil.copytree(
        fixtures / "xbookmarks", tmp_path / "xbookmarks", dirs_exist_ok=True
    )

    # Create config file
    config = {
        "global": {
            "cm_dir": str(tmp_path / ".cm"),
            "no_image": True,  # Disable GPT for basic test
        },
        "sources": [
            {
                "type": "bear",
                "srcDir": str(tmp_path / "bear"),
                "destDir": str(tmp_path / "output" / "bear"),
            },
            {
                "type": "xbookmarks",
                "srcDir": str(tmp_path / "xbookmarks"),
                "destDir": str(tmp_path / "output" / "xbookmarks"),
            },
        ],
    }
    config_path = tmp_path / "config.toml"
    config_path.write_text(tomli_w.dumps(config))

    return tmp_path


def test_full_pipeline_sequential(test_env):
    """Test full pipeline processing in sequential mode."""
    config = load_config(test_env / "config.toml")
    runner = Runner(config)

    summary = runner.run(parallel=False)

    # Verify processing completed
    assert summary.source_stats["bear"]["processed"] > 0
    assert summary.source_stats["xbookmarks"]["processed"] > 0
    assert len(summary.errors) == 0

    # Verify output structure
    bear_output = test_env / "output" / "bear"
    xbookmarks_output = test_env / "output" / "xbookmarks"

    assert bear_output.exists()
    assert xbookmarks_output.exists()
    assert len(list(bear_output.glob("**/*.md"))) > 0
    assert len(list(xbookmarks_output.glob("**/*.md"))) > 0


def test_full_pipeline_parallel(test_env):
    """Test full pipeline processing in parallel mode."""
    config = load_config(test_env / "config.toml")
    runner = Runner(config)

    summary = runner.run(parallel=True)

    # Verify processing completed
    assert summary.source_stats["bear"]["processed"] > 0
    assert summary.source_stats["xbookmarks"]["processed"] > 0
    assert len(summary.errors) == 0


def test_pipeline_with_attachments(test_env):
    """Test pipeline with various attachment types."""
    # Add test attachments
    attachments = test_env / "bear" / "note_with_attachments"
    attachments.mkdir(exist_ok=True)

    # Add image
    (attachments / "test.png").write_bytes(b"fake png data")
    (attachments / "test.jpg").write_bytes(b"fake jpg data")

    # Add document
    (attachments / "test.pdf").write_bytes(b"fake pdf data")

    config = load_config(test_env / "config.toml")
    runner = Runner(config)
    summary = runner.run()

    # Verify attachment processing
    assert summary.source_stats["bear"]["images"]["processed"] > 0
    assert summary.source_stats["bear"]["documents"]["processed"] > 0


def test_pipeline_with_cache(test_env):
    """Test pipeline with caching enabled."""
    config = load_config(test_env / "config.toml")
    runner = Runner(config)

    # First run - should process everything
    summary1 = runner.run()
    initial_processed = summary1.stats["processed"]

    # Second run - should use cache
    summary2 = runner.run()
    assert summary2.stats["from_cache"] > 0
    assert summary2.stats["processed"] == initial_processed


def test_pipeline_error_handling(test_env):
    """Test pipeline error handling with invalid files."""
    # Create invalid files
    (test_env / "bear" / "invalid.md").write_text("Invalid markdown content")
    (test_env / "xbookmarks" / "invalid").mkdir()

    config = load_config(test_env / "config.toml")
    runner = Runner(config)
    summary = runner.run()

    # Should continue processing despite errors
    assert summary.stats["processed"] > 0
    assert len(summary.errors) > 0


def test_pipeline_large_dataset(test_env):
    """Test pipeline with a large number of files."""
    # Create many test files
    bear_dir = test_env / "bear"
    for i in range(100):
        (bear_dir / f"note_{i}.md").write_text(f"# Note {i}\nTest content")

    config = load_config(test_env / "config.toml")
    runner = Runner(config)
    summary = runner.run()

    assert summary.source_stats["bear"]["processed"] >= 100


def test_pipeline_concurrent_access(test_env):
    """Test pipeline with concurrent access attempts."""
    import threading

    config = load_config(test_env / "config.toml")
    results = []

    def run_pipeline():
        runner = Runner(config)
        summary = runner.run()
        results.append(summary)

    # Run multiple instances concurrently
    threads = [threading.Thread(target=run_pipeline) for _ in range(3)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # All runs should complete without errors
    assert len(results) == 3
    assert all(len(summary.errors) == 0 for summary in results)
