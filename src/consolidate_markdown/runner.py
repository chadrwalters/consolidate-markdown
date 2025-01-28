"""Runner for processing markdown files."""

import logging
from typing import Dict, Type

from consolidate_markdown.config import Config, SourceConfig
from consolidate_markdown.logging import SummaryLogger
from consolidate_markdown.processors.base import ProcessingResult, SourceProcessor

logger = logging.getLogger(__name__)


class Runner:
    """Runner for processing markdown files."""

    PROCESSORS: Dict[str, Type[SourceProcessor]] = {}

    def __init__(self, config: Config):
        """Initialize the runner.

        Args:
            config: The configuration to use.
        """
        self.config = config
        self.summary = SummaryLogger()

    def run(self, parallel: bool = False) -> SummaryLogger:
        """Run the processing.

        Args:
            parallel: Ignored. Kept for backwards compatibility.

        Returns:
            The processing summary.

        Raises:
            KeyboardInterrupt: If processing is cancelled.
        """
        logger.info("Starting consolidation process")

        try:
            for source_config in self.config.sources:
                self._process_source(source_config)
        except KeyboardInterrupt as e:
            logger.warning("Processing cancelled")
            raise e
        finally:
            logger.info("Completed consolidation")

        return self.summary

    def _process_source(self, source_config: SourceConfig) -> None:
        """Process a single source.

        Args:
            source_config: The source configuration.
        """
        try:
            processor_class = self.PROCESSORS[source_config.type]
            processor = processor_class(source_config)
            processor.validate()

            result = processor.process(self.config)
            self._merge_result(source_config.type, result)

        except Exception as e:
            logger.error("Error processing source %s: %s", source_config.type, str(e))
            self.summary.add_error(source_config.type, str(e))

    def _merge_result(self, source_type: str, result: ProcessingResult) -> None:
        """Merge a processing result into the summary.

        Args:
            source_type: The type of source that was processed.
            result: The processing result to merge.
        """
        # Initialize source stats if needed
        if source_type not in self.summary.source_stats:
            self.summary._init_source_stats(source_type)

        # Add note stats
        for _ in range(result.from_cache):
            self.summary.add_from_cache(source_type)
        for _ in range(result.regenerated):
            self.summary.add_generated(source_type)
        for _ in range(result.skipped):
            self.summary.add_skipped(source_type)

        # Add document stats
        for _ in range(result.documents_from_cache):
            self.summary.add_document_from_cache(source_type)
        for _ in range(result.documents_generated):
            self.summary.add_document_generated(source_type)
        for _ in range(result.documents_skipped):
            self.summary.add_document_skipped(source_type)

        # Add image stats
        for _ in range(result.images_from_cache):
            self.summary.add_image_from_cache(source_type)
        for _ in range(result.images_generated):
            self.summary.add_image_generated(source_type)
        for _ in range(result.images_skipped):
            self.summary.add_image_skipped(source_type)

        # Add GPT stats
        for _ in range(result.gpt_cache_hits):
            self.summary.add_gpt_from_cache(source_type)
        for _ in range(result.gpt_new_analyses):
            self.summary.add_gpt_generated(source_type)

        # Add errors
        for error in result.errors:
            self.summary.add_error(source_type, str(error))
