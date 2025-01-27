from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..config import Config, SourceConfig
import logging

logger = logging.getLogger(__name__)

class ProcessingResult:
    """Track results of processing a set of notes."""

    def __init__(self):
        """Initialize empty result."""
        self.processed = 0
        self.from_cache = 0
        self.regenerated = 0
        self.skipped = 0
        self.documents_processed = 0
        self.documents_generated = 0
        self.documents_from_cache = 0
        self.documents_skipped = 0
        self.images_processed = 0
        self.images_generated = 0
        self.images_from_cache = 0
        self.images_skipped = 0
        self.gpt_cache_hits = 0
        self.gpt_new_analyses = 0
        self.gpt_skipped = 0
        self.errors = []

    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)

    def merge(self, other: 'ProcessingResult'):
        """Merge another result into this one."""
        self.processed += other.processed
        self.from_cache += other.from_cache
        self.regenerated += other.regenerated
        self.skipped += other.skipped
        self.documents_processed += other.documents_processed
        self.documents_generated += other.documents_generated
        self.documents_from_cache += other.documents_from_cache
        self.documents_skipped += other.documents_skipped
        self.images_processed += other.images_processed
        self.images_generated += other.images_generated
        self.images_from_cache += other.images_from_cache
        self.images_skipped += other.images_skipped
        self.gpt_cache_hits += other.gpt_cache_hits
        self.gpt_new_analyses += other.gpt_new_analyses
        self.gpt_skipped += other.gpt_skipped
        self.errors.extend(other.errors)

    def __str__(self) -> str:
        """Return string representation."""
        parts = []
        if self.processed > 0:
            parts.append(f"{self.processed} processed")
        if self.from_cache > 0:
            parts.append(f"{self.from_cache} from cache")
        if self.regenerated > 0:
            parts.append(f"{self.regenerated} generated")
        if self.skipped > 0:
            parts.append(f"{self.skipped} skipped")
        if self.documents_processed > 0:
            parts.append(f"{self.documents_processed} documents processed")
        if self.documents_from_cache > 0:
            parts.append(f"{self.documents_from_cache} documents from cache")
        if self.documents_skipped > 0:
            parts.append(f"{self.documents_skipped} documents skipped")
        if self.images_processed > 0:
            parts.append(f"{self.images_processed} images processed")
        if self.images_from_cache > 0:
            parts.append(f"{self.images_from_cache} images from cache")
        if self.images_skipped > 0:
            parts.append(f"{self.images_skipped} images skipped")
        if self.gpt_cache_hits > 0:
            parts.append(f"{self.gpt_cache_hits} GPT analyses from cache")
        if self.gpt_new_analyses > 0:
            parts.append(f"{self.gpt_new_analyses} new GPT analyses")
        if self.gpt_skipped > 0:
            parts.append(f"{self.gpt_skipped} GPT analyses skipped")
        if self.errors:
            parts.append(f"{len(self.errors)} errors")
        return ", ".join(parts) if parts else "No results"

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
