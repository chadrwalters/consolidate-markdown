"""Process X bookmarks."""

import logging
from pathlib import Path
from typing import Optional

from ..attachments.processor import AttachmentProcessor
from ..cache import CacheManager, quick_hash
from ..config import Config, SourceConfig
from .base import ProcessingResult, SourceProcessor

logger = logging.getLogger(__name__)


class XBookmarksProcessor(SourceProcessor):
    """Process X bookmarks and their attachments."""

    def __init__(
        self, source_config: SourceConfig, cache_manager: Optional[CacheManager] = None
    ):
        """Initialize processor."""
        super().__init__(source_config, cache_manager)
        self.validate()  # Call validate to ensure source directory exists
        if cache_manager is None:
            self.cache_manager = CacheManager(source_config.dest_dir.parent)
        else:
            self.cache_manager = cache_manager

    def _process_impl(self, config: Config) -> ProcessingResult:
        """Process all X bookmarks in the source directory."""
        result = ProcessingResult()

        # Clear cache if force flag is set
        if config.global_config.force_generation:
            self.cache_manager.clear_cache()

        # Ensure output directory exists
        self._ensure_dest_dir()

        # Get all bookmark directories and apply limit if set
        bookmark_dirs = [d for d in self.source_config.src_dir.iterdir() if d.is_dir()]
        bookmark_dirs = self._apply_limit(bookmark_dirs)

        # Process each bookmark directory
        for bookmark_dir in bookmark_dirs:
            try:
                logger.info(f"Processing X bookmark: {bookmark_dir.name}")
                bookmark_result = ProcessingResult()

                # Look for index file
                index_file = bookmark_dir / self.source_config.index_filename
                if not index_file.exists():
                    # Special case: don't count special directories in skip count
                    special_dirs = ["images", "markitdown", "temp"]
                    if bookmark_dir.name not in special_dirs:
                        logger.warning(f"No index file found in {bookmark_dir.name}")
                        result.add_skipped(self._processor_type)
                    else:
                        logger.debug(f"Skipping special directory: {bookmark_dir.name}")
                    continue

                # Check if we need to process this bookmark
                content = index_file.read_text(encoding="utf-8")
                content_hash = quick_hash(content)
                cached = self.cache_manager.get_note_cache(str(index_file))

                should_process = True
                if cached and not config.global_config.force_generation:
                    if cached["hash"] == content_hash:
                        # Check for any newer files in the bookmark directory
                        latest_file = max(
                            bookmark_dir.glob("*"),
                            key=lambda p: p.stat().st_mtime if p.is_file() else 0,
                            default=None,
                        )
                        if (
                            latest_file
                            and latest_file.stat().st_mtime <= cached["timestamp"]
                        ):
                            should_process = False

                if not should_process and cached and "processed_content" in cached:
                    logger.debug(f"Using cached version of {bookmark_dir.name}")
                    bookmark_result.add_from_cache(self._processor_type)
                    bookmark_result.processed += (
                        1  # Increment processed count for cached content
                    )

                    # Write cached content
                    output_file = (
                        self.source_config.dest_dir / f"{bookmark_dir.name}.md"
                    )
                    output_file.write_text(
                        cached["processed_content"], encoding="utf-8"
                    )

                    result.merge(bookmark_result)
                    continue

                # Process bookmark
                logger.debug(f"Processing {bookmark_dir}")

                # Process media files in the content
                content = self._process_media_references(
                    content,
                    bookmark_dir,
                    self.attachment_processor,
                    config,
                    bookmark_result,
                )

                # Process media files in the media directory
                media_content = self._process_media(
                    bookmark_dir,
                    config,
                    bookmark_result,
                )
                if media_content:
                    content += "\n\n" + media_content

                # Process non-media attachments
                attachment_content = self._process_attachments(
                    content,
                    bookmark_dir,
                    self.attachment_processor,
                    config,
                    bookmark_result,
                )
                if attachment_content:
                    content += "\n\n" + attachment_content

                # Add to stats
                if config.global_config.force_generation or not cached:
                    bookmark_result.add_generated(self._processor_type)
                else:
                    bookmark_result.add_from_cache(self._processor_type)
                bookmark_result.processed += (
                    1  # Increment processed count for newly generated content
                )

                # Write processed bookmark
                output_file = self.source_config.dest_dir / f"{bookmark_dir.name}.md"
                output_file.write_text(content, encoding="utf-8")

                # Update cache
                self.cache_manager.update_note_cache(
                    str(index_file),
                    content_hash,
                    index_file.stat().st_mtime,
                    processed_content=content,
                )

                result.merge(bookmark_result)
                logger.info(
                    f"Successfully processed: {bookmark_dir.name} "
                    f"({bookmark_result.images_processed} images, "
                    f"{bookmark_result.documents_processed} documents)"
                )

            except Exception as e:
                error_msg = f"Error processing {bookmark_dir.name}: {str(e)}"
                logger.error(error_msg)
                result.add_error(error_msg, self._processor_type)

        logger.info(
            f"Completed X bookmarks source: {result.processed} processed "
            f"[{result.from_cache} from cache, {result.regenerated} regenerated], "
            f"{result.skipped} skipped"
        )

        return result

    def _process_media_references(
        self,
        content: str,
        bookmark_dir: Path,
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult,
    ) -> str:
        """Process media references in content.

        Args:
            content: The current content of the bookmark
            bookmark_dir: The directory containing the bookmark files
            attachment_processor: The processor for handling attachments
            config: The application configuration
            result: The processing result object to update

        Returns:
            Updated content with processed media references
        """
        import re
        import urllib.parse
        from typing import Match

        def replace_media(match: Match[str]) -> str:
            """Replace a media reference with processed content."""
            alt_text, path = match.groups()

            # URL decode the path
            decoded_path = urllib.parse.unquote(path)

            # Handle relative paths
            if not Path(decoded_path).is_absolute():
                media_path = bookmark_dir / decoded_path
            else:
                # For absolute paths, just use the filename
                media_path = Path(decoded_path)

            if not media_path.exists():
                logger.warning(f"Media file not found: {media_path}")
                return match.group(0)

            logger.info(f"Processing media reference: {media_path}")

            # Process the attachment using the base class method
            markdown_result = self._process_attachment(
                media_path,
                self.source_config.dest_dir,  # This is no longer used for file operations
                attachment_processor,
                config,
                result,
                alt_text=alt_text,
                is_image=True,
            )

            # Handle the Optional[str] return type
            if markdown_result is None:
                return match.group(0)

            logger.info(
                f"Generated markdown for {media_path.name}: {markdown_result[:200]}"
            )
            return markdown_result

        # Replace image references
        result_content = re.sub(r"!\[(.*?)\]\((.*?)\)", replace_media, content)
        return result_content

    def _process_media(
        self,
        bookmark_dir: Path,
        config: Config,
        result: ProcessingResult,
    ) -> str:
        """Process media files in the bookmark directory.

        Args:
            bookmark_dir: The directory containing the bookmark files
            config: The application configuration
            result: The processing result object to update

        Returns:
            Formatted markdown content for all media files
        """
        media_dir = bookmark_dir / "media"
        if not media_dir.exists() or not media_dir.is_dir():
            logger.debug(f"No media directory found in {bookmark_dir}")
            return ""

        # No longer creating output media directory

        # Get all image files
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".heic"}
        media_files = [
            f
            for f in media_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]

        if not media_files:
            logger.debug(f"No media files found in {media_dir}")
            return ""

        logger.info(f"Processing {len(media_files)} media files from {media_dir}")

        # Process all media files and collect their markdown representations
        return self._process_attachment_files(
            media_files, self.source_config.dest_dir, config, result, is_image=True
        )

    def _process_attachments(
        self,
        content: str,
        bookmark_dir: Path,
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult,
    ) -> str:
        """Process non-media attachments in the bookmark directory.

        Args:
            content: The current content of the bookmark
            bookmark_dir: The directory containing the bookmark files
            attachment_processor: The processor for handling attachments
            config: The application configuration
            result: The processing result object to update

        Returns:
            Formatted markdown content for all non-media attachments
        """
        # Skip media files and markdown files
        skip_exts = {".md", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".heic"}
        attachments = [
            f
            for f in bookmark_dir.iterdir()
            if f.is_file() and f.suffix.lower() not in skip_exts
        ]

        if not attachments:
            logger.debug(f"No attachments found in {bookmark_dir}")
            return ""

        logger.info(f"Processing {len(attachments)} attachments from {bookmark_dir}")

        # No longer creating output attachments directory

        # Process all attachment files and collect their markdown representations
        return self._process_attachment_files(
            attachments, self.source_config.dest_dir, config, result, is_image=False
        )

    def _process_attachment_files(
        self,
        files: list[Path],
        output_dir: Path,
        config: Config,
        result: ProcessingResult,
        is_image: bool = True,
    ) -> str:
        """Process a list of attachment files and return their markdown representation.

        Args:
            files: List of file paths to process
            output_dir: Directory to save processed files
            config: The application configuration
            result: The processing result object to update
            is_image: Whether the files are images (True) or documents (False)

        Returns:
            Formatted markdown content for all processed files
        """
        content = ""

        for file_path in files:
            try:
                # Use the _process_attachment method from AttachmentHandlerMixin
                formatted_content = self._process_attachment(
                    file_path,
                    output_dir,
                    self.attachment_processor,
                    config,
                    result,
                    is_image=is_image,
                    progress=self._progress,
                    task_id=self._task_id,
                )

                if formatted_content:
                    content += formatted_content + "\n\n"
                    logger.debug(f"Successfully processed {file_path.name}")
                else:
                    logger.warning(f"No content generated for {file_path.name}")

            except Exception as e:
                error_msg = f"Error processing {'image' if is_image else 'document'} {file_path}: {str(e)}"
                logger.error(error_msg)
                result.add_error(error_msg, self._processor_type)
                if is_image:
                    result.add_image_skipped(self._processor_type)
                else:
                    result.add_document_skipped(self._processor_type)

        return content.strip()
