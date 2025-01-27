import logging
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Type

from .config import Config, SourceConfig
from .logging import SummaryLogger
from .processors.base import ProcessingResult, SourceProcessor
from .processors.bear import BearProcessor
from .processors.xbookmarks import XBookmarksProcessor

logger = logging.getLogger(__name__)

class Runner:
    """Main processing runner."""

    PROCESSORS: Dict[str, Type[SourceProcessor]] = {
        'bear': BearProcessor,
        'xbookmarks': XBookmarksProcessor
    }

    def __init__(self, config: Config):
        self.config = config
        self.summary = SummaryLogger()

    def run(self, parallel: bool = True) -> SummaryLogger:
        """Run all configured processors."""
        try:
            # Validate all sources first
            self._validate_sources()

            # Process sources
            if parallel and len(self.config.sources) > 1:
                self._run_parallel()
            else:
                self._run_sequential()

            return self.summary

        except Exception as e:
            logger.error(f"Runner failed: {str(e)}")
            raise

    def _validate_sources(self) -> None:
        """Validate all source configurations."""
        for source in self.config.sources:
            if source.type not in self.PROCESSORS:
                raise ValueError(f"Unknown source type: {source.type}")

            processor = self.PROCESSORS[source.type](source)
            is_valid, errors = processor.validate()

            if not is_valid:
                raise ValueError(f"Invalid {source.type} configuration:\n" + "\n".join(errors))

    def _run_sequential(self) -> None:
        """Process sources sequentially."""
        for source in self.config.sources:
            self._process_source(source)

    def _run_parallel(self) -> None:
        """Process sources in parallel."""
        max_workers = min(len(self.config.sources), mp.cpu_count())

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self._process_source, self.config.sources)

    def _process_source(self, source: SourceConfig) -> None:
        """Process a single source."""
        try:
            logger.info(f"Processing {source.type} source: {source.src_dir}")

            processor = self.PROCESSORS[source.type](source)
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

    def _merge_result_into_summary(self, source_type: str, result: ProcessingResult):
        """Merge processing result into summary."""
        # Track notes
        if result.from_cache > 0:
            self.summary.add_from_cache(source_type)
        if result.regenerated > 0:
            self.summary.add_generated(source_type)
        if result.skipped > 0:
            self.summary.add_skipped(source_type)

        # Track documents
        for _ in range(result.documents_from_cache):
            self.summary.add_document_from_cache(source_type)
        for _ in range(result.documents_generated):
            self.summary.add_document_generated(source_type)
        for _ in range(result.documents_skipped):
            self.summary.add_document_skipped(source_type)

        # Track images
        for _ in range(result.images_from_cache):
            self.summary.add_image_from_cache(source_type)
        for _ in range(result.images_generated):
            self.summary.add_image_generated(source_type)
        for _ in range(result.images_skipped):
            self.summary.add_image_skipped(source_type)

        # Track GPT analyses
        for _ in range(result.gpt_cache_hits):
            self.summary.add_gpt_from_cache(source_type)
        for _ in range(result.gpt_new_analyses):
            self.summary.add_gpt_generated(source_type)
        for _ in range(result.gpt_skipped):
            self.summary.add_gpt_skipped(source_type)

        # Track errors
        for error in result.errors:
            self.summary.add_error(source_type, error)
