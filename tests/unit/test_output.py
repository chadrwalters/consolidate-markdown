import pytest

from consolidate_markdown.output import OutputGenerator


def test_markdown_image_block(tmp_path):
    """Test formatting of image blocks in markdown"""
    generator = OutputGenerator(tmp_path)
    metadata = {"size": (100, 100), "file_size": 1024}

    block = generator.format_embedded_image("test.jpg", "A test image", metadata)

    assert "<!-- EMBEDDED IMAGE: test.jpg -->" in block
    assert "🖼️ test.jpg (100x100, 1KB)" in block
    assert "A test image" in block


def test_markdown_document_block(tmp_path):
    """Test formatting of document blocks in markdown"""
    generator = OutputGenerator(tmp_path)
    metadata = {"size_bytes": 2048}

    block = generator.format_embedded_document(
        "test.pdf", "Document content", "DOCUMENT", metadata
    )

    assert "<!-- EMBEDDED DOCUMENT: test.pdf -->" in block
    assert "📄 test.pdf (2KB)" in block
    assert "Document content" in block


def test_file_writing(tmp_path):
    """Test atomic file writing"""
    generator = OutputGenerator(tmp_path)
    content = "Test content"

    output_path = generator.write_output(content, "test.md")

    assert output_path.exists()
    assert output_path.read_text() == content


def test_backup_creation(tmp_path):
    """Test backup creation before file operations"""
    backup_dir = tmp_path / "backup"
    generator = OutputGenerator(tmp_path, backup_dir)

    # Create original file
    original_content = "Original content"
    output_file = tmp_path / "test.md"
    output_file.write_text(original_content)

    # Write new content
    new_content = "New content"
    generator.write_output(new_content, "test.md", force=True)

    backup_file = backup_dir / "test.md"
    assert backup_file.exists()
    assert backup_file.read_text() == original_content
    assert output_file.read_text() == new_content


def test_concurrent_access(tmp_path):
    """Test handling of concurrent file access"""
    generator = OutputGenerator(tmp_path)
    content = "Test content"
    target_file = tmp_path / "test.md"

    # Simulate file being held open
    with target_file.open("w") as f:
        f.write("Initial content")

        # Attempt write while file is open
        with pytest.raises(Exception):  # Could be IOError or OutputError
            generator.write_output(content, "test.md")

    # Should succeed after file is closed
    generator.write_output(content, "test.md", force=True)
    assert target_file.read_text() == content
