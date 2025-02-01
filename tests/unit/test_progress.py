"""Unit tests for progress display functionality."""

import time
from unittest.mock import Mock

import pytest
from rich.console import Console
from rich.live import Live
from rich.progress import Progress

from consolidate_markdown.config import SourceConfig
from consolidate_markdown.processors.base import SourceProcessor


class TestProgressDisplay:
    """Test suite for progress display functionality."""

    @pytest.fixture
    def mock_console(self):
        """Create a mock console for testing."""
        console = Mock(spec=Console)
        console.get_time = Mock(return_value=time.monotonic())
        console.size = (80, 24)
        console.options = Mock()
        console.is_terminal = True
        return console

    @pytest.fixture
    def mock_live(self, mock_console):
        """Create a mock Live object."""
        live = Mock(spec=Live)
        live.is_started = True
        live.refresh = Mock()
        live.console = mock_console
        return live

    @pytest.fixture
    def progress(self, mock_console, mock_live):
        """Create a Progress instance for testing."""
        progress = Progress(
            console=mock_console,
            expand=True,
            transient=False,
        )
        progress.live = mock_live
        return progress

    @pytest.fixture
    def processor(self, tmp_path):
        """Create a test processor instance."""
        config = SourceConfig(
            type="test",
            src_dir=tmp_path / "src",
            dest_dir=tmp_path / "dest",
        )
        return Mock(spec=SourceProcessor, source_config=config)

    def test_progress_creation(self, progress):
        """Test creating progress tasks."""
        task_id = progress.add_task("Test Task", total=100)
        # TaskID is just an int under the hood
        assert isinstance(task_id, int)
        assert progress.tasks[0].description == "Test Task"
        assert progress.tasks[0].total == 100

    def test_progress_update(self, progress):
        """Test updating progress."""
        task_id = progress.add_task("Test Task", total=100)
        progress.update(task_id, advance=50)
        assert progress.tasks[0].completed == 50
        assert progress.tasks[0].percentage == 50.0

    def test_processor_progress_tracking(self, processor, progress):
        """Test processor progress tracking."""
        task_id = progress.add_task("Processing Test", total=10)
        processor.set_progress(progress, task_id)

        # Simulate processing updates
        progress.update(task_id, advance=5)
        assert progress.tasks[0].completed == 5
        assert progress.tasks[0].percentage == 50.0

    def test_nested_progress(self, progress):
        """Test nested progress bars."""
        parent_id = progress.add_task("Parent Task", total=100)
        child_id = progress.add_task("Child Task", total=50)

        # Update child progress
        progress.update(child_id, advance=25)
        assert progress.tasks[1].completed == 25
        assert progress.tasks[1].percentage == 50.0

        # Update parent progress
        progress.update(parent_id, advance=50)
        assert progress.tasks[0].completed == 50
        assert progress.tasks[0].percentage == 50.0

    def test_progress_completion(self, progress):
        """Test progress completion."""
        task_id = progress.add_task("Test Task", total=100)
        progress.update(task_id, completed=100)
        assert progress.tasks[0].finished
        assert progress.tasks[0].percentage == 100.0

    def test_progress_error_state(self, progress):
        """Test progress error state handling."""
        task_id = progress.add_task("Error Task", total=100)
        progress.update(task_id, description="[red]Error Task (Failed)")
        assert "red" in progress.tasks[0].description

    def test_progress_display_refresh(self, progress, mock_live):
        """Test progress display refresh."""
        progress.add_task("Test Task", total=100)  # We don't need to store the task_id
        mock_live.refresh.reset_mock()  # Reset mock to ignore any previous calls
        progress.refresh()
        mock_live.refresh.assert_called_once()

    def test_multiple_processors_progress(self, progress):
        """Test progress tracking with multiple processors."""
        task_ids = [progress.add_task(f"Processor {i}", total=100) for i in range(3)]

        # Update progress for each processor
        for i, task_id in enumerate(task_ids):
            progress.update(task_id, advance=i * 25)
            assert progress.tasks[i].completed == i * 25
            assert progress.tasks[i].percentage == i * 25.0

    def test_progress_with_unknown_total(self, progress):
        """Test progress handling with unknown total."""
        task_id = progress.add_task("Unknown Total", total=None)
        progress.update(task_id, advance=1)
        assert not progress.tasks[0].finished
        assert progress.tasks[0].total is None
