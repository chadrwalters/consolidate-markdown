"""Main entry point for the consolidate-markdown tool."""

import argparse
import logging
import sys
from pathlib import Path

from consolidate_markdown.config import load_config
from consolidate_markdown.processors.bear import BearProcessor
from consolidate_markdown.processors.xbookmarks import XBookmarksProcessor
from consolidate_markdown.runner import Runner

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
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set the logging level",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging (same as --log-level DEBUG)",
    )
    return parser.parse_args()


def main() -> int:
    """Run the consolidation process.

    Returns:
        0 on success, non-zero on error.
    """
    args = parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else getattr(logging, args.log_level)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Load configuration
        config = load_config(args.config)

        # Update global config with command line options
        config.global_config.no_image = args.no_image
        config.global_config.force_generation = args.force
        config.global_config.log_level = args.log_level

        # Run consolidation
        runner = Runner(config)
        summary = runner.run()

        # Log summary
        logger.info("\n%s", summary.get_summary())

        if summary.errors:
            logger.error("Errors occurred during processing:")
            for error in summary.errors:
                logger.error(str(error))
            return 1

        return 0

    except Exception as e:
        logger.error("Error: %s", str(e))
        if args.debug:
            logger.exception(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
