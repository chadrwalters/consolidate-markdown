"""Unit tests for summary generation functionality."""

from unittest.mock import Mock, patch

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from consolidate_markdown.output import print_summary
from consolidate_markdown.processors.result import ProcessingResult, ProcessorStats


class TestSummaryGeneration:
    """Test suite for summary generation functionality."""

    @pytest.fixture
    def mock_console(self) -> Mock:
        """Create a mock console for testing."""
        console = Mock(spec=Console)
        console.size = (80, 24)
        console.options = Mock()
        console.is_terminal = True
        # Create a print method that preserves Rich objects
        print_mock = Mock()
        print_mock.side_effect = lambda *args, **kwargs: None
        console.print = print_mock
        return console

    @pytest.fixture
    def result(self) -> ProcessingResult:
        """Create a test processing result."""
        result = ProcessingResult()

        # Add stats for different processors
        bear_stats = ProcessorStats(processor_type="bear")
        bear_stats.processed = 15
        bear_stats.regenerated = 8
        bear_stats.from_cache = 7
        bear_stats.images_processed = 5
        bear_stats.images_generated = 3
        bear_stats.images_from_cache = 2
        result.processor_stats["bear"] = bear_stats

        return result

    def test_summary_table_creation(
        self: "TestSummaryGeneration", result: ProcessingResult, mock_console: Mock
    ) -> None:
        """Test creation of summary table."""
        with patch("consolidate_markdown.output.console", mock_console):
            print_summary(result)
            # Verify console output was generated
            assert mock_console.print.called
            # Get the first call args
            first_call = mock_console.print.call_args_list[1]  # Skip the newline
            panel = first_call[0][0]
            # Verify it's a Panel containing a Table
            assert isinstance(panel, Panel)
            assert isinstance(panel.renderable, Table)

    def test_processor_columns(
        self: "TestSummaryGeneration", result: ProcessingResult, mock_console: Mock
    ) -> None:
        """Test processor columns in summary table."""
        with patch("consolidate_markdown.output.console", mock_console):
            print_summary(result)
            # Get the table from the panel
            first_call = mock_console.print.call_args_list[1]  # Skip the newline
            panel = first_call[0][0]
            table = panel.renderable
            # Verify all processor columns are present
            expected_columns = [
                "Metric",
                "Bear Notes",
                "X Bookmarks",
                "Claude",
            ]
            assert len(table.columns) == len(expected_columns)
            for i, col in enumerate(table.columns):
                assert col.header == expected_columns[i]

    def test_metric_rows(
        self: "TestSummaryGeneration", result: ProcessingResult, mock_console: Mock
    ) -> None:
        """Test metric rows in summary table."""
        with patch("consolidate_markdown.output.console", mock_console):
            print_summary(result)
            # Get the table from the panel
            first_call = mock_console.print.call_args_list[1]  # Skip the newline
            panel = first_call[0][0]
            table = panel.renderable
            # Get the first column cells
            metric_cells = table.columns[0]._cells
            # Verify key metrics are present
            assert "Total Processed" in metric_cells
            assert "Generated" in metric_cells
            assert "From Cache" in metric_cells
            assert "Images Processed" in metric_cells
            assert "GPT From Cache" in metric_cells

    def test_error_display(
        self: "TestSummaryGeneration", result: ProcessingResult, mock_console: Mock
    ) -> None:
        """Test error display in summary."""
        result.errors.append("Test error")
        with patch("consolidate_markdown.output.console", mock_console):
            print_summary(result)
            # Get the error panel
            error_calls = [
                call
                for call in mock_console.print.call_args_list
                if isinstance(call[0][0], Panel)
                and "Errors Detected" in str(call[0][0].title)
            ]
            assert len(error_calls) == 1
            error_panel = error_calls[0][0][0]
            # Verify error is displayed
            assert isinstance(error_panel, Panel)
            panel_content = str(error_panel.renderable)
            assert "Test error" in panel_content

    def test_processor_specific_errors(
        self: "TestSummaryGeneration", result: ProcessingResult, mock_console: Mock
    ) -> None:
        """Test processor-specific error display."""
        result.processor_stats["bear"].errors.append("Bear error")

        with patch("consolidate_markdown.output.console", mock_console):
            print_summary(result)
            # Get the error panel
            error_calls = [
                call
                for call in mock_console.print.call_args_list
                if isinstance(call[0][0], Panel)
                and "Errors Detected" in str(call[0][0].title)
            ]
            assert len(error_calls) == 1
            error_panel = error_calls[0][0][0]
            # Verify processor-specific errors are displayed
            panel_content = str(error_panel.renderable)
            assert "Bear error" in panel_content

    def test_zero_stats_display(
        self: "TestSummaryGeneration", mock_console: Mock
    ) -> None:
        """Test display of empty/zero statistics."""
        result = ProcessingResult()
        with patch("consolidate_markdown.output.console", mock_console):
            print_summary(result)
            # Verify table is still created
            assert mock_console.print.called
            first_call = mock_console.print.call_args_list[1]  # Skip the newline
            panel = first_call[0][0]
            assert isinstance(panel, Panel)
            assert isinstance(panel.renderable, Table)

    def test_separator_rows(
        self: "TestSummaryGeneration", result: ProcessingResult, mock_console: Mock
    ) -> None:
        """Test separator rows in summary table."""
        with patch("consolidate_markdown.output.console", mock_console):
            print_summary(result)
            # Get the table from the panel
            first_call = mock_console.print.call_args_list[1]  # Skip the newline
            panel = first_call[0][0]
            table = panel.renderable
            # Verify separator rows are included
            assert any(row.style == "dim" for row in table.rows)

    def test_no_errors_message(
        self: "TestSummaryGeneration", result: ProcessingResult, mock_console: Mock
    ) -> None:
        """Test display when no errors are present."""
        with patch("consolidate_markdown.output.console", mock_console):
            print_summary(result)
            # Get the last message
            success_calls = [
                call
                for call in mock_console.print.call_args_list
                if isinstance(call[0][0], str) and "No errors detected" in call[0][0]
            ]
            assert len(success_calls) == 1
            text = success_calls[0][0][0]
            assert isinstance(text, str)
            assert "No errors detected" in text

    def test_summary_creation(self: "TestSummaryGeneration") -> None:
        # Implementation of the method
        pass

    def test_summary_with_no_files(self: "TestSummaryGeneration") -> None:
        # Implementation of the method
        pass

    def test_summary_with_one_file(self: "TestSummaryGeneration") -> None:
        # Implementation of the method
        pass

    def test_summary_with_multiple_files(self: "TestSummaryGeneration") -> None:
        # Implementation of the method
        pass

    def test_summary_with_errors(self: "TestSummaryGeneration") -> None:
        # Implementation of the method
        pass

    def test_summary_with_skipped(self: "TestSummaryGeneration") -> None:
        # Implementation of the method
        pass

    def test_summary_with_warnings(self: "TestSummaryGeneration") -> None:
        # Implementation of the method
        pass

    def test_summary_with_all_stats(self: "TestSummaryGeneration") -> None:
        # Implementation of the method
        pass

    def test_summary_str(self: "TestSummaryGeneration") -> None:
        # Implementation of the method
        pass

    def test_summary_repr(self: "TestSummaryGeneration") -> None:
        # Implementation of the method
        pass
