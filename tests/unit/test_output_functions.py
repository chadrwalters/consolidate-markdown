"""Unit tests for output functions."""

import io
from unittest.mock import patch

import pytest

from consolidate_markdown.output import (
    OutputError,
    OutputGenerator,
    format_count,
    print_deletion_message,
    print_processing_message,
    print_summary,
)
from consolidate_markdown.processors.result import ProcessingResult, ProcessorStats


class TestOutputError:
    """Test suite for OutputError."""

    def test_output_error_creation(self):
        """Test that OutputError can be created with a message."""
        error = OutputError("Test error message")
        assert str(error) == "Test error message"

    def test_output_error_inheritance(self):
        """Test that OutputError inherits from Exception."""
        error = OutputError("Test error")
        assert isinstance(error, Exception)

    def test_output_error_raising(self):
        """Test that OutputError can be raised and caught."""
        with pytest.raises(OutputError) as excinfo:
            raise OutputError("Test raising error")
        assert "Test raising error" in str(excinfo.value)


class TestOutputFormattingMethods:
    """Test suite for document formatting methods."""

    @pytest.fixture
    def output_generator(self, tmp_path):
        """Create an OutputGenerator instance."""
        return OutputGenerator(tmp_path)

    def test_format_document(self, output_generator):
        """Test formatting a document."""
        title = "Test Document"
        content = "This is test content."
        metadata = {"author": "Test Author", "date": "2023-01-01"}

        formatted = output_generator.format_document(title, content, metadata)

        # Check title
        assert f"# {title}" in formatted
        # Check metadata
        assert "## Metadata" in formatted
        assert "- **author**: Test Author" in formatted
        assert "- **date**: 2023-01-01" in formatted
        # Check content
        assert content in formatted

    def test_format_document_without_metadata(self, output_generator):
        """Test formatting a document without metadata."""
        title = "Test Document"
        content = "This is test content."

        formatted = output_generator.format_document(title, content)

        # Check title
        assert f"# {title}" in formatted
        # Check no metadata section
        assert "## Metadata" not in formatted
        # Check content
        assert content in formatted

    def test_format_embedded_document(self, output_generator):
        """Test formatting an embedded document."""
        title = "Embedded Doc"
        content = "Embedded content."
        doc_type = "note"
        metadata = {"size_bytes": 1024}

        formatted = output_generator.format_embedded_document(
            title, content, doc_type, metadata
        )

        # Check header
        assert f"<!-- EMBEDDED {doc_type.upper()}: {title} -->" in formatted
        # Check details tag
        assert "<details>" in formatted
        assert "</details>" in formatted
        # Check summary with metadata
        assert f"<summary>📄 {title} (1KB)</summary>" in formatted
        # Check content
        assert content in formatted

    def test_format_embedded_document_without_metadata(self, output_generator):
        """Test formatting an embedded document without metadata."""
        title = "Embedded Doc"
        content = "Embedded content."
        doc_type = "note"

        formatted = output_generator.format_embedded_document(title, content, doc_type)

        # Check header
        assert f"<!-- EMBEDDED {doc_type.upper()}: {title} -->" in formatted
        # Check details tag
        assert "<details>" in formatted
        assert "</details>" in formatted
        # Check summary without metadata
        assert f"<summary>📄 {title}</summary>" in formatted
        # Check content
        assert content in formatted

    def test_format_embedded_image(self, output_generator):
        """Test formatting an embedded image."""
        title = "Test Image"
        description = "Image description."
        metadata = {"size": (800, 600), "file_size": 2048}

        formatted = output_generator.format_embedded_image(title, description, metadata)

        # Check header
        assert f"<!-- EMBEDDED IMAGE: {title} -->" in formatted
        # Check details tag
        assert "<details>" in formatted
        assert "</details>" in formatted
        # Check summary with metadata
        assert f"<summary>🖼️ {title} (800x600, 2KB)</summary>" in formatted
        # Check description
        assert description in formatted

    def test_format_embedded_image_without_metadata(self, output_generator):
        """Test formatting an embedded image without metadata."""
        title = "Test Image"
        description = "Image description."

        formatted = output_generator.format_embedded_image(title, description)

        # Check header
        assert f"<!-- EMBEDDED IMAGE: {title} -->" in formatted
        # Check details tag
        assert "<details>" in formatted
        assert "</details>" in formatted
        # Check summary without metadata
        assert f"<summary>🖼️ {title}</summary>" in formatted
        # Check description
        assert description in formatted


class TestOutputUtilityFunctions:
    """Test suite for output utility functions."""

    def test_format_count(self):
        """Test formatting counts with thousands separator."""
        assert format_count(0) == "0"
        assert format_count(1) == "1"
        assert format_count(1000) == "1,000"
        assert format_count(1234567) == "1,234,567"

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_print_deletion_message(self, mock_stdout):
        """Test printing deletion message."""
        with patch("rich.console.Console.print") as mock_print:
            print_deletion_message("/path/to/file")
            mock_print.assert_called_once()
            args = mock_print.call_args[0]
            assert "Deleting:" in args[0]
            assert "/path/to/file" in args[0]

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_print_processing_message(self, mock_stdout):
        """Test printing processing message."""
        with patch("rich.console.Console.print") as mock_print:
            # Test normal message
            print_processing_message("Processing file")
            mock_print.assert_called_once()
            args = mock_print.call_args[0]
            assert "INFO:" in args[0]
            assert "Processing file" in args[0]

            mock_print.reset_mock()

            # Test debug message
            print_processing_message("Debug info", debug=True)
            mock_print.assert_called_once()
            args = mock_print.call_args[0]
            assert "DEBUG:" in args[0]
            assert "Debug info" in args[0]

    def test_print_summary_with_errors(self):
        """Test printing summary with errors."""
        # Create a result with errors
        result = ProcessingResult()

        # Add processor stats with errors
        bear_stats = ProcessorStats(processor_type="bear")
        bear_stats.errors.append("Bear error 1")
        bear_stats.errors.append("Bear error 2")
        result.processor_stats["bear"] = bear_stats

        # Add general errors
        result.errors.append("General error 1")

        # Simply call the function to ensure it doesn't raise exceptions
        # This is a basic smoke test for the error handling path
        print_summary(result)
        # If we get here without exceptions, the test passes

    def test_print_summary_without_errors(self):
        """Test printing summary without errors."""
        # Create a result without errors
        result = ProcessingResult()

        # Add processor stats without errors
        bear_stats = ProcessorStats(processor_type="bear")
        bear_stats.processed = 10
        result.processor_stats["bear"] = bear_stats

        with patch("rich.console.Console.print") as mock_print:
            print_summary(result)

            # Verify success message was printed
            success_calls = [
                call
                for call in mock_print.call_args_list
                if "No errors detected" in str(call)
            ]
            assert len(success_calls) > 0
