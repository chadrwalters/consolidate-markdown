"""Unit tests for output generation system."""

import threading
import time
from unittest.mock import patch

import pytest

from consolidate_markdown.output import OutputGenerator


class TestOutputGenerator:
    """Test suite for OutputGenerator."""

    @pytest.fixture
    def writer(self, tmp_path):
        """Create an OutputGenerator instance."""
        return OutputGenerator(tmp_path)

    def test_basic_write(self, writer, tmp_path):
        """Test basic file writing."""
        content = "Test content"
        path = "test.md"

        writer.write_output(path, content)

        full_path = tmp_path / path
        assert full_path.exists()
        assert full_path.read_text() == content

    def test_atomic_write(self, writer, tmp_path):
        """Test atomic write operation."""
        content = "Test content"
        path = "test.md"
        full_path = tmp_path / path

        # Write file
        writer.write_output(path, content)

        # Verify no temporary files remain
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0
        assert full_path.exists()
        assert full_path.read_text() == content

    def test_concurrent_writes(self, writer, tmp_path):
        """Test concurrent file writes."""
        num_threads = 5
        writes_per_thread = 10

        def write_file(content):
            for i in range(writes_per_thread):
                filename = f"test_{content}_{i}.md"
                writer.write_output(filename, f"Content {content} {i}")
                time.sleep(0.01)  # Simulate some work

        # Create and start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=write_file, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all files were written
        expected_count = num_threads * writes_per_thread
        actual_files = list(tmp_path.glob("test_*.md"))
        assert len(actual_files) == expected_count

    def test_backup_creation(self, writer, tmp_path):
        """Test backup creation before write."""
        content = "Original content"
        new_content = "New content"
        path = "backup.md"

        # Write original content
        writer.write_output(path, content)

        # Write new content (should create backup)
        writer.write_output(path, new_content, force=True)

        # Verify backup exists
        backup_files = list(tmp_path.parent.glob(f"{tmp_path.name}_backup/*.md"))
        assert len(backup_files) == 1
        assert backup_files[0].read_text() == content

    def test_large_file_handling(self, writer, tmp_path):
        """Test handling of large files."""
        large_content = "x" * (1024 * 1024)  # 1MB content
        path = "large.md"

        writer.write_output(path, large_content)

        full_path = tmp_path / path
        assert full_path.exists()
        assert len(full_path.read_text()) == len(large_content)

    def test_special_characters_in_path(self, writer, tmp_path):
        """Test handling of special characters in file paths."""
        content = "Test content"
        paths = [
            "test with spaces.md",
            "test_with_unicode_中文.md",
            "test.with.dots.md",
            "very/nested/path/test.md",
        ]

        for path in paths:
            writer.write_output(path, content)
            full_path = tmp_path / path
            assert full_path.exists()
            assert full_path.read_text() == content

    def test_error_handling(self, writer, tmp_path):
        """Test error handling during write."""
        content = "Test content"
        path = "test.md"
        full_path = tmp_path / path

        # Create a directory at the target path to cause an error
        full_path.mkdir(parents=True)

        with pytest.raises(Exception):
            writer.write_output(path, content)

    @patch("pathlib.Path.write_text")
    def test_write_failure_cleanup(self, mock_write, writer, tmp_path):
        """Test cleanup after write failure."""
        mock_write.side_effect = Exception("Write failed")

        with pytest.raises(Exception):
            writer.write_output("test.md", "content")

        # Verify no temporary files remain
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0

    def test_directory_creation(self, writer, tmp_path):
        """Test automatic directory creation."""
        content = "Test content"
        path = "nested/deeply/test.md"

        writer.write_output(path, content)

        full_path = tmp_path / path
        assert full_path.exists()
        assert full_path.read_text() == content
