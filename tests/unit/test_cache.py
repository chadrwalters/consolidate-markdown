"""Unit tests for cache management system."""

import atexit
import errno
import json
import os
import shutil
import stat
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Set

import pytest

from consolidate_markdown.cache import CacheManager, quick_hash

_temp_dirs: Set[str] = set()


def _handle_remove_readonly(func, path, exc):
    """Handle read-only files and directories during cleanup."""
    excvalue = exc[1]
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        func(path)
    else:
        raise


def _cleanup_temp_dirs():
    """Clean up temporary directories at exit."""
    for temp_dir in _temp_dirs:
        try:
            shutil.rmtree(temp_dir, onerror=_handle_remove_readonly)
        except Exception as e:
            print(f"Warning: Failed to remove temporary directory {temp_dir}: {e}")


atexit.register(_cleanup_temp_dirs)


def test_quick_hash():
    """Test the quick hash function."""
    content = "test content"
    hash1 = quick_hash(content)
    hash2 = quick_hash(content)
    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 32  # MD5 hash length


def on_rm_error(func, path, exc_info):
    # Make the file/directory writable before attempting removal
    os.chmod(path, stat.S_IWRITE)
    func(path)


def recursive_chmod(path):
    """Recursively change permissions to allow deletion."""
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            os.chmod(os.path.join(root, name), stat.S_IWRITE | stat.S_IREAD)
        for name in dirs:
            os.chmod(
                os.path.join(root, name), stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC
            )
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)


def recursive_remove(path):
    """Recursively remove a directory and its contents."""
    try:
        recursive_chmod(path)
        if os.path.isfile(path):
            os.unlink(path)
        else:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                recursive_remove(item_path)
            os.rmdir(path)
    except Exception as e:
        print(f"Warning: Failed to remove {path}: {e}")


def force_remove(path):
    """Force remove a file or directory by changing permissions."""

    def handle_error(func, path, exc_info):
        # Make the file/directory writable and try again
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        func(path)

    if os.path.isfile(path):
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        os.unlink(path)
    elif os.path.isdir(path):
        # First make all files and directories writable
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
            for name in dirs:
                dir_path = os.path.join(root, name)
                os.chmod(dir_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)

        # Then remove the directory tree
        shutil.rmtree(path, onerror=handle_error)


@pytest.fixture
def cache_dir():
    """Provide a temporary directory for cache testing."""
    temp_dir = Path(tempfile.mkdtemp())
    _temp_dirs.add(str(temp_dir))
    yield temp_dir
    try:
        shutil.rmtree(temp_dir, onerror=_handle_remove_readonly)
    except Exception as e:
        print(f"Warning: Failed to cleanup {temp_dir}: {e}")


