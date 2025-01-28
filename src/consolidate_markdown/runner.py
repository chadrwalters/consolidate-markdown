import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Type

from .config import Config, SourceConfig
from .logging import SummaryLogger
from .processors.base import ProcessingResult, SourceProcessor
from .processors.bear import BearProcessor
from .processors.xbookmarks import XBookmarksProcessor

logger = logging.getLogger(__name__)


class Runner:
    """Main processing runner."""

    PROCESSORS: Dict[str, Type[SourceProcessor]] = {
        "bear": BearProcessor,
        "xbookmarks": XBookmarksProcessor,
    }

    def __init__(self, config: Config):
        self.config = config
        self.summary = SummaryLogger()

    def run(self, parallel: bool = True) -> "SummaryLogger":
        """Run all processors."""
        logger.info("Starting consolidation")

        try:
            # Process each source
            if parallel and len(self.config.sources) > 1:
                with ThreadPoolExecutor() as executor:
                    executor.map(self._process_source, self.config.sources)
            else:
                for source in self.config.sources:
                    self._process_source(source)

        except Exception as e:
            error_msg = f"Failed to run consolidation: {str(e)}"
            logger.error(error_msg)
            self.summary.add_error("global", error_msg)

        return self.summary

    def _process_source(self, source: SourceConfig) -> None:
        """Process a single source."""
        try:
            logger.info(f"Processing {source.type} source: {source.src_dir}")

            processor = self.PROCESSORS[source.type](source)
            # Validate source configuration
            processor.validate()  # This will raise ValueError if invalid
            result = processor.process(self.config)

            # Update summary using _merge_result_into_summary helper
            self._merge_result_into_summary(source.type, result)

            logger.info(
                f"Completed {source.type} source: {result.processed} processed, "
                f"{result.skipped} skipped, {result.images_processed} images, "
                f"{result.images_skipped} images skipped"
            )

        except Exception as e:
            error_msg = f"Failed to process {source.type} source: {str(e)}"
            logger.error(error_msg)
            self.summary.add_error(source.type, error_msg)

    def _merge_result_into_summary(
        self, source_type: str, result: ProcessingResult
    ) -> None:
        """Merge processing result into summary."""
        # Initialize source stats if needed
        if source_type not in self.summary.source_stats:
            self.summary._init_source_stats(source_type)

        # Track notes - only add from cache or generated, not both
        for _ in range(result.from_cache):
            self.summary.add_from_cache(source_type)
        for _ in range(result.regenerated):  # Use regenerated count directly
            self.summary.add_generated(source_type)
        for _ in range(result.skipped):
            self.summary.add_skipped(source_type)

        # Track documents
        for _ in range(result.documents_from_cache):
            self.summary.add_document_from_cache(source_type)
        for _ in range(result.documents_generated):
            self.summary.add_document_generated(source_type)

        # Track images
        for _ in range(result.images_from_cache):
            self.summary.add_image_from_cache(source_type)
        for _ in range(result.images_generated):
            self.summary.add_image_generated(source_type)

        # Track GPT analyses
        for _ in range(result.gpt_cache_hits):
            self.summary.add_gpt_from_cache(source_type)
        for _ in range(result.gpt_new_analyses):
            self.summary.add_gpt_generated(source_type)

        # Track errors
        for error in result.errors:
            self.summary.add_error(source_type, error)
