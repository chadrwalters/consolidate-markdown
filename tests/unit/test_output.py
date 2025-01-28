"""Unit tests for output generation system."""

import threading
import time
from unittest.mock import patch

import pytest

from consolidate_markdown.output import FileWriter, MarkdownFormatter


class TestMarkdownFormatter:
    """Test suite for MarkdownFormatter."""

    @pytest.fixture
    def formatter(self):
        """Create a MarkdownFormatter instance."""
        return MarkdownFormatter()

    def test_basic_formatting(self, formatter):
        """Test basic markdown formatting."""
        content = "# Title\nNormal text\n**Bold text**"
        formatted = formatter.format(content)
        assert formatted == content  # Should preserve basic markdown

    def test_image_formatting(self, formatter):
        """Test image formatting."""
        content = "![Alt text](path/to/image.jpg)"
        formatted = formatter.format(content)
        assert "![Alt text]" in formatted
        assert "(path/to/image.jpg)" in formatted

    def test_special_characters(self, formatter):
        """Test handling of special characters."""
        content = "Text with *asterisks* and _underscores_\nAnd some <html> tags"
        formatted = formatter.format(content)
        assert "*asterisks*" in formatted
        assert "_underscores_" in formatted
        assert "<html>" in formatted

    def test_code_blocks(self, formatter):
        """Test code block formatting."""
        content = "```python\ndef test():\n    pass\n```"
        formatted = formatter.format(content)
        assert "```python" in formatted
        assert "def test():" in formatted
        assert "```" in formatted

    def test_tables(self, formatter):
        """Test table formatting."""
        content = """
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
"""
        formatted = formatter.format(content)
        assert "| Header 1 |" in formatted
        assert "|----------|" in formatted
        assert "| Cell 1   |" in formatted

    def test_nested_lists(self, formatter):
        """Test nested list formatting."""
        content = """
- Level 1
  - Level 2
    - Level 3
      - Level 4
"""
        formatted = formatter.format(content)
        assert "- Level 1" in formatted
        assert "  - Level 2" in formatted
        assert "    - Level 3" in formatted
        assert "      - Level 4" in formatted

    def test_large_content(self, formatter):
        """Test formatting of large content."""
        content = "Large paragraph\n" * 1000
        formatted = formatter.format(content)
        assert len(formatted.splitlines()) == 1000

    def test_mixed_content(self, formatter):
        """Test formatting of mixed content types."""
        content = """
# Title

Normal paragraph with **bold** and *italic* text.

```python
def code():
    pass
```

1. Numbered list
2. With items
   - And nested
   - Bullet points

| Table | Header |
|-------|--------|
| Cell  | Data   |

![Image](test.jpg)
"""
        formatted = formatter.format(content)
        assert "# Title" in formatted
        assert "**bold**" in formatted
        assert "```python" in formatted
        assert "1. Numbered" in formatted
        assert "| Table |" in formatted
        assert "![Image]" in formatted


class TestFileWriter:
    """Test suite for FileWriter."""

    @pytest.fixture
    def writer(self, tmp_path):
        """Create a FileWriter instance."""
        return FileWriter(tmp_path)

    def test_basic_write(self, writer, tmp_path):
        """Test basic file writing."""
        content = "Test content"
        path = "test.md"
        writer.write(path, content)

        full_path = tmp_path / path
        assert full_path.exists()
        assert full_path.read_text() == content

    def test_atomic_write(self, writer, tmp_path):
        """Test atomic write operation."""
        content = "Test content"
        path = "atomic.md"
        full_path = tmp_path / path

        # Write file
        writer.write(path, content)

        # Verify no temporary files remain
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0

        # Verify content was written
        assert full_path.read_text() == content

    def test_concurrent_writes(self, writer, tmp_path):
        """Test concurrent file writes."""
        path = "concurrent.md"
        full_path = tmp_path / path

        def write_file(content):
            writer.write(path, content)
            time.sleep(0.1)  # Simulate some work

        # Create multiple threads writing to the same file
        threads = []
        for i in range(10):
            thread = threading.Thread(target=write_file, args=(f"Content {i}",))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify file exists and contains valid content
        assert full_path.exists()
        content = full_path.read_text()
        assert "Content" in content
        assert (
            len(content.splitlines()) == 1
        )  # Should be atomic, only last write remains

    def test_backup_creation(self, writer, tmp_path):
        """Test backup creation before write."""
        content = "Original content"
        new_content = "New content"
        path = "backup.md"

        # Write original content
        writer.write(path, content)

        # Write new content (should create backup)
        writer.write(path, new_content)

        # Verify backup exists
        backup_files = list(tmp_path.glob("*.bak"))
        assert len(backup_files) == 1
        assert backup_files[0].read_text() == content

    def test_large_file_handling(self, writer, tmp_path):
        """Test handling of large files."""
        large_content = "x" * (1024 * 1024)  # 1MB content
        path = "large.md"

        writer.write(path, large_content)

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
            writer.write(path, content)
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
            writer.write(path, content)

    @patch("pathlib.Path.write_text")
    def test_write_failure_cleanup(self, mock_write, writer, tmp_path):
        """Test cleanup after write failure."""
        mock_write.side_effect = Exception("Write failed")

        with pytest.raises(Exception):
            writer.write("test.md", "content")

        # Verify no temporary files remain
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0

    def test_directory_creation(self, writer, tmp_path):
        """Test automatic directory creation."""
        content = "Test content"
        path = "nested/deeply/test.md"

        writer.write(path, content)

        full_path = tmp_path / path
        assert full_path.exists()
        assert full_path.read_text() == content
