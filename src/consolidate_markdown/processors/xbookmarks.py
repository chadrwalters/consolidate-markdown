"""Process X bookmarks."""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import urllib.parse

from ..attachments.processor import AttachmentProcessor, AttachmentMetadata
from ..attachments.gpt import GPTProcessor, GPTError
from ..config import Config
from .base import ProcessingResult, SourceProcessor

logger = logging.getLogger(__name__)

class XBookmarksProcessor(SourceProcessor):
    """Process X (Twitter) bookmarks and their attachments."""

    def process(self, config: Config) -> ProcessingResult:
        """Process all X bookmarks in the source directory."""
        result = ProcessingResult()
        attachment_processor = AttachmentProcessor(config.global_config.cm_dir)

        try:
            # Ensure output directory exists
            self._ensure_dest_dir()

            # Process each bookmark directory
            for bookmark_dir in self.source_config.src_dir.iterdir():
                if not bookmark_dir.is_dir():
                    continue

                try:
                    logger.info(f"Processing X bookmark: {bookmark_dir.name}")
                    bookmark_result = ProcessingResult()  # Track stats for this bookmark

                    # Check for index file
                    index_file = bookmark_dir / self.source_config.index_filename
                    if not index_file.exists():
                        logger.warning(f"Missing index file in {bookmark_dir.name}")
                        result.skipped += 1
                        continue

                    try:
                        # Read index content
                        content = index_file.read_text(encoding='utf-8')
                    except Exception as e:
                        logger.error(f"Failed to read index file in {bookmark_dir.name}: {str(e)}")
                        result.skipped += 1
                        continue

                    if not content:
                        logger.warning(f"Empty index file in {bookmark_dir.name}")
                        result.skipped += 1
                        continue

                    # Process media files
                    content = self._process_media(
                        content,
                        bookmark_dir,
                        attachment_processor,
                        config,
                        bookmark_result
                    )

                    if not content:  # Changed from content is None
                        logger.warning(f"Media processing returned empty content for {bookmark_dir.name}")
                        content = ""  # Use empty string but don't skip - we may have processed media

                    # Process any embedded attachments
                    processed_content = self._process_attachments(
                        content,
                        bookmark_dir,
                        attachment_processor,
                        config,
                        bookmark_result
                    )

                    if not processed_content:  # Changed from content is None
                        logger.warning(f"Attachment processing returned empty content for {bookmark_dir.name}")
                        processed_content = content  # Keep original content with any processed media

                    # Write processed bookmark
                    output_file = self.source_config.dest_dir / f"{bookmark_dir.name}.md"
                    output_file.write_text(processed_content or content, encoding='utf-8')  # Use original if processed is empty

                    result.merge(bookmark_result)  # Merge bookmark stats into overall stats
                    result.processed += 1
                    logger.info(f"Successfully processed: {bookmark_dir.name} ({bookmark_result.images_processed} images, {bookmark_result.documents_processed} documents)")

                except Exception as e:
                    error_msg = f"Error processing {bookmark_dir.name}: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

            logger.info(f"Completed xbookmarks source: {result.processed} processed, {result.skipped} skipped")

        finally:
            attachment_processor.cleanup()

        return result

    def _process_media(
        self,
        content: str,
        bookmark_dir: Path,
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult
    ) -> str:
        """Process media files in the bookmark directory."""
        if content is None:  # Handle None content
            logger.warning(f"No content found in {bookmark_dir.name}")
            return ""

        processed_content = []
        processed_content.append(content.strip())

        # Process media files in media directory
        media_dir = bookmark_dir / "media"
        if media_dir.exists() and media_dir.is_dir():
            for media_file in media_dir.iterdir():
                if media_file.is_file() and media_file.name != '.DS_Store':
                    try:
                        temp_path, metadata = attachment_processor.process_file(
                            media_file,
                            force=config.global_config.force_generation,
                            result=result
                        )
                        if metadata.is_image:
                            result.images_processed += 1
                            processed_content.append(self._format_image(
                                media_file,
                                metadata,
                                config,
                                result
                            ))
                        else:
                            result.documents_processed += 1
                            processed_content.append(self._format_document(
                                media_file,
                                metadata,
                                result
                            ))
                    except Exception as e:
                        error_msg = f"Error processing media file {media_file.name}: {str(e)}"
                        logger.error(error_msg)
                        result.add_error(error_msg)
                        result.images_skipped += 1
                        # Don't return None, keep processing other files

        # Also check root directory for media files
        for pattern in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.heic', '*.svg']:
            for media_file in bookmark_dir.glob(pattern):
                if (media_file.is_file() and
                    media_file.name != '.DS_Store' and
                    media_file.parent.name != 'media'):  # Skip files in media dir
                    try:
                        temp_path, metadata = attachment_processor.process_file(
                            media_file,
                            force=config.global_config.force_generation,
                            result=result
                        )
                        if metadata.is_image:
                            result.images_processed += 1
                            processed_content.append(self._format_image(
                                media_file,
                                metadata,
                                config,
                                result
                            ))
                        else:
                            result.documents_processed += 1
                            processed_content.append(self._format_document(
                                media_file,
                                metadata,
                                result
                            ))
                    except Exception as e:
                        error_msg = f"Error processing media file {media_file.name}: {str(e)}"
                        logger.error(error_msg)
                        result.add_error(error_msg)
                        result.images_skipped += 1
                        # Don't return None, keep processing other files

        return "\n\n".join(processed_content) if processed_content else ""

    def _format_image(
        self,
        image_path: Path,
        metadata: 'AttachmentMetadata',
        config: Config,
        result: ProcessingResult
    ) -> str:
        """Format an image with optional GPT description."""
        size_kb = metadata.size_bytes / 1024
        dimensions = metadata.dimensions or (0, 0)

        # Get image description if enabled
        description = ""
        if not config.global_config.no_image:
            try:
                gpt = GPTProcessor(config.global_config.openai_key)
                description = gpt.describe_image(image_path, result)
            except Exception as e:
                logger.error(f"GPT processing failed for {image_path}: {str(e)}")
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
        metadata: 'AttachmentMetadata',
        result: ProcessingResult
    ) -> str:
        """Format a document attachment."""
        size_kb = metadata.size_bytes / 1024
        content = metadata.markdown_content or "[Document content will be converted in Phase 4]"
        result.documents_processed += 1

        return f"""
<!-- EMBEDDED DOCUMENT: {doc_path.name} -->
<details>
<summary>📄 {doc_path.name} ({size_kb:.0f}KB)</summary>

{content}

</details>
"""

    def _process_attachments(
        self,
        content: str,
        bookmark_dir: Path,
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult
    ) -> str:
        """Process attachments and update note content."""
        if not content:  # Handle empty content
            return ""

        # Find all attachment references
        image_pattern = r'!\[(.*?)\]\((.*?)\)'
        embed_pattern = r'\[(.*?)\]\((.*?)\)<!-- *{"embed":"true".*?} *-->'

        def replace_attachment(match: re.Match, is_image: bool = True) -> str:
            alt_text, path = match.groups()
            # URL decode the path
            decoded_path = urllib.parse.unquote(path)
            filename = Path(decoded_path).name

            # Try different possible locations for the attachment
            possible_paths = [
                bookmark_dir / "media" / filename,  # media subdirectory
                bookmark_dir / filename,  # root directory
                bookmark_dir / decoded_path,  # full path from markdown
            ]

            # Find first existing path
            attachment_path = None
            for p in possible_paths:
                if p.exists() and p.is_file() and p.name != '.DS_Store':
                    attachment_path = p
                    break

            if not attachment_path:
                logger.warning(f"Attachment not found, tried: {[str(p) for p in possible_paths]}")
                result.images_skipped += 1  # Count missing attachments as skipped
                return match.group(0)

            try:
                temp_path, metadata = attachment_processor.process_file(
                    attachment_path,
                    force=config.global_config.force_generation,
                    result=result
                )

                if metadata.is_image:
                    result.images_processed += 1
                    return self._format_image(
                        attachment_path,
                        metadata,
                        config,
                        result
                    )
                else:
                    result.documents_processed += 1
                    return self._format_document(
                        attachment_path,
                        metadata,
                        result
                    )

            except Exception as e:
                logger.error(f"Error processing attachment {attachment_path}: {str(e)}")
                result.images_skipped += 1  # Count failed attachments as skipped
                return match.group(0)

        # Process image references first
        content = re.sub(image_pattern, lambda m: replace_attachment(m, True), content)

        # Then process embedded attachments
        content = re.sub(embed_pattern, lambda m: replace_attachment(m, False), content)

        return content
