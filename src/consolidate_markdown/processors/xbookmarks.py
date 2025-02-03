"""Process X bookmarks."""

import logging
import shutil
from pathlib import Path

from ..attachments.processor import AttachmentProcessor
from ..cache import CacheManager, quick_hash
from ..config import Config, SourceConfig
from .base import ProcessingResult, SourceProcessor

logger = logging.getLogger(__name__)


class XBookmarksProcessor(SourceProcessor):
    """Process X bookmarks and their attachments."""

    def __init__(self, source_config: SourceConfig):
        """Initialize processor."""
        super().__init__(source_config)
        self.validate()  # Call validate to ensure source directory exists
        self.cache_manager = CacheManager(source_config.dest_dir.parent)

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
                    # Special case: don't count 'images' directory in skip count
                    if bookmark_dir.name != "images":
                        logger.warning(f"No index file found in {bookmark_dir.name}")
                        result.add_skipped(self._processor_type)
                    else:
                        logger.debug(
                            f"Skipping special images directory: {bookmark_dir.name}"
                        )
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

                # Create output media directory
                output_media_dir = self.source_config.dest_dir / "media"
                output_media_dir.mkdir(exist_ok=True)

                # Process media files
                media_content = self._process_media(
                    bookmark_dir,
                    self.attachment_processor,
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

    def _process_media(
        self,
        bookmark_dir: Path,
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult,
    ) -> str:
        """Process media files in the bookmark directory."""
        content = ""
        media_dir = bookmark_dir / "media"
        if not media_dir.exists() or not media_dir.is_dir():
            return content

        # Create output media directory
        output_media_dir = self.source_config.dest_dir / "media"
        output_media_dir.mkdir(exist_ok=True)

        # Process each media file
        media_files = [
            f
            for f in media_dir.iterdir()
            if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif"}
        ]

        media_content = ""
        for media_file in media_files:
            try:
                temp_path, metadata = attachment_processor.process_file(
                    media_file,
                    force=config.global_config.force_generation,
                    result=result,
                )

                # Copy processed file to output directory
                output_path = output_media_dir / media_file.name
                shutil.copy2(temp_path, output_path)

                if metadata.is_image:
                    if config.global_config.force_generation:
                        result.add_image_generated(self._processor_type)
                    else:
                        result.add_image_from_cache(self._processor_type)

                    size_kb = metadata.size_bytes / 1024
                    dimensions = metadata.dimensions or (0, 0)

                    media_content += f"""
<!-- EMBEDDED IMAGE: {media_file.name} -->
<details>
<summary>🖼️ {media_file.name} ({dimensions[0]}x{dimensions[1]}, {size_kb:.0f}KB)</summary>

[Image will be analyzed in Phase 4]

</details>
"""

            except Exception as e:
                logger.error(f"Error processing media file {media_file}: {str(e)}")
                result.add_image_skipped(self._processor_type)

        return content + media_content if media_content else content

    def _process_attachments(
        self,
        content: str,
        bookmark_dir: Path,
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult,
    ) -> str:
        """Process non-media attachments in the bookmark directory."""
        # Find all non-media files (excluding index and media files)
        skip_exts = {".md", ".jpg", ".jpeg", ".png", ".gif", ".svg"}
        attachments = [
            f
            for f in bookmark_dir.iterdir()
            if f.is_file() and f.suffix.lower() not in skip_exts
        ]

        # Process each attachment
        attachment_content = ""
        for attachment in attachments:
            try:
                temp_path, metadata = attachment_processor.process_file(
                    attachment,
                    force=config.global_config.force_generation,
                    result=result,
                )

                if not metadata.is_image:
                    if config.global_config.force_generation:
                        result.add_document_generated(self._processor_type)
                    else:
                        result.add_document_from_cache(self._processor_type)

                    size_kb = metadata.size_bytes / 1024
                    doc_content = (
                        metadata.markdown_content
                        or "[Document content will be converted in Phase 4]"
                    )

                    attachment_content += f"""

<!-- EMBEDDED DOCUMENT: {attachment.name} -->
<details>
<summary>📄 {attachment.name} ({size_kb:.0f}KB)</summary>

{doc_content}

</details>
"""

            except Exception as e:
                logger.error(f"Error processing attachment {attachment}: {str(e)}")
                result.add_document_skipped(self._processor_type)

        return content + attachment_content if attachment_content else content
