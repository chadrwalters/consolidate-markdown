import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..attachments.processor import AttachmentProcessor
from ..config import Config, SourceConfig
from .result import ProcessingResult

logger = logging.getLogger(__name__)


class SourceProcessor(ABC):
    """Base class for all source processors."""

    def __init__(self, source_config: SourceConfig):
        """Initialize processor with source configuration."""
        self.source_config = source_config
        self.validate_called = False
        self._attachment_processor: Optional[AttachmentProcessor] = None
        self._temp_dir: Optional[Path] = None

    @property
    def attachment_processor(self) -> AttachmentProcessor:
        """Get the attachment processor, ensuring it is initialized."""
        if self._attachment_processor is None:
            raise RuntimeError(
                "Attachment processor not initialized - must call process() first"
            )
        return self._attachment_processor

    @attachment_processor.setter
    def attachment_processor(self, value: Optional[AttachmentProcessor]) -> None:
        """Set the attachment processor."""
        self._attachment_processor = value

    def validate(self) -> None:
        """Validate source configuration.

        Raises:
            ValueError: If source configuration is invalid.
        """
        self.validate_called = True
        # Check source directory exists and is readable
        if not self.source_config.src_dir.exists():
            raise ValueError(
                f"Source directory does not exist: {self.source_config.src_dir}"
            )
        if not self.source_config.src_dir.is_dir():
            raise ValueError(
                f"Source path is not a directory: {self.source_config.src_dir}"
            )

        # Check destination parent directory exists
        dest_parent = self.source_config.dest_dir.parent
        if not dest_parent.exists():
            raise ValueError(
                f"Destination parent directory does not exist: {dest_parent}"
            )

    def _ensure_dest_dir(self) -> None:
        """Ensure destination directory exists."""
        self.source_config.dest_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_path(self, path: Path) -> Path:
        """Handle paths with spaces and special characters."""
        return Path(str(path).replace("\\", "/"))

    def _create_temp_dir(self, config: Config) -> Path:
        """Create a temporary directory for processing."""
        if self._temp_dir is None:
            # Create a unique temp dir for this processor instance
            self._temp_dir = config.global_config.cm_dir / "temp"
            self._temp_dir.mkdir(parents=True, exist_ok=True)
        return self._temp_dir

    def _cleanup_temp_dir(self):
        """Clean up temporary directory after processing."""
        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp dir {self._temp_dir}: {e}")
            self._temp_dir = None

    def process(self, config: Config) -> ProcessingResult:
        """Process the source."""
        # Initialize attachment processor if needed
        if self._attachment_processor is None:
            temp_dir = self._create_temp_dir(config)
            self._attachment_processor = AttachmentProcessor(temp_dir)

        try:
            return self._process_impl(config)
        finally:
            # Clean up
            if self._attachment_processor is not None:
                try:
                    self._attachment_processor.cleanup()
                except Exception as e:
                    logger.error(f"Error during attachment processor cleanup: {e}")
                self._attachment_processor = None

            try:
                self._cleanup_temp_dir()
            except Exception as e:
                logger.error(f"Error during temp directory cleanup: {e}")

    @abstractmethod
    def _process_impl(self, config: Config) -> ProcessingResult:
        """Implementation of source processing."""
        pass
