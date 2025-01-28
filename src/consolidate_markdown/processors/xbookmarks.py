"""Process X bookmarks."""

import logging
import shutil
from pathlib import Path

from ..attachments.processor import AttachmentProcessor
from ..cache import CacheManager, quick_hash
from ..config import Config
from .base import ProcessingResult, SourceProcessor

logger = logging.getLogger(__name__)


class XBookmarksProcessor(SourceProcessor):
    """Process X bookmarks and their attachments."""

    def __init__(self, source_config):
        """Initialize processor."""
        super().__init__(source_config)
        self.validate()  # Call validate to ensure source directory exists
        self.cache_manager = CacheManager(source_config.dest_dir.parent)
        self.attachment_processor = AttachmentProcessor(source_config.dest_dir.parent)

    def process(self, config: Config) -> ProcessingResult:
        """Process all X bookmarks in the source directory."""
        result = ProcessingResult()

        # Clear cache if force flag is set
        if config.global_config.force_generation:
            self.cache_manager.clear_cache()

        try:
            # Ensure output directory exists
            self._ensure_dest_dir()

            # Process each bookmark directory
            for bookmark_dir in self.source_config.src_dir.iterdir():
                if not bookmark_dir.is_dir():
                    continue

                try:
                    logger.info(f"Processing X bookmark: {bookmark_dir.name}")
                    bookmark_result = ProcessingResult()

                    # Look for index file
                    index_file = bookmark_dir / self.source_config.index_filename
                    if not index_file.exists():
                        logger.warning(f"No index file found in {bookmark_dir.name}")
                        result.skipped += 1
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
                        bookmark_result.add_from_cache()

                        # Write cached content
                        output_file = (
                            self.source_config.dest_dir / f"{bookmark_dir.name}.md"
                        )
                        output_file.write_text(
                            cached["processed_content"], encoding="utf-8"
                        )

                        result.merge(bookmark_result)
                        continue

                    # If cache is valid and we're not forcing regeneration, use it
                    if not config.global_config.force_generation and cached:
                        logger.debug(f"Using cached content for {bookmark_dir}")
                        bookmark_result.add_from_cache()
                        processed_content = cached["processed_content"]
                    else:
                        # Process bookmark
                        logger.debug(f"Processing {bookmark_dir}")
                        # Process media files
                        media_content = self._process_media(
                            bookmark_dir,
                            self.attachment_processor,
                            config,
                            bookmark_result,
                        )

                        if media_content:
                            content += "\n\n" + media_content

                        # Process any embedded attachments
                        processed_content = self._process_attachments(
                            content,
                            bookmark_dir,
                            self.attachment_processor,
                            config,
                            bookmark_result,
                        )

                        if not processed_content:
                            logger.warning(
                                f"Attachment processing returned empty content for {bookmark_dir.name}"
                            )
                            processed_content = content

                        bookmark_result.add_generated()

                    # Write processed bookmark
                    output_file = (
                        self.source_config.dest_dir / f"{bookmark_dir.name}.md"
                    )
                    output_file.write_text(processed_content, encoding="utf-8")

                    # Update cache
                    self.cache_manager.update_note_cache(
                        str(index_file),
                        content_hash,
                        index_file.stat().st_mtime,
                        processed_content=processed_content,
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
                    result.errors.append(error_msg)

            logger.info(
                f"Completed X bookmarks source: {result.processed} processed "
                f"[{result.from_cache} from cache, {result.regenerated} regenerated], "
                f"{result.skipped} skipped"
            )

        finally:
            self.attachment_processor.cleanup()

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
                    result.images_processed += 1
                    if config.global_config.force_generation:
                        result.images_generated += 1

                    size_kb = metadata.size_bytes / 1024
                    dimensions = metadata.dimensions or (0, 0)

                    content += f"""
<!-- EMBEDDED IMAGE: {media_file.name} -->
<details>
<summary>🖼️ {media_file.name} ({dimensions[0]}x{dimensions[1]}, {size_kb:.0f}KB)</summary>

[Image will be analyzed in Phase 4]

</details>
"""

            except Exception as e:
                logger.error(f"Error processing media file {media_file}: {str(e)}")

        return content

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
        skip_exts = {".md", ".jpg", ".jpeg", ".png", ".gif"}
        attachments = [
            f
            for f in bookmark_dir.iterdir()
            if f.is_file() and f.suffix.lower() not in skip_exts
        ]

        # Process each attachment
        for attachment in attachments:
            try:
                temp_path, metadata = attachment_processor.process_file(
                    attachment,
                    force=config.global_config.force_generation,
                    result=result,
                )

                if not metadata.is_image:
                    result.documents_processed += 1
                    if config.global_config.force_generation:
                        result.documents_generated += 1
                    size_kb = metadata.size_bytes / 1024
                    doc_content = (
                        metadata.markdown_content
                        or "[Document content will be converted in Phase 4]"
                    )

                    content += f"""

<!-- EMBEDDED DOCUMENT: {attachment.name} -->
<details>
<summary>📄 {attachment.name} ({size_kb:.0f}KB)</summary>

{doc_content}

</details>
"""

            except Exception as e:
                logger.error(f"Error processing attachment {attachment}: {str(e)}")

        return content
