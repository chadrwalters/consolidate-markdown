import logging
import logging.handlers
from pathlib import Path
from typing import Optional

def setup_logging(cm_dir: Path, log_level: str) -> None:
    """Configure logging with file and console output."""
    # Create logs directory
    log_dir = cm_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # File handler with rotation
    log_file = log_dir / "consolidate.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Suppress HTTP client debug logging
    logging.getLogger("httpcore").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("openai").setLevel(logging.INFO)

class SummaryLogger:
    """Track processing statistics and generate summary."""
    def __init__(self):
        self.stats = {
            'processed': 0,
            'skipped': 0,
            'documents_processed': 0,
            'images_processed': 0,
            'images_skipped': 0,
            'errors': []
        }
        self.source_stats = {}

    def add_processed(self, source_type: str):
        """Record a successfully processed file."""
        self.stats['processed'] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]['processed'] += 1

    def add_skipped(self, source_type: str):
        """Record a skipped file."""
        self.stats['skipped'] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]['skipped'] += 1

    def add_images_skipped(self, source_type: str):
        """Record a skipped image."""
        self.stats['images_skipped'] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]['images_skipped'] += 1

    def add_documents_processed(self, source_type: str):
        """Record a processed document."""
        self.stats['documents_processed'] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]['documents_processed'] += 1

    def add_images_processed(self, source_type: str):
        """Record a processed image."""
        self.stats['images_processed'] += 1
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]['images_processed'] += 1

    def add_error(self, source_type: str, error: str):
        """Record an error."""
        self.stats['errors'].append(error)
        if source_type not in self.source_stats:
            self._init_source_stats(source_type)
        self.source_stats[source_type]['errors'].append(error)

    def _init_source_stats(self, source_type: str):
        """Initialize stats for a new source type."""
        self.source_stats[source_type] = {
            'processed': 0,
            'skipped': 0,
            'documents_processed': 0,
            'images_processed': 0,
            'images_skipped': 0,
            'errors': []
        }

    def get_summary(self) -> str:
        """Generate end-of-run summary."""
        lines = ["───────────────────────────────────────────────"]

        # Per-source summaries
        for source_type, stats in self.source_stats.items():
            lines.append(f"Summary for {source_type.title()} Source:")
            lines.append(f"  - {stats['processed']} notes processed")
            lines.append(f"  - {stats['images_processed']} images processed")
            lines.append(f"  - {stats['images_skipped']} images skipped")
            lines.append(f"  - {stats['documents_processed']} documents processed")
            if stats['errors']:
                lines.append(f"  - {len(stats['errors'])} errors:")
                for error in stats['errors']:
                    lines.append(f"    -> {error}")
            lines.append("")

        # Overall summary
        lines.append("───────────────────────────────────────────────")
        lines.append(
            f"Overall: {self.stats['processed']} notes processed, "
            f"{self.stats['images_processed']} images processed, "
            f"{self.stats['images_skipped']} images skipped, "
            f"{self.stats['documents_processed']} documents processed, "
            f"{len(self.stats['errors'])} errors"
        )
        lines.append("───────────────────────────────────────────────")

        return "\n".join(lines)
