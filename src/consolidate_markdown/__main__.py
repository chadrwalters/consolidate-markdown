"""Main entry point for the consolidate-markdown tool."""

import argparse
import logging
import sys
from pathlib import Path

from consolidate_markdown.config import load_config
from consolidate_markdown.log_setup import setup_logging
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
        "--processor",
        type=str,
        choices=list(Runner.PROCESSORS.keys()),
        help="Run only the specified processor type",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit processing to the last N items per source",
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


def ensure_cm_directory(config_path: Path) -> None:
    """Ensure the .cm directory exists.

    Args:
        config_path: Path to the config file, used to determine workspace root.
    """
    workspace_root = config_path.parent
    cm_dir = workspace_root / ".cm"
    log_dir = cm_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)


def main() -> int:
    """Main entry point.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    args = parse_args()
    config = load_config(args.config)

    # Apply command line overrides
    if args.log_level:
        config.global_config.log_level = args.log_level
    if args.debug:
        config.global_config.log_level = "DEBUG"
    if args.no_image:
        config.global_config.no_image = True
    if args.force:
        config.global_config.force_generation = True

    # Set up logging
    setup_logging(config)

    # Create and run the processor
    runner = Runner(config, delete_existing=args.delete)
    if args.processor:
        runner.selected_processor = args.processor
    if args.limit:
        runner.processing_limit = args.limit

    try:
        result = runner.run()
        print(str(result))
        if result.errors:
            return 1
        return 0
    except KeyboardInterrupt:
        logger.info("Processing cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
