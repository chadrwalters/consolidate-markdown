"""Unit tests for the processing runner."""

from unittest.mock import MagicMock, patch

import pytest

from consolidate_markdown.config import Config, GlobalConfig, SourceConfig
from consolidate_markdown.processors.base import ProcessingResult, SourceProcessor
from consolidate_markdown.runner import Runner


class MockProcessor(SourceProcessor):
    """Mock processor for testing."""

    def __init__(self, source_config):
        super().__init__(source_config)
        self.process_called = False
        self.validate_called = False

    def validate(self):
        self.validate_called = True

    def process(self, config) -> ProcessingResult:
        self.process_called = True
        return ProcessingResult(
            processed=1,
            regenerated=1,
            from_cache=0,
            skipped=0,
            images_processed=1,
            images_skipped=0,
            images_from_cache=0,
            images_generated=1,
            documents_processed=1,
            documents_skipped=0,
            documents_from_cache=0,
            documents_generated=1,
            gpt_cache_hits=0,
            gpt_new_analyses=1,
            errors=[],
        )


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration."""
    return Config(
        global_config=GlobalConfig(cm_dir=tmp_path / ".cm", no_image=True),
        sources=[
            SourceConfig(
                type="mock", src_dir=tmp_path / "source1", dest_dir=tmp_path / "dest1"
            ),
            SourceConfig(
                type="mock", src_dir=tmp_path / "source2", dest_dir=tmp_path / "dest2"
            ),
        ],
    )


@pytest.fixture
def runner(mock_config):
    """Create a runner instance with mock processor."""
    Runner.PROCESSORS["mock"] = MockProcessor
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
    runner.run()

    # Both processors should have validate called
    for source in runner.config.sources:
        processor = Runner.PROCESSORS[source.type](source)
        assert isinstance(processor, MockProcessor)
        assert processor.validate_called


@patch("concurrent.futures.ThreadPoolExecutor")
def test_parallel_execution_error(mock_executor, runner):
    """Test handling of parallel execution errors."""

    def mock_map(*args, **kwargs):
        raise Exception("Parallel execution failed")

    mock_executor.return_value.__enter__.return_value.map = mock_map

    summary = runner.run(parallel=True)
    assert len(summary.errors) > 0
    assert "Parallel execution failed" in str(summary.errors[0])


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
            return ProcessingResult(
                processed=2,
                regenerated=1,
                from_cache=1,
                skipped=1,
                images_processed=2,
                images_skipped=1,
                images_from_cache=1,
                images_generated=1,
                documents_processed=2,
                documents_skipped=1,
                documents_from_cache=1,
                documents_generated=1,
                gpt_cache_hits=1,
                gpt_new_analyses=1,
                errors=["Test error"],
            )

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
            raise KeyboardInterrupt()

    Runner.PROCESSORS["mock"] = CancellingProcessor

    with pytest.raises(KeyboardInterrupt):
        runner.run()


@patch("logging.getLogger")
def test_logging_integration(mock_logger, runner):
    """Test integration with logging system."""
    mock_logger.return_value = MagicMock()

    runner.run()

    # Verify logging calls
    mock_logger.return_value.info.assert_called()
    assert "Starting consolidation" in str(
        mock_logger.return_value.info.call_args_list[0]
    )


def test_resource_management(runner):
    """Test proper resource management during processing."""
    with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance

        runner.run(parallel=True)

        # Verify ThreadPoolExecutor was used correctly
        mock_executor.assert_called_once()
        mock_executor_instance.map.assert_called_once()
