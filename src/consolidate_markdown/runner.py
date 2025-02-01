"""Runner for processing markdown files."""

import logging
from typing import Dict, Optional, Type

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from consolidate_markdown.config import Config
from consolidate_markdown.log_setup import set_progress
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

        # Create progress display for sources
        sources = list(self.config.sources)  # Convert to list for progress
        logger.info(f"Starting consolidation with {len(sources)} source(s)")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            expand=True,
            transient=False,  # Keep progress bars visible
        ) as progress:
            # Set up progress-aware logging
            set_progress(progress)
            try:
                source_task = progress.add_task(
                    "[cyan]Processing Sources...", total=len(sources)
                )

                for source in sources:
                    # Skip if a specific processor is selected and this isn't it
                    if (
                        self.selected_processor
                        and source.type != self.selected_processor
                    ):
                        logger.debug(f"Skipping {source.type} processor (not selected)")
                        continue

                    # Update progress description
                    progress.update(
                        source_task, description=f"[cyan]Processing {source.type}..."
                    )

                    try:
                        # Get the processor class
                        processor_class = self.PROCESSORS.get(source.type)
                        if not processor_class:
                            error_msg = f"No processor found for type: {source.type}"
                            logger.error(error_msg)
                            self.summary.errors.append(error_msg)
                            progress.advance(source_task)
                            continue

                        # Create and run the processor
                        processor = processor_class(source)
                        if self.processing_limit is not None:
                            processor.item_limit = self.processing_limit

                        # Set up progress tracking for the processor
                        processor.set_progress(progress, source_task)

                        # Validate and process
                        processor.validate()
                        logger.info(f"Processing source: {source.type}")
                        result = processor.process(self.config)
                        self.summary.merge(result)

                        # Update progress
                        progress.update(
                            source_task,
                            advance=1,
                            description=f"[green]Completed {source.type}",
                        )
                        logger.info(f"Completed source: {source.type}")

                    except Exception as e:
                        error_msg = f"Error processing {source.type}: {str(e)}"
                        logger.error(error_msg)
                        self.summary.errors.append(error_msg)
                        progress.update(
                            source_task,
                            advance=1,
                            description=f"[red]Failed {source.type}",
                        )

            finally:
                # Clear progress-aware logging
                set_progress(None)

        logger.info(
            f"Consolidation complete: {self.summary.processed} processed, {self.summary.errors} errors"
        )
        return self.summary
