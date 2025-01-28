"""Unit tests for the processing runner."""

from unittest.mock import MagicMock, call, patch

import pytest

from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors.base import ProcessingResult, SourceProcessor
from consolidate_markdown.runner import Runner


class MockProcessor(SourceProcessor):
    """Mock processor for testing."""

    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.validate_called = False

    def validate(self):
        """Track validation call."""
        super().validate()
        self.validate_called = True

    def process(self, config: Config) -> ProcessingResult:
        """Return mock result."""
        result = ProcessingResult()
        result.processed = 1
        result.skipped = 0
        result.from_cache = 0
        result.regenerated = 1
        result.images_processed = 1
        result.images_skipped = 0
        return result


# Register the mock processor
Runner.PROCESSORS["mock"] = MockProcessor


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration."""
    # Create source directories
    source1_dir = tmp_path / "source1"
    source2_dir = tmp_path / "source2"
    dest1_dir = tmp_path / "dest1"
    dest2_dir = tmp_path / "dest2"
    source1_dir.mkdir(parents=True)
    source2_dir.mkdir(parents=True)
    dest1_dir.parent.mkdir(parents=True, exist_ok=True)
    dest2_dir.parent.mkdir(parents=True, exist_ok=True)

    return Config(
        global_config=GlobalConfig(cm_dir=tmp_path / ".cm", no_image=True),
        sources=[
            SourceConfig(type="mock", src_dir=source1_dir, dest_dir=dest1_dir),
            SourceConfig(type="mock", src_dir=source2_dir, dest_dir=dest2_dir),
        ],
    )


@pytest.fixture
def runner(mock_config):
    """Create a runner instance with mock processor."""
    return Runner(mock_config)


def test_runner_initialization(runner):
    """Test runner initialization."""
    assert isinstance(runner.config, Config)
    assert runner.summary is not None


def test_sequential_processing(runner):
    """Test sequential processing of sources."""
    summary = runner.run(parallel=False)

    assert summary.source_stats["mock"]["processed"] == 2
    assert summary.source_stats["mock"]["generated"] == 2
    assert summary.source_stats["mock"]["from_cache"] == 0
    assert len(summary.errors) == 0


def test_parallel_processing(runner):
    """Test parallel processing of sources."""
    summary = runner.run(parallel=True)

    assert summary.source_stats["mock"]["processed"] == 2
    assert summary.source_stats["mock"]["generated"] == 2
    assert summary.source_stats["mock"]["from_cache"] == 0
    assert len(summary.errors) == 0


def test_processor_registration():
    """Test processor registration and lookup."""
    assert "mock" in Runner.PROCESSORS
    assert Runner.PROCESSORS["mock"] == MockProcessor

    # Test invalid processor type
    with pytest.raises(KeyError):
        Runner.PROCESSORS["invalid"]


def test_processor_validation(runner):
    """Test that processor validation is called."""
    # Create a list to store processor instances
    processors = []

    # Override the processor creation to track instances
    original_processor = Runner.PROCESSORS["mock"]

    class TrackingProcessor(original_processor):
        def __init__(self, config):
            super().__init__(config)
            processors.append(self)

    Runner.PROCESSORS["mock"] = TrackingProcessor

    try:
        runner.run()

        # Check that we have the expected number of processors
        assert len(processors) > 0

        # Verify each processor had validate called
        for processor in processors:
            assert processor.validate_called

    finally:
        # Restore original processor
        Runner.PROCESSORS["mock"] = original_processor


@patch("consolidate_markdown.runner.ThreadPoolExecutor")
def test_parallel_execution_error(mock_executor, runner):
    """Test handling of parallel execution errors."""

    def mock_map(*args, **kwargs):
        raise RuntimeError("Parallel execution failed")

    mock_executor.return_value.__enter__.return_value.map = mock_map

    summary = runner.run(parallel=True)

    # Verify error was added to summary
    assert len(summary.errors) == 1
    assert "Parallel execution failed" in summary.errors[0]


def test_source_processing_error(mock_config):
    """Test handling of source processing errors."""

    class ErrorProcessor(MockProcessor):
        def process(self, config):
            raise ValueError("Processing failed")

    Runner.PROCESSORS["mock"] = ErrorProcessor
    runner = Runner(mock_config)

    summary = runner.run()
    assert len(summary.errors) > 0
    assert "Processing failed" in str(summary.errors[0])


def test_result_merging(runner):
    """Test merging of processing results into summary."""

    class CustomProcessor(MockProcessor):
        def process(self, config):
            result = ProcessingResult()
            result.processed = 2
            result.regenerated = 1
            result.from_cache = 1
            result.skipped = 1
            result.images_processed = 2
            result.images_skipped = 1
            result.images_from_cache = 1
            result.images_generated = 1
            result.documents_processed = 2
            result.documents_skipped = 1
            result.documents_from_cache = 1
            result.documents_generated = 1
            result.gpt_cache_hits = 1
            result.gpt_new_analyses = 1
            result.errors.append("Test error")
            return result

    Runner.PROCESSORS["mock"] = CustomProcessor
    summary = runner.run()

    stats = summary.source_stats["mock"]
    assert stats["processed"] == 4  # 2 sources * 2 processed
    assert stats["generated"] == 2  # 2 sources * 1 regenerated
    assert stats["from_cache"] == 2  # 2 sources * 1 from_cache
    assert stats["skipped"] == 2  # 2 sources * 1 skipped
    assert len(summary.errors) == 2  # 2 sources * 1 error


def test_cancellation_handling(runner):
    """Test handling of processing cancellation."""

    class CancellingProcessor(MockProcessor):
        def process(self, config):
            raise KeyboardInterrupt("Processing cancelled")

    original_processor = Runner.PROCESSORS["mock"]
    Runner.PROCESSORS["mock"] = CancellingProcessor

    try:
        with pytest.raises(KeyboardInterrupt, match="Processing cancelled"):
            runner.run()
    finally:
        Runner.PROCESSORS["mock"] = original_processor


@patch("consolidate_markdown.runner.logger")
def test_logging_integration(mock_logger, runner):
    """Test integration with logging system."""
    # Run with a mock processor that succeeds
    runner.run()

    # Verify logging calls
    assert mock_logger.info.call_count >= 2
    start_call = call("Starting consolidation")
    complete_call = call("Completed consolidation")

    # Get all calls to info
    actual_calls = mock_logger.info.call_args_list

    # Verify start and complete calls are present in the correct order
    assert start_call == actual_calls[0]
    assert complete_call == actual_calls[-1]


@patch("consolidate_markdown.runner.ThreadPoolExecutor")
def test_resource_management(mock_executor, runner):
    """Test proper resource management during processing."""
    # Create a mock executor instance that returns itself as the context manager
    mock_executor_instance = MagicMock()
    mock_executor.return_value = mock_executor_instance
    mock_executor_instance.__enter__.return_value = mock_executor_instance
    mock_executor_instance.__exit__.return_value = None

    # Configure mock_map to return an empty list
    mock_executor_instance.map = MagicMock(return_value=[])

    # Run with parallel=True to ensure ThreadPoolExecutor is used
    runner.run(parallel=True)

    # Verify ThreadPoolExecutor was used correctly
    mock_executor.assert_called_once()
    assert mock_executor_instance.map.call_count == 1

    # Verify map was called with correct arguments
    map_args = mock_executor_instance.map.call_args[0]
    assert len(map_args) == 2
    assert map_args[0] == runner._process_source
    assert list(map_args[1]) == runner.config.sources