class TestCacheManager:
    """Test suite for CacheManager class."""

    @pytest.fixture(autouse=True)
    def cleanup(self, request, cache_dir):
        """Cleanup fixture to ensure proper removal of test files."""
        yield
        try:
            # Close any potential open file handles
            if hasattr(self, "cache_manager"):
                del self.cache_manager
            # Force close any remaining file handles
            import gc

            gc.collect()
            # Remove the directory with proper permissions
            if os.path.exists(cache_dir):
                # First make all files writable
                for root, dirs, files in os.walk(cache_dir):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), 0o755)
                    for f in files:
                        os.chmod(os.path.join(root, f), 0o644)
                shutil.rmtree(cache_dir, ignore_errors=True)
        except Exception as e:
            print(f"Cleanup warning: {e}")

    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Create a temporary cache directory."""
        cache_path = tmp_path / ".cm"
        # Ensure directory has proper permissions from the start
        cache_path.mkdir(parents=True, exist_ok=True)
        os.chmod(str(cache_path), 0o755)
        return cache_path

    @pytest.fixture
    def cache_manager(self, cache_dir):
        """Create a CacheManager instance."""
        return CacheManager(cache_dir)

    def test_init_creates_directories(self, cache_dir):
        """Test that initialization creates required directories and files."""
        CacheManager(cache_dir)
        assert (cache_dir / "cache").exists()
        assert (cache_dir / "cache" / "notes.json").exists()
        assert (cache_dir / "cache" / "gpt.json").exists()

    def test_init_with_existing_cache(self, cache_dir):
        """Test initialization with existing cache files."""
        # Create pre-existing cache files
        notes_file = cache_dir / "cache" / "notes.json"
        notes_file.parent.mkdir(parents=True, exist_ok=True)
        notes_file.write_text('{"test": "data"}')

        # Initialize manager but don't use it directly
        _ = CacheManager(cache_dir)
        cache_data = json.loads(notes_file.read_text())
        assert cache_data == {"test": "data"}

    def test_note_cache_operations(self, cache_manager):
        """Test basic note cache operations."""
        note_path = "test/note.md"
        content_hash = "abc123"
        timestamp = time.time()

        # Initially should be None
        assert cache_manager.get_note_cache(note_path) is None

        # Update and verify
        cache_manager.update_note_cache(note_path, content_hash, timestamp)
        cached = cache_manager.get_note_cache(note_path)
        assert cached is not None
        assert cached["hash"] == content_hash
        assert cached["timestamp"] == timestamp

    def test_gpt_cache_operations(self, cache_manager):
        """Test basic GPT cache operations."""
        image_hash = "def456"
        analysis = "A beautiful sunset"

        # Initially should be None
        assert cache_manager.get_gpt_cache(image_hash) is None

        # Update and verify
        cache_manager.update_gpt_cache(image_hash, analysis)
        assert cache_manager.get_gpt_cache(image_hash) == analysis

    def test_clear_cache(self, cache_manager):
        """Test cache clearing."""
        # Add some data
        cache_manager.update_note_cache("test.md", "hash1", time.time())
        cache_manager.update_gpt_cache("image1", "analysis1")

        # Clear cache
        cache_manager.clear_cache()

        # Verify empty
        assert cache_manager.get_note_cache("test.md") is None
        assert cache_manager.get_gpt_cache("image1") is None

    def test_path_normalization(self, cache_manager):
        """Test path normalization in cache operations."""
        paths = [
            "test\\note.md",  # Windows style
            "test/note.md",  # Unix style
            "test\nnote.md",  # With newline
        ]
        content_hash = "hash123"
        timestamp = time.time()

        # Update with Windows path
        cache_manager.update_note_cache(paths[0], content_hash, timestamp)

        # Should be able to retrieve with any path format
        for path in paths:
            cached = cache_manager.get_note_cache(path)
            assert cached is not None
            assert cached["hash"] == content_hash

    def test_concurrent_access(self, cache_manager):
        """Test concurrent cache access."""

        def cache_operation(i):
            note_path = f"test/note_{i}.md"
            content_hash = f"hash_{i}"
            timestamp = time.time()
            cache_manager.update_note_cache(note_path, content_hash, timestamp)
            return cache_manager.get_note_cache(note_path)

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(cache_operation, range(10)))

        assert len(results) == 10
        assert all(r is not None for r in results)
        assert all(r["hash"] == f"hash_{i}" for i, r in enumerate(results))

    def test_large_content_handling(self, cache_manager):
        """Test handling of large content in cache."""
        large_content = "x" * (1024 * 1024)  # 1MB of content
        note_path = "large_note.md"
        content_hash = quick_hash(large_content)
        timestamp = time.time()

        cache_manager.update_note_cache(
            note_path, content_hash, timestamp, processed_content=large_content
        )
        cached = cache_manager.get_note_cache(note_path)
        assert cached is not None
        assert cached["processed_content"] == large_content

    def test_invalid_cache_recovery(self, cache_manager, cache_dir):
        """Test recovery from invalid cache files."""
        # Write invalid JSON
        (cache_dir / "cache" / "notes.json").write_text("invalid json{")

        # Should handle gracefully and return None
        assert cache_manager.get_note_cache("test.md") is None

        # Should be able to write new cache entries
        cache_manager.update_note_cache("test.md", "hash1", time.time())
        assert cache_manager.get_note_cache("test.md") is not None

    def test_gpt_analysis_count(self, cache_manager):
        """Test tracking of GPT analysis count in note cache."""
        note_path = "test/note.md"
        content_hash = "hash123"
        timestamp = time.time()

        # Update with GPT analysis count
        cache_manager.update_note_cache(
            note_path, content_hash, timestamp, gpt_analyses=3
        )
        cached = cache_manager.get_note_cache(note_path)
        assert cached["gpt_analyses"] == 3

    def test_processed_content_storage(self, cache_manager):
        """Test storage and retrieval of processed content."""
        note_path = "test/note.md"
        content_hash = "hash123"
        timestamp = time.time()
        processed_content = "# Processed Markdown"

        cache_manager.update_note_cache(
            note_path, content_hash, timestamp, processed_content=processed_content
        )
        cached = cache_manager.get_note_cache(note_path)
        assert cached["processed_content"] == processed_content
