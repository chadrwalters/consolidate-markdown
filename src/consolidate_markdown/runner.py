"""Runner for processing markdown files."""

import logging
from typing import Dict, Optional, Type

from tqdm import tqdm

from consolidate_markdown.config import Config
from consolidate_markdown.processors import PROCESSOR_TYPES
from consolidate_markdown.processors.base import ProcessingResult, SourceProcessor

logger = logging.getLogger(__name__)


class Runner:
    """Runner for processing markdown files."""

    PROCESSORS: Dict[str, Type[SourceProcessor]] = PROCESSOR_TYPES

    def __init__(self, config: Config):
        """Initialize the runner.

        Args:
            config: The configuration to use.
        """
        self.config = config
        self.summary = ProcessingResult()
        self.selected_processor: Optional[str] = (
            None  # Type of processor to run (optional)
        )
        self.processing_limit: Optional[int] = (
            None  # Max items to process per processor
        )

    def run(self, parallel: bool = False) -> ProcessingResult:
        """Run the consolidation process.

        Args:
            parallel: Whether to process sources in parallel (not implemented).

        Returns:
            The processing result.
        """
        # Reset summary for new run
        self.summary = ProcessingResult()

        # Create progress bar for sources
        sources = list(self.config.sources)  # Convert to list for tqdm
        with tqdm(
            sources,
            desc="Processing Sources",
            unit="src",
            leave=True,  # Keep the progress bar after completion
        ) as source_pbar:
            for source in source_pbar:
                # Skip if a specific processor is selected and this isn't it
                if self.selected_processor and source.type != self.selected_processor:
                    logger.debug(f"Skipping {source.type} processor (not selected)")
                    continue

                # Update progress bar description
                source_pbar.set_description(f"Processing {source.type}")

                try:
                    # Get the processor class
                    processor_class = self.PROCESSORS.get(source.type)
                    if not processor_class:
                        error_msg = f"No processor found for type: {source.type}"
                        logger.error(error_msg)
                        self.summary.errors.append(error_msg)
                        continue

                    # Create and run the processor
                    processor = processor_class(source)
                    if self.processing_limit is not None:
                        processor.item_limit = self.processing_limit

                    # Validate and process
                    processor.validate()
                    result = processor.process(self.config)
                    self.summary.merge(result)

                    # Update progress bar with counts
                    source_pbar.set_postfix(
                        processed=result.processed,
                        cached=result.from_cache,
                        skipped=result.skipped,
                    )

                except Exception as e:
                    error_msg = f"Error processing {source.type}: {str(e)}"
                    logger.error(error_msg)
                    self.summary.errors.append(error_msg)

        return self.summary
