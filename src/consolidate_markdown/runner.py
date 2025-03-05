"""Runner for processing markdown files."""

import logging
from typing import Dict, Optional, Type

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from consolidate_markdown.cache import CacheManager
from consolidate_markdown.config import Config
from consolidate_markdown.log_setup import set_progress
from consolidate_markdown.output import format_count
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
        self.selected_processor: Optional[
            str
        ] = None  # Type of processor to run (optional)
        self.processing_limit: Optional[
            int
        ] = None  # Max items to process per processor

        # Create a single shared cache manager for all processors
        self.cache_manager = CacheManager(config.global_config.cm_dir)

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

        # Print initial message
        console = Console()
        console.print("\nConsolidating markdown files...")

        # Progress display depends on verbosity level
        if self.config.global_config.verbosity <= 1:
            # Simple progress for low verbosity levels - no progress bars
            progress = Progress(
                auto_refresh=False,  # Don't auto refresh to avoid progress bar display
                console=None,  # Use null console to suppress progress output
                transient=True,  # Make progress bars transient
            )
        else:
            # Detailed progress for high verbosity levels
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                expand=True,
                transient=True,  # Make progress bars transient
                auto_refresh=True,  # Auto refresh the progress display
            )

        with progress:
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

                    # Get display name for this processor
                    display_name = source.type.title()
                    if source.type == "bear":
                        display_name = "Bear notes"
                    elif source.type == "xbookmarks":
                        display_name = "X Bookmarks"

                    # Print processor start with spinner
                    console.print(f"\n{display_name}: ⠦ Processing...")

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

                        # Create processor with shared cache manager
                        processor = processor_class(
                            source, cache_manager=self.cache_manager
                        )
                        if self.processing_limit is not None:
                            processor.item_limit = self.processing_limit

                        # Set up progress tracking for the processor
                        processor.set_progress(progress, source_task)

                        # Validate and process
                        try:
                            processor.validate()
                            # Keep separators in logs but not in user-facing output
                            logger.info("=" * 80)
                            logger.info(f"Processing source: {source.type}")
                            logger.info("-" * 80)

                            # Process the source
                            result = processor.process(self.config)
                            self.summary.merge(result)

                            # Print completion message with checkmark
                            stats = result.processor_stats.get(source.type)
                            if stats:
                                console.print(
                                    f"✓ {display_name} completed "
                                    f"({format_count(stats.processed)} total: "
                                    f"{format_count(stats.regenerated)} generated, "
                                    f"{format_count(stats.from_cache)} from cache)"
                                )
                            else:
                                console.print(f"✓ {display_name} completed")

                            # Update progress
                            progress.update(
                                source_task,
                                advance=1,
                                description=f"[green]Completed {source.type}",
                            )

                            # Add a clear separator after processing a source
                            logger.info("-" * 80)
                            logger.info(f"Completed source: {source.type}")
                            logger.info("=" * 80)

                        except FileNotFoundError as e:
                            # Skip if this is just a missing source file for Claude
                            if (
                                isinstance(e, FileNotFoundError)
                                and source.type == "claude"
                            ):
                                logger.info(f"Skipping Claude source: {str(e)}")
                                console.print(
                                    f"⚠ {display_name} processor skipped (no source files)"
                                )
                                progress.update(
                                    source_task,
                                    advance=1,
                                    description=f"[yellow]Skipped {source.type}",
                                )
                                continue
                            else:
                                raise

                    except Exception as e:
                        error_msg = f"Error processing {source.type}: {str(e)}"
                        logger.error(error_msg)
                        self.summary.errors.append(error_msg)
                        progress.update(
                            source_task,
                            advance=1,
                            description=f"[red]Failed {source.type}",
                        )

                # Mark the source task as completed to ensure it's removed from display
                progress.update(source_task, completed=len(sources))

                # Force a refresh to clear any remaining progress bars
                progress.refresh()

                # Remove all tasks to ensure they don't show up in the final output
                for task_id in progress.task_ids:
                    try:
                        progress.remove_task(task_id)
                    except Exception:
                        pass

            finally:
                # Clear progress-aware logging
                set_progress(None)

        logger.info(
            f"Consolidation complete: {self.summary.processed} processed, {self.summary.errors} errors"
        )
        return self.summary
