"""Test document format conversions."""

import json
from pathlib import Path

import pandas as pd
import pytest

from consolidate_markdown.attachments.document import ConversionError, MarkItDown


@pytest.fixture
def markdown_converter(tmp_path):
    """Create a MarkItDown converter instance."""
    return MarkItDown(tmp_path)


@pytest.fixture
def fixtures_dir():
    """Get the path to test fixtures."""
    return Path(__file__).parent.parent / "fixtures" / "documents"


def test_csv_conversion(markdown_converter, fixtures_dir):
    """Test converting CSV files to markdown tables."""
    csv_file = fixtures_dir / "Time Off Tracker(Holiday Time Off Tracker).csv"
    result = markdown_converter.convert_to_markdown(csv_file)

    # Verify it's a markdown table
    assert "|" in result
    assert "-|-" in result

    # Verify content matches original
    df = pd.read_csv(
        csv_file, encoding="cp1252", engine="python"
    )  # Use same params as converter
    expected_headers = list(df.columns)
    for header in expected_headers:
        assert header in result


def test_text_conversion(markdown_converter, fixtures_dir):
    """Test converting text files to markdown code blocks."""
    txt_file = fixtures_dir / "env.txt"
    result = markdown_converter.convert_to_markdown(txt_file)

    # Verify it's wrapped in code blocks
    assert result.startswith("```\n")
    assert result.endswith("\n```")

    # Verify content matches original
    with open(txt_file, "r", encoding="utf-8") as f:
        original = f.read()
    assert original in result


def test_json_conversion(markdown_converter, fixtures_dir):
    """Test converting JSON files to markdown code blocks."""
    json_file = fixtures_dir / "json.json"
    result = markdown_converter.convert_to_markdown(json_file)

    # Verify it's wrapped in json code blocks
    assert result.startswith("```json\n")
    assert result.endswith("\n```")

    # Verify content is valid JSON and matches original
    with open(json_file, "r", encoding="utf-8") as f:
        original = json.load(f)
    result_json = json.loads(result.replace("```json\n", "").replace("\n```", ""))
    assert result_json == original


def test_pdf_conversion(markdown_converter, fixtures_dir):
    """Test converting PDF files to markdown."""
    pdf_file = fixtures_dir / "pdf_test.pdf"
    result = markdown_converter.convert_to_markdown(pdf_file)

    # Verify it contains PDF content markers
    assert "```pdf" in result
    assert "```" in result

    # Verify some text was extracted (specific content depends on PDF)
    text_content = result.split("```pdf\n")[1].split("\n```")[0]
    assert len(text_content.strip()) > 0


def test_unsupported_format(markdown_converter, tmp_path):
    """Test handling of unsupported file formats."""
    unsupported_file = tmp_path / "test.xyz"
    unsupported_file.write_text("test content")

    with pytest.raises(ConversionError) as exc_info:
        markdown_converter.convert_to_markdown(unsupported_file)
    assert "Format not supported" in str(exc_info.value)


def test_missing_file(markdown_converter, tmp_path):
    """Test handling of missing files."""
    missing_file = tmp_path / "nonexistent.txt"

    with pytest.raises(FileNotFoundError):
        markdown_converter.convert_to_markdown(missing_file)


def test_malformed_json(markdown_converter, tmp_path):
    """Test handling of malformed JSON files."""
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not valid json}")

    with pytest.raises(ConversionError) as exc_info:
        markdown_converter.convert_to_markdown(bad_json)
    assert "Failed to parse JSON" in str(exc_info.value)


def test_malformed_csv(markdown_converter, tmp_path):
    """Test handling of malformed CSV files."""
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("a,b\n1,2\na")  # Mismatched columns

    with pytest.raises(ConversionError) as exc_info:
        markdown_converter.convert_to_markdown(bad_csv)
    assert "CSV file is malformed" in str(exc_info.value)  # Match exact error message


def test_ds_store_handling(markdown_converter, tmp_path):
    """Test handling of .DS_Store files."""
    ds_store = tmp_path / ".DS_Store"
    ds_store.write_text("fake ds_store content")

    result = markdown_converter.convert_to_markdown(ds_store)
    assert result == ""  # Should return empty string for .DS_Store files
