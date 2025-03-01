"""Main entry point for the consolidate-markdown tool."""

import argparse
import logging
import shutil
import sys
from pathlib import Path

from consolidate_markdown.config import load_config
from consolidate_markdown.exceptions import ConfigurationError, DependencyError
from consolidate_markdown.log_setup import setup_logging
from consolidate_markdown.output import print_deletion_message, print_summary
from consolidate_markdown.processors.bear import BearProcessor
from consolidate_markdown.processors.xbookmarks import XBookmarksProcessor
from consolidate_markdown.runner import Runner
from consolidate_markdown.utils import validate_api_keys, validate_external_dependencies

logger = logging.getLogger(__name__)

# Register processors
Runner.PROCESSORS["bear"] = BearProcessor
Runner.PROCESSORS["xbookmarks"] = XBookmarksProcessor


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Consolidate markdown files from various sources"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.toml"),
        help="Path to configuration file (default: config.toml)",
    )
    parser.add_argument(
        "--no-image",
        action="store_true",
        help="Skip image analysis",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration of all files",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete existing output files before processing",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level",
    )
    parser.add_argument(
        "--processor",
        choices=list(Runner.PROCESSORS.keys()),
        help="Only run a specific processor",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of items to process per source",
    )
    parser.add_argument(
        "--skip-dependency-check",
        action="store_true",
        help="Skip checking for external dependencies",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        sys.exit(1)

    # Update config with command line arguments
    config.global_config.no_image = args.no_image
    config.global_config.force_generation = args.force
    config.global_config.log_level = getattr(logging, args.log_level)

    # Set up logging
    setup_logging(config)

    # Validate external dependencies unless explicitly skipped
    if not args.skip_dependency_check:
        try:
            logger.debug("Checking external dependencies...")
            validate_external_dependencies()
        except DependencyError as e:
            logger.error(f"Dependency check failed: {str(e)}")
            logger.error("Use --skip-dependency-check to bypass this check if needed.")
            sys.exit(1)

    # Validate API keys
    try:
        logger.debug("Validating API keys...")
        validate_api_keys(config)
    except ConfigurationError as e:
        logger.error(f"API key validation failed: {str(e)}")
        sys.exit(1)

    # Create output directories
    config.global_config.cm_dir.mkdir(parents=True, exist_ok=True)
    for source in config.sources:
        source.dest_dir.mkdir(parents=True, exist_ok=True)

    # Delete existing files if requested
    if args.delete:
        # Delete .cm directory
        if config.global_config.cm_dir.exists():
            print_deletion_message(str(config.global_config.cm_dir))
            shutil.rmtree(config.global_config.cm_dir)
            config.global_config.cm_dir.mkdir(parents=True, exist_ok=True)

        # Delete output directories
        for source in config.sources:
            if source.dest_dir.exists():
                print_deletion_message(str(source.dest_dir))
                shutil.rmtree(source.dest_dir)
                source.dest_dir.mkdir(parents=True, exist_ok=True)

    # Create and run the processor
    runner = Runner(config)
    if args.processor:
        runner.selected_processor = args.processor
    if args.limit:
        runner.processing_limit = args.limit

    try:
        result = runner.run()
        print_summary(result)
        if result.errors:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
