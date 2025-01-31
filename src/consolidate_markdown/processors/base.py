import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from ..attachments.gpt import GPTProcessor
from ..attachments.processor import AttachmentMetadata, AttachmentProcessor
from ..config import Config, SourceConfig
from .result import ProcessingResult

logger = logging.getLogger(__name__)


class AttachmentHandlerMixin:
    """Mixin class for handling attachments in processors."""

    def _format_image(
        self,
        image_path: Path,
        metadata: AttachmentMetadata,
        config: Config,
        result: ProcessingResult,
        cache_manager=None,
    ) -> str:
        """Format an image with optional GPT description."""
        size_kb = metadata.size_bytes / 1024
        dimensions = metadata.dimensions or (0, 0)

        # Get image description if enabled
        description = ""
        if not config.global_config.no_image:
            try:
                gpt = GPTProcessor(
                    config.global_config.openai_key or "dummy-key",
                    cache_manager,
                )
                description = gpt.describe_image(image_path, result)
            except Exception as e:
                logger.error(f"GPT processing failed for {image_path}: {str(e)}")
                gpt = GPTProcessor("dummy-key")
                description = gpt.get_placeholder(image_path, result)
        else:
            gpt = GPTProcessor("dummy-key")
            description = gpt.get_placeholder(image_path, result)

        return f"""
<!-- EMBEDDED IMAGE: {image_path.name} -->
<details>
<summary>🖼️ {image_path.name} ({dimensions[0]}x{dimensions[1]}, {size_kb:.0f}KB)</summary>

{description}

</details>
"""

    def _format_document(
        self,
        doc_path: Path,
        metadata: AttachmentMetadata,
        alt_text: Optional[str] = None,
        result: Optional[ProcessingResult] = None,
    ) -> str:
        """Format a document attachment."""
        size_kb = metadata.size_bytes / 1024
        content = (
            metadata.markdown_content
            or "[Document content will be converted in Phase 4]"
        )

        return f"""
<!-- EMBEDDED DOCUMENT: {doc_path.name} -->
<details>
<summary>📄 {alt_text or doc_path.name} ({size_kb:.0f}KB)</summary>

{content}

</details>
"""

    def _process_attachment(
        self,
        attachment_path: Path,
        output_dir: Path,
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult,
        alt_text: Optional[str] = None,
        is_image: bool = True,
    ) -> Optional[str]:
        """Process a single attachment and return its markdown representation."""
        try:
            if not attachment_path.exists():
                logger.warning(f"Attachment not found: {attachment_path}")
                return None

            # Process the file
            temp_path, metadata = attachment_processor.process_file(
                attachment_path,
                force=config.global_config.force_generation,
                result=result,
            )

            # Copy processed file to output directory
            output_path = output_dir / attachment_path.name
            if temp_path.suffix != attachment_path.suffix:
                # If the extension changed (e.g. svg -> jpg), update the output path
                output_path = output_path.with_suffix(temp_path.suffix)
            shutil.copy2(temp_path, output_path)

            # Format based on type
            if metadata.is_image:
                result.images_processed += 1
                result.images_generated += 1
                return self._format_image(output_path, metadata, config, result)
            else:
                result.documents_processed += 1
                result.documents_generated += 1
                return self._format_document(output_path, metadata, alt_text, result)

        except Exception as e:
            logger.error(f"Error processing attachment {attachment_path}: {str(e)}")
            if is_image:
                result.images_skipped += 1
            return None


class SourceProcessor(AttachmentHandlerMixin, ABC):
    """Base class for all source processors."""

    def __init__(self, source_config: SourceConfig):
        """Initialize processor with source configuration."""
        self.source_config = source_config
        self.validate_called = False
        self._attachment_processor: Optional[AttachmentProcessor] = None
        self._temp_dir: Optional[Path] = None
        self.item_limit: Optional[int] = None  # Maximum number of items to process

    @property
    def attachment_processor(self) -> AttachmentProcessor:
        """Get the attachment processor instance."""
        if self._attachment_processor is None:
            self._attachment_processor = AttachmentProcessor(
                self.source_config.dest_dir
            )
        return self._attachment_processor

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

    def _apply_limit(self, items: List[Path]) -> List[Path]:
        """Apply item limit to sorted items.

        Args:
            items: List of paths to sort and limit.

        Returns:
            Limited list of paths, sorted by modification time (newest first).
        """
        if not items or self.item_limit is None:
            return items
        items.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return items[: self.item_limit]

    def process(self, config: Config) -> ProcessingResult:
        """Process the source."""
        try:
            # Ensure output directory exists
            self._ensure_dest_dir()

            # Process files
            result = self._process_impl(config)

            return result
        finally:
            # Clean up temporary files
            self.cleanup()

    @abstractmethod
    def _process_impl(self, config: Config) -> ProcessingResult:
        """Implementation of source processing."""
        pass

    def cleanup(self) -> None:
        """Clean up temporary files."""
        try:
            if self._attachment_processor is not None:
                self._attachment_processor.cleanup()
                self._attachment_processor = None
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Ensure cleanup is called when object is destroyed."""
        self.cleanup()
