"""Unit tests for Runner class."""

from pathlib import Path
from unittest.mock import patch

import pytest

from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors.base import ProcessingResult, SourceProcessor
from consolidate_markdown.runner import Runner


class MockProcessor(SourceProcessor):
    """Mock processor for testing."""

    def __init__(self, source_config: SourceConfig):
        """Initialize the mock processor."""
        super().__init__(source_config)
        self.process_called = False
        self.validate_called = False

    def validate(self) -> None:
        """Mock validate method."""
        self.validate_called = True
        # Create source directory if it doesn't exist
        self.source_config.src_dir.mkdir(parents=True, exist_ok=True)

    def _process_impl(self, config: Config) -> ProcessingResult:
        """Mock process implementation."""
        self.process_called = True
        result = ProcessingResult()
        result.processed = 1
        result.regenerated = 1
        return result


@pytest.fixture
def config(tmp_path):
    """Create a test configuration."""
    global_config = GlobalConfig(cm_dir=tmp_path / ".cm")
    source_config = SourceConfig(
        type="mock", src_dir=tmp_path / "src", dest_dir=tmp_path / "dest"
    )
    return Config(global_config=global_config, sources=[source_config])


@pytest.fixture
def runner(config):
    """Create a test runner."""
    Runner.PROCESSORS = {"mock": MockProcessor}
    return Runner(config)


def test_runner_initialization(runner):
    """Test runner initialization."""
    assert isinstance(runner.config, Config)
    assert isinstance(runner.summary, ProcessingResult)


def test_sequential_processing(runner):
    """Test sequential processing of sources."""
    summary = runner.run(parallel=False)
    assert summary.processed == 1
    assert summary.regenerated == 1


def test_processor_registration():
    """Test processor registration and lookup."""
    Runner.PROCESSORS = {"mock": MockProcessor}
    assert "mock" in Runner.PROCESSORS


def test_processor_validation(runner):
    """Test that processor validation is called."""
    # Create a list to store processor instances
    processors = []

    # Override the processor creation
    class TrackingProcessor(MockProcessor):
        def __init__(self, config):
            super().__init__(config)
            processors.append(self)

    Runner.PROCESSORS = {"mock": TrackingProcessor}
    runner.run(parallel=False)

    # Check that we have the expected number of processors
    assert len(processors) > 0

    # Verify each processor had validate called
    for processor in processors:
        assert processor.validate_called


def test_source_processing_error(config):
    """Test handling of source processing errors."""

    class ErrorProcessor(MockProcessor):
        def validate(self):
            raise ValueError("Processing failed")

    Runner.PROCESSORS = {"mock": ErrorProcessor}
    runner = Runner(config)

    summary = runner.run(parallel=False)
    assert len(summary.errors) > 0
    assert "Processing failed" in str(summary.errors[0])


def test_result_merging(runner):
    """Test merging of processing results."""

    class CustomProcessor(MockProcessor):
        def _process_impl(self, config):
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

    Runner.PROCESSORS = {"mock": CustomProcessor}
    summary = runner.run(parallel=False)

    assert summary.processed == 2
    assert summary.regenerated == 1
    assert summary.from_cache == 1
    assert summary.skipped == 1
    assert summary.images_processed == 2
    assert summary.images_skipped == 1
    assert summary.images_from_cache == 1
    assert summary.images_generated == 1
    assert summary.documents_processed == 2
    assert summary.documents_skipped == 1
    assert summary.documents_from_cache == 1
    assert summary.documents_generated == 1
    assert summary.gpt_cache_hits == 1
    assert summary.gpt_new_analyses == 1
    assert len(summary.errors) == 1


def test_cancellation_handling(runner):
    """Test handling of processing cancellation."""

    class CancellingProcessor(MockProcessor):
        def validate(self):
            raise KeyboardInterrupt("Processing cancelled")

    Runner.PROCESSORS = {"mock": CancellingProcessor}
    with pytest.raises(KeyboardInterrupt, match="Processing cancelled"):
        runner.run(parallel=False)


@patch("consolidate_markdown.runner.logger")
def test_logging_integration(mock_logger, runner):
    """Test integration with logging system."""
    runner.run(parallel=False)
    assert mock_logger.info.call_count >= 1
    assert mock_logger.error.call_count == 0


def test_processor_selection(runner: Runner, config: Config, tmp_path: Path):
    """Test processor selection."""
    # Add a second source
    config.sources.append(
        SourceConfig(
            type="other_mock", src_dir=tmp_path / "src2", dest_dir=tmp_path / "dest2"
        )
    )

    # Register both processors
    Runner.PROCESSORS = {"mock": MockProcessor, "other_mock": MockProcessor}

    # Run with specific processor
    runner.selected_processor = "mock"
    summary = runner.run(parallel=False)
    assert summary.processed == 1

    # Run with different processor
    runner.selected_processor = "other_mock"
    summary = runner.run(parallel=False)
    assert summary.processed == 1


def test_item_limit(runner: Runner):
    """Test item limit propagation."""
    runner.processing_limit = 5
    summary = runner.run(parallel=False)
    assert summary.processed == 1


def test_processor_error_handling(runner: Runner):
    """Test handling of processor errors."""

    class FailingProcessor(MockProcessor):
        def validate(self):
            raise ValueError("Test error")

    Runner.PROCESSORS = {"mock": FailingProcessor}
    summary = runner.run(parallel=False)
    assert len(summary.errors) > 0
    assert "Test error" in str(summary.errors[0])
