"""Logging configuration."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

from .config import Config

logger = logging.getLogger(__name__)


def ensure_log_file(log_file: Path) -> None:
    """Ensure the log file exists.

    Args:
        log_file: Path to the log file
    """
    if not log_file.exists():
        log_file.touch()


def setup_logging(config: Config) -> None:
    """Set up logging configuration."""
    # First, configure third-party loggers to prevent debug output
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("openai._base_client").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("httpcore").setLevel(logging.INFO)

    # Create log directory if it doesn't exist
    log_dir = config.global_config.cm_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.global_config.log_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Configure file logging
    log_file = log_dir / "consolidate_markdown.log"
    ensure_log_file(log_file)

    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Configure Rich console logging
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_path=False,
        level=config.global_config.log_level,
        show_time=False,  # Time is already in the message
        enable_link_path=False,  # Don't show file links
    )
    root_logger.addHandler(console_handler)

    logger.debug("Logging configured successfully")


class SummaryLogger:
    """Track processing statistics and generate summary."""

    def __init__(self):
        self.stats = {
            "processed": 0,
            "generated": 0,
            "from_cache": 0,
            "skipped": 0,
            "documents_processed": 0,
            "documents_generated": 0,
            "documents_from_cache": 0,
            "documents_skipped": 0,
            "images_processed": 0,
            "images_generated": 0,
            "images_from_cache": 0,
            "images_skipped": 0,
            "gpt_generated": 0,
            "gpt_from_cache": 0,
            "gpt_skipped": 0,
            "errors": [],
        }
        self.source_stats = {}

    def _init_source_stats(self, source_type: str):
        """Initialize stats for a new source type."""
        self.source_stats[source_type] = {
            "processed": 0,
            "generated": 0,
            "from_cache": 0,
            "skipped": 0,
            "documents_processed": 0,
            "documents_generated": 0,
            "documents_from_cache": 0,
            "documents_skipped": 0,
            "images_processed": 0,
            "images_generated": 0,
            "images_from_cache": 0,
            "images_skipped": 0,
            "gpt_generated": 0,
            "gpt_from_cache": 0,
            "gpt_skipped": 0,
            "errors": [],
        }

    def add_from_cache(self, source_type: str):
        """Record a note loaded from cache."""
        self.stats["processed"] += 1
        self.stats["from_cache"] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["processed"] += 1
        self.source_stats[source_type]["from_cache"] += 1

    def add_generated(self, source_type: str):
        """Record a generated note."""
        self.stats["processed"] += 1
        self.stats["generated"] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["processed"] += 1
        self.source_stats[source_type]["generated"] += 1

    def add_skipped(self, source_type: str):
        """Record a skipped note."""
        self.stats["skipped"] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["skipped"] += 1

    def add_document_generated(self, source_type: str):
        """Record a generated document."""
        self.stats["documents_processed"] += 1
        self.stats["documents_generated"] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["documents_processed"] += 1
        self.source_stats[source_type]["documents_generated"] += 1

    def add_document_from_cache(self, source_type: str):
        """Record a document loaded from cache."""
        self.stats["documents_processed"] += 1
        self.stats["documents_from_cache"] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["documents_processed"] += 1
        self.source_stats[source_type]["documents_from_cache"] += 1

    def add_document_skipped(self, source_type: str):
        """Record a skipped document."""
        self.stats["documents_skipped"] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["documents_skipped"] += 1

    def add_image_generated(self, source_type: str):
        """Record a generated image."""
        self.stats["images_processed"] += 1
        self.stats["images_generated"] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["images_processed"] += 1
        self.source_stats[source_type]["images_generated"] += 1

    def add_image_from_cache(self, source_type: str):
        """Record an image loaded from cache."""
        self.stats["images_processed"] += 1
        self.stats["images_from_cache"] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["images_processed"] += 1
        self.source_stats[source_type]["images_from_cache"] += 1

    def add_image_skipped(self, source_type: str):
        """Record a skipped image."""
        self.stats["images_skipped"] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["images_skipped"] += 1

    def add_gpt_generated(self, source_type: str):
        """Record a generated GPT analysis."""
        self.stats["gpt_generated"] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["gpt_generated"] += 1

    def add_gpt_from_cache(self, source_type: str):
        """Record a GPT analysis loaded from cache."""
        self.stats["gpt_from_cache"] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["gpt_from_cache"] += 1

    def add_gpt_skipped(self, source_type: str):
        """Record a skipped GPT analysis."""
        self.stats["gpt_skipped"] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["gpt_skipped"] += 1

    def add_error(self, source_type: str, error: str):
        """Record an error."""
        self.stats["errors"].append(error)
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]["errors"].append(error)

    @property
    def errors(self) -> list[str]:
        """Get all errors."""
        return self.stats["errors"]

    def _format_category_stats(
        self, name: str, total: int, generated: int, from_cache: int, skipped: int
    ) -> list[str]:
        """Format statistics for a category."""
        lines = []
        if total > 0 or skipped > 0:
            lines.append(f"{name} ({total + skipped} total)")
            if generated > 0:
                lines.append(f"  Generated:  {generated}")
            if from_cache > 0:
                lines.append(f"  From Cache: {from_cache}")
            if skipped > 0:
                lines.append(f"  Skipped:    {skipped}")
            lines.append("")
        return lines

    def get_summary(self) -> str:
        """Generate end-of-run summary."""
        lines = []

        # Per-source summaries
        for source_type, stats in self.source_stats.items():
            lines.append("───────────────────────────────────────────────")
            lines.append(f"{source_type.title()} Source Summary")
            lines.append("───────────────────────────────────────────────")

            # Notes
            lines.extend(
                self._format_category_stats(
                    "Notes",
                    stats["processed"],
                    stats["generated"],
                    stats["from_cache"],
                    stats["skipped"],
                )
            )

            # Documents
            lines.extend(
                self._format_category_stats(
                    "Documents",
                    stats["documents_processed"],
                    stats["documents_generated"],
                    stats["documents_from_cache"],
                    stats["documents_skipped"],
                )
            )

            # Images
            lines.extend(
                self._format_category_stats(
                    "Images",
                    stats["images_processed"],
                    stats["images_generated"],
                    stats["images_from_cache"],
                    stats["images_skipped"],
                )
            )

            # GPT Analysis
            if (
                stats["gpt_generated"] > 0
                or stats["gpt_from_cache"] > 0
                or stats["gpt_skipped"] > 0
            ):
                lines.extend(
                    self._format_category_stats(
                        "GPT Analysis",
                        stats["gpt_generated"] + stats["gpt_from_cache"],
                        stats["gpt_generated"],
                        stats["gpt_from_cache"],
                        stats["gpt_skipped"],
                    )
                )

            if stats["errors"]:
                lines.append("Errors:")
                for error in stats["errors"]:
                    lines.append(f"  -> {error}")
                lines.append("")

        # Overall statistics
        lines.append("───────────────────────────────────────────────")
        lines.append("Overall Statistics")
        lines.append("───────────────────────────────────────────────")

        # Notes
        lines.extend(
            self._format_category_stats(
                "Notes",
                self.stats["processed"],
                self.stats["generated"],
                self.stats["from_cache"],
                self.stats["skipped"],
            )
        )

        # Documents
        lines.extend(
            self._format_category_stats(
                "Documents",
                self.stats["documents_processed"],
                self.stats["documents_generated"],
                self.stats["documents_from_cache"],
                self.stats["documents_skipped"],
            )
        )

        # Images
        lines.extend(
            self._format_category_stats(
                "Images",
                self.stats["images_processed"],
                self.stats["images_generated"],
                self.stats["images_from_cache"],
                self.stats["images_skipped"],
            )
        )

        # GPT Analysis
        if (
            self.stats["gpt_generated"] > 0
            or self.stats["gpt_from_cache"] > 0
            or self.stats["gpt_skipped"] > 0
        ):
            lines.extend(
                self._format_category_stats(
                    "GPT Analysis",
                    self.stats["gpt_generated"] + self.stats["gpt_from_cache"],
                    self.stats["gpt_generated"],
                    self.stats["gpt_from_cache"],
                    self.stats["gpt_skipped"],
                )
            )

        if self.stats["errors"]:
            lines.append(f"Errors: {len(self.stats['errors'])}")

        lines.append("───────────────────────────────────────────────")

        return "\n".join(lines)
