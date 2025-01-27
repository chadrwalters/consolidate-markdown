from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..config import Config, SourceConfig
import logging

logger = logging.getLogger(__name__)

class ProcessingResult:
    """Result of processing a source."""
    def __init__(self):
        self.processed = 0  # Number of notes/bookmarks processed
        self.skipped = 0  # Number of files skipped
        self.documents_processed = 0  # Number of documents processed
        self.images_processed = 0  # Number of images processed
        self.images_skipped = 0  # Number of images skipped
        self.errors = []  # List of error messages
        logger.debug("Created new ProcessingResult")

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        logger.debug(f"Added error: {error}")

    def merge(self, other: 'ProcessingResult') -> None:
        """Merge another result into this one."""
        logger.debug(f"Merging results - Before: {self}")
        self.processed += other.processed
        self.skipped += other.skipped
        self.documents_processed += other.documents_processed
        self.images_processed += other.images_processed
        self.images_skipped += other.images_skipped
        self.errors.extend(other.errors)
        logger.debug(f"Merging results - After: {self}")

    def __str__(self) -> str:
        """String representation of the result."""
        return (
            f"ProcessingResult(processed={self.processed}, "
            f"images_processed={self.images_processed}, "
            f"images_skipped={self.images_skipped}, "
            f"skipped={self.skipped}, "
            f"documents_processed={self.documents_processed}, "
            f"errors={len(self.errors)})"
        )

class SourceProcessor(ABC):
    """Base class for all source processors."""

    def __init__(self, source_config: SourceConfig):
        self.source_config = source_config

    @abstractmethod
    def process(self, config: Config) -> ProcessingResult:
        """Process all files in the source directory."""
        pass

    def validate(self) -> tuple[bool, List[str]]:
        """Validate source configuration."""
        errors = []

        # Check source directory exists and is readable
        if not self.source_config.src_dir.exists():
            errors.append(f"Source directory does not exist: {self.source_config.src_dir}")
        elif not self.source_config.src_dir.is_dir():
            errors.append(f"Source path is not a directory: {self.source_config.src_dir}")

        # Check destination parent exists
        if not self.source_config.dest_dir.parent.exists():
            errors.append(f"Destination parent directory does not exist: {self.source_config.dest_dir.parent}")

        return len(errors) == 0, errors

    def _ensure_dest_dir(self) -> None:
        """Ensure destination directory exists."""
        self.source_config.dest_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_path(self, path: Path) -> Path:
        """Handle paths with spaces and special characters."""
        return Path(str(path).replace('\\', '/'))
