import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List, Optional, TypeVar

from rich.progress import Progress, TaskID

from ..attachments.gpt import GPTProcessor
from ..attachments.processor import AttachmentMetadata, AttachmentProcessor
from ..cache import CacheManager, quick_hash
from ..config import Config, SourceConfig
from ..utils import apply_limit, ensure_directory, should_process_from_cache
from .result import ProcessingResult

logger = logging.getLogger(__name__)
T = TypeVar("T")


class AttachmentHandlerMixin:
    """Mixin class for handling attachments in processors.

    This class provides methods for processing attachments and formatting them as comments
    in markdown files. Instead of copying attachment files to the output directory, it now
    embeds information about the attachments as comments in the markdown output.

    This approach creates a flat output directory structure with only markdown files and
    no physical attachment files or subdirectories, which has several benefits:
    - Simplified output directory structure
    - Reduced disk space usage (no duplicate files)
    - Preserved attachment metadata
    - Better compatibility with version control systems

    The comment format for images is:
    ```
    <!-- ATTACHMENT: IMAGE: filename.jpg (dimensions, size) -->
    <!-- GPT Description: description text -->
    ![description]()
    ```

    The comment format for documents is:
    ```
    <!-- ATTACHMENT: DOCUMENT: filename.pdf (size) -->
    <!-- Content: document content -->
    [filename]()
    ```

    For SVG images, the SVG content may be embedded directly within <details> tags
    in the markdown for inline display, while still using comment-based metadata.
    """

    @property
    @abstractmethod
    def _processor_type(self) -> str:
        """Get the processor type.

        Returns:
            The processor type string
        """
        pass

    def _format_image(
        self,
        image_path: Path,
        metadata: AttachmentMetadata,
        config: Config,
        result: ProcessingResult,
        cache_manager: Optional[CacheManager] = None,
    ) -> str:
        """Format an image as a comment-based reference with optional GPT description.

        Instead of creating a link to a copied image file, this method generates a comment
        containing information about the image (filename, dimensions, size) and includes
        the GPT description as a separate comment. It also adds an empty markdown image
        syntax for better compatibility with markdown viewers.

        For SVG images, the SVG content may be embedded directly within <details> tags
        in the markdown for inline display, while still using comment-based metadata.

        The comment format is:
        ```
        <!-- ATTACHMENT: IMAGE: filename.jpg (dimensions, size) -->
        <!-- GPT Description: description text -->
        ![description]()
        ```

        Args:
            image_path: Path to the image file
            metadata: Metadata about the image
            config: Configuration
            result: Processing result
            cache_manager: Optional cache manager

        Returns:
            Markdown representation of the image as comments
        """
        size_kb = metadata.size / 1024
        dimensions = metadata.dimensions or (0, 0)
        is_svg = image_path.suffix.lower() == ".svg"

        # Get image description if enabled
        description = ""
        if not config.global_config.no_image:
            try:
                gpt = GPTProcessor(config.global_config, cache_manager)
                # For SVGs, use the PNG version for GPT analysis
                if is_svg and hasattr(metadata, "png_path"):
                    description = gpt.describe_image(
                        Path(metadata.png_path), result, self._processor_type
                    )
                else:
                    description = gpt.describe_image(
                        image_path, result, self._processor_type
                    )
            except Exception as e:
                logger.error(f"GPT processing failed for {image_path}: {str(e)}")
                gpt = GPTProcessor(config.global_config, cache_manager)
                description = gpt.get_placeholder(
                    image_path, result, self._processor_type
                )
        else:
            gpt = GPTProcessor(config.global_config, cache_manager)
            description = gpt.get_placeholder(image_path, result, self._processor_type)

        # Handle SVG files - embed content directly
        if is_svg and hasattr(metadata, "inlined_content"):
            return f"""<!-- ATTACHMENT: SVG: {image_path.name} ({dimensions[0]}x{dimensions[1]}, {size_kb:.0f}KB) -->
<!-- GPT Description: {description.strip()} -->
![{description.strip()}]()"""

        # Add comment-based image reference instead of markdown image link
        return f"""<!-- ATTACHMENT: IMAGE: {image_path.name} ({dimensions[0]}x{dimensions[1]}, {size_kb:.0f}KB) -->
<!-- GPT Description: {description.strip()} -->
![{description.strip()}]()"""

    def _format_document(
        self,
        doc_path: Path,
        metadata: AttachmentMetadata,
        alt_text: Optional[str] = None,
        result: Optional[ProcessingResult] = None,
    ) -> str:
        """Format a document as a comment-based reference.

        Instead of creating a link to a copied document file, this method generates a comment
        containing information about the document (filename, size) and includes the document
        content as a separate comment. It also adds an empty markdown link syntax for better
        compatibility with markdown viewers.

        The comment format is:
        ```
        <!-- ATTACHMENT: DOCUMENT: filename.pdf (size) -->
        <!-- Content: document content -->
        [filename]()
        ```

        Args:
            doc_path: Path to the document file
            metadata: Metadata about the document
            alt_text: Optional alternative text for the document
            result: Optional processing result

        Returns:
            Markdown representation of the document as comments
        """
        size_kb = metadata.size / 1024

        # Handle PDFs differently
        if doc_path.suffix.lower() == ".pdf":
            content = metadata.markdown_content or "PDF content not extracted"
            link_text = alt_text or doc_path.name
            return f"""<!-- ATTACHMENT: PDF: {doc_path.name} ({size_kb:.0f}KB) -->
<!-- Content: {content.strip()} -->
[{link_text}]()"""

        # Handle other documents
        content = (
            metadata.markdown_content
            or "[Document content will be converted in Phase 4]"
        )
        link_text = alt_text or doc_path.name
        return f"""<!-- ATTACHMENT: DOCUMENT: {doc_path.name} ({size_kb:.0f}KB) -->
<!-- Content: {content.strip()} -->
[{link_text}]()"""

    def _process_attachment(
        self,
        attachment_path: Path,
        output_dir: Path,  # Kept for compatibility but not used for file operations
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult,
        alt_text: Optional[str] = None,
        is_image: bool = True,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None,
    ) -> Optional[str]:
        """Process an attachment and generate a comment-based representation.

        This method processes an attachment file (image or document) and generates
        a comment-based representation of the attachment instead of copying the file
        to the output directory.

        The processing steps are:
        1. Process the attachment using the AttachmentProcessor to extract metadata
        2. For images, generate a comment with image information and optional GPT description
        3. For documents, generate a comment with document information and content
        4. Return the comment-based representation as a string

        Args:
            attachment_path: Path to the attachment file
            output_dir: Output directory (kept for compatibility but not used for file operations)
            attachment_processor: Processor for handling attachments
            config: Configuration
            result: Processing result
            alt_text: Optional alternative text for the attachment
            is_image: Whether the attachment is an image
            progress: Optional progress bar
            task_id: Optional task ID for progress reporting

        Returns:
            Markdown representation of the attachment as comments, or None if processing failed
        """
        try:
            logger.info(f"Processing attachment: {attachment_path}")

            if not attachment_path.exists():
                logger.warning(f"Attachment not found: {attachment_path}")
                if progress and task_id is not None:
                    progress.advance(task_id)
                return None

            logger.info(f"Processing attachment file: {attachment_path}")

            # Process the file
            temp_path, metadata = attachment_processor.process_file(
                attachment_path,
                force=config.global_config.force_generation,
                result=result,
            )

            logger.info(
                f"Processed {attachment_path.name}: is_image={metadata.is_image}, markdown_content_length={len(metadata.markdown_content) if metadata.markdown_content else 0}"
            )

            # No longer copying files to output directory
            # Just format based on type
            if metadata.is_image:
                logger.info(f"Updating image statistics for {self._processor_type}")
                result.add_image_generated(
                    self._processor_type
                )  # Always count as generated for now
                formatted = self._format_image(
                    attachment_path,  # Use original path since we're not copying
                    metadata,
                    config,
                    result,
                    getattr(
                        self, "cache_manager", None
                    ),  # Use processor's cache manager if available
                )
            else:
                logger.info(f"Updating document statistics for {self._processor_type}")
                result.add_document_generated(
                    self._processor_type
                )  # Always count as generated for now
                formatted = self._format_document(
                    attachment_path,  # Use original path since we're not copying
                    metadata,
                    alt_text,
                    result,
                )

            if progress and task_id is not None:
                progress.advance(task_id)

            return formatted

        except Exception as e:
            logger.error(f"Error processing attachment {attachment_path}: {str(e)}")
            if is_image:
                result.add_image_skipped(self._processor_type)
            else:
                result.add_document_skipped(self._processor_type)
            if progress and task_id is not None:
                progress.advance(task_id)
            return None


