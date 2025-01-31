"""Runner for processing markdown files."""

import logging
import shutil
from typing import Dict, Optional, Type

from consolidate_markdown.config import Config
from consolidate_markdown.processors import PROCESSOR_TYPES
from consolidate_markdown.processors.base import ProcessingResult, SourceProcessor

logger = logging.getLogger(__name__)


class Runner:
    """Runner for processing markdown files."""

    PROCESSORS: Dict[str, Type[SourceProcessor]] = PROCESSOR_TYPES

    def __init__(self, config: Config, delete_existing: bool = False):
        """Initialize the runner.

        Args:
            config: The configuration to use.
            delete_existing: Whether to delete existing output files and .cm directory.
        """
        self.config = config
        self.summary = ProcessingResult()
        self.delete_existing = delete_existing
        self.selected_processor: Optional[str] = (
            None  # Type of processor to run (optional)
        )
        self.processing_limit: Optional[int] = (
            None  # Max items to process per processor
        )

    def _delete_existing(self) -> None:
        """Delete existing output files and .cm directory."""
        try:
            # Delete .cm directory
            cm_dir = self.config.global_config.cm_dir
            if cm_dir.exists():
                logger.info(f"Deleting .cm directory: {cm_dir}")
                shutil.rmtree(cm_dir)

            # Delete output directories
            for source in self.config.sources:
                dest_dir = source.dest_dir
                if dest_dir.exists():
                    logger.info(f"Deleting output directory: {dest_dir}")
                    shutil.rmtree(dest_dir)
        except Exception as e:
            logger.error(f"Error deleting existing files: {str(e)}")
            raise

    def run(self, parallel: bool = False) -> ProcessingResult:
        """Run the consolidation process.

        Args:
            parallel: Whether to process sources in parallel (not implemented).

        Returns:
            The processing result.
        """
        # Reset summary for new run
        self.summary = ProcessingResult()

        if self.delete_existing:
            self._delete_existing()

        for source in self.config.sources:
            # Skip if a specific processor is selected and this isn't it
            if self.selected_processor and source.type != self.selected_processor:
                logger.debug(f"Skipping {source.type} processor (not selected)")
                continue

            try:
                processor_class = self.PROCESSORS.get(source.type)
                if not processor_class:
                    error_msg = f"Unknown processor type: {source.type}"
                    logger.error(error_msg)
                    self.summary.errors.append(error_msg)
                    continue

                processor = processor_class(source)
                if self.processing_limit is not None:
                    processor.item_limit = self.processing_limit

                # Validate and process
                try:
                    processor.validate()
                    result = processor.process(self.config)
                    self.summary.merge(result)
                except Exception as e:
                    error_msg = f"Error processing source {source.type}: {str(e)}"
                    logger.error(error_msg)
                    self.summary.errors.append(error_msg)

            except Exception as e:
                error_msg = f"Error creating processor for {source.type}: {str(e)}"
                logger.error(error_msg)
                self.summary.errors.append(error_msg)

        logger.info("Completed consolidation")
        return self.summary
