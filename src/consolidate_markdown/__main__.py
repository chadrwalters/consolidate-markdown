import argparse
import logging
import os
import sys
from pathlib import Path

from .config import load_config
from .logging import setup_logging
from .runner import Runner

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Consolidate Markdown files from multiple sources"
    )

    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to TOML configuration file"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing of all files"
    )

    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete existing output files before processing"
    )

    parser.add_argument(
        "--no-image",
        action="store_true",
        help="Skip GPT image analysis"
    )

    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Process sources sequentially (no parallel processing)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Override logging level from config"
    )

    return parser.parse_args()

def main() -> int:
    """Main entry point."""
    try:
        # Parse arguments
        args = parse_args()

        # Load configuration
        config = load_config(args.config)

        # Override config with command line arguments
        config.global_config.force_generation = args.force
        config.global_config.no_image = args.no_image
        if args.log_level:
            config.global_config.log_level = args.log_level

        # Handle --delete
        if args.delete:
            for source in config.sources:
                if source.dest_dir.exists():
                    import shutil
                    shutil.rmtree(source.dest_dir)
                if config.global_config.cm_dir.exists():
                    shutil.rmtree(config.global_config.cm_dir)

        # Setup logging
        setup_logging(config.global_config.cm_dir, config.global_config.log_level)
        logger = logging.getLogger(__name__)

        # Run processing
        logger.info("Starting consolidation process...")
        logger.info(f"Using config file: {args.config}")
        logger.info(f"Working directory: {config.global_config.cm_dir}")

        runner = Runner(config)
        summary = runner.run(parallel=not args.sequential)

        # Print summary
        print("\n" + summary.get_summary())

        return 0

    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        return 130
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