class SourceProcessor(AttachmentHandlerMixin, ABC):
    """Base class for all source processors."""

    def __init__(
        self, source_config: SourceConfig, cache_manager: Optional[CacheManager] = None
    ):
        """Initialize processor with source configuration."""
        self.source_config = source_config
        self.cache_manager = cache_manager or CacheManager(
            source_config.dest_dir.parent
        )
        self._attachment_processor: Optional[AttachmentProcessor] = None
        self.validate_called = False
        self._temp_dir: Optional[Path] = None
        self.item_limit: Optional[int] = None  # Maximum number of items to process
        self._progress: Optional[Progress] = None
        self._task_id: Optional[TaskID] = None
        self.__processor_type = source_config.type
        self.logger = logging.getLogger(__name__)
        self.validate()

        # Initialize attachment processor
        self._attachment_processor = None

    @property
    def attachment_processor(self) -> AttachmentProcessor:
        """Get the attachment processor instance."""
        if self._attachment_processor is None:
            self._attachment_processor = AttachmentProcessor(
                self.source_config.dest_dir
            )
        assert self._attachment_processor is not None
        return self._attachment_processor

    def set_progress(self, progress: Progress, task_id: TaskID) -> None:
        """Set the progress tracker for this processor.

        Args:
            progress: The progress instance to use
            task_id: The task ID for this processor
        """
        self._progress = progress
        self._task_id = task_id

    def set_limit(self, limit: Optional[int]) -> None:
        """Set a limit on the number of items to process.

        Args:
            limit: Maximum number of items to process, or None for no limit
        """
        self.item_limit = limit

    def _apply_limit(self, items: List[T]) -> List[T]:
        """Apply the item limit to a list.

        Args:
            items: The list to limit

        Returns:
            The limited list
        """
        return apply_limit(items, self.item_limit)

    def _ensure_dest_dir(self) -> None:
        """Ensure the destination directory exists."""
        ensure_directory(self.source_config.dest_dir)

    def _normalize_path(self, path: Path) -> Path:
        """Normalize a path for consistent handling.

        Args:
            path: The path to normalize

        Returns:
            Normalized path
        """
        return path

    def _create_temp_dir(self, config: Config) -> Path:
        """Create a temporary directory for processing.

        Args:
            config: The configuration to use

        Returns:
            Path to the temporary directory
        """
        if self._temp_dir is None:
            self._temp_dir = config.global_config.cm_dir / "temp"
            self._temp_dir.mkdir(parents=True, exist_ok=True)
        return self._temp_dir

    def _cleanup_temp_dir(self) -> None:
        """Clean up the temporary directory."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None

    def process(self, config: Config) -> ProcessingResult:
        """Process the source.

        Args:
            config: The configuration to use

        Returns:
            The processing result
        """
        # Clear cache if force flag is set
        if config.global_config.force_generation:
            self.cache_manager.clear_cache()

        # Ensure destination directory exists
        self._ensure_dest_dir()

        # Process the source
        return self._process_impl(config)

    @abstractmethod
    def _process_impl(self, config: Config) -> ProcessingResult:
        """Process the source implementation.

        Args:
            config: The configuration to use

        Returns:
            The processing result
        """
        pass

    def validate(self) -> None:
        """Validate source configuration.

        Raises:
            ValueError: If source configuration is invalid.
        """
        if not self.source_config.src_dir.exists():
            raise ValueError(
                f"Source directory does not exist: {self.source_config.src_dir}"
            )
        self.validate_called = True

    @property
    def _processor_type(self) -> str:
        """Get the processor type.

        Returns:
            The processor type string
        """
        return self.__processor_type

    def process_file_with_cache(
        self,
        file_path: Path,
        content: str,
        output_path: Path,
        config: Config,
        result: ProcessingResult,
        attachment_dir: Optional[Path] = None,
        process_func: Optional[Callable[[str], str]] = None,
    ) -> None:
        """Process a file with caching.

        Args:
            file_path: Path to the file
            content: Content of the file
            output_path: Path to write the output
            config: Configuration
            result: Processing result
            attachment_dir: Optional directory containing attachments
            process_func: Optional function to process the content
        """
        # Check if we need to process this file
        should_process, cached = should_process_from_cache(
            file_path,
            content,
            self.cache_manager,
            config.global_config.force_generation,
            attachment_dir,
        )

        if not should_process and cached and "processed_content" in cached:
            logger.debug(f"Using cached version of {file_path.name}")
            result.add_from_cache(self._processor_type)
            result.processed += 1  # Increment processed count for cached content

            # Write cached content
            output_path.write_text(cached["processed_content"], encoding="utf-8")
            return

        # Process file from scratch
        logger.debug(f"Processing {file_path.name} from scratch")

        processed_content = content
        if process_func:
            processed_content = process_func(content)

        # Write processed content
        output_path.write_text(processed_content, encoding="utf-8")

        # Update cache
        self.cache_manager.update_note_cache(
            str(file_path),
            quick_hash(content),
            output_path.stat().st_mtime,
            result.gpt_new_analyses,
            processed_content,
        )

        # Add to result stats
        result.add_generated(self._processor_type)
        result.processed += 1  # Increment processed count for newly generated content

    def cleanup(self) -> None:
        """Clean up temporary files."""
        self._cleanup_temp_dir()

    def __del__(self) -> None:
        """Ensure cleanup is called when object is destroyed."""
        self.cleanup()

    def format_completion_summary(self, result: ProcessingResult) -> str:
        """Format a standardized completion summary for the processor.

        Args:
            result: The processing result to summarize

        Returns:
            A formatted summary string
        """
        processor_name = self._processor_type.capitalize()

        # Format the main statistics
        summary = (
            f"Completed {processor_name} source: "
            f"{result.processed} processed "
            f"[{result.from_cache} from cache, {result.regenerated} regenerated], "
            f"{result.skipped} skipped"
        )

        # Add document statistics if any were processed
        if result.documents_processed > 0:
            summary += (
                f" | Documents: {result.documents_processed} processed "
                f"[{result.documents_from_cache} from cache, {result.documents_generated} generated], "
                f"{result.documents_skipped} skipped"
            )

        # Add image statistics if any were processed
        if result.images_processed > 0:
            summary += (
                f" | Images: {result.images_processed} processed "
                f"[{result.images_from_cache} from cache, {result.images_generated} generated], "
                f"{result.images_skipped} skipped"
            )

        # Add GPT statistics if any were processed
        if (
            result.gpt_cache_hits > 0
            or result.gpt_new_analyses > 0
            or result.gpt_skipped > 0
        ):
            summary += (
                f" | GPT: {result.gpt_cache_hits + result.gpt_new_analyses} processed "
                f"[{result.gpt_cache_hits} from cache, {result.gpt_new_analyses} generated], "
                f"{result.gpt_skipped} skipped"
            )

        # Add error count if any occurred
        if result.errors:
            summary += f" | Errors: {len(result.errors)}"

        return summary
