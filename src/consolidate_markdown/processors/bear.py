"""Process Bear notes."""
import logging
import re
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..attachments.processor import AttachmentProcessor, AttachmentMetadata
from ..attachments.gpt import GPTProcessor, GPTError
from ..config import Config
from .base import ProcessingResult, SourceProcessor

logger = logging.getLogger(__name__)

class BearProcessor(SourceProcessor):
    """Process Bear notes and their attachments."""

    def process(self, config: Config) -> ProcessingResult:
        """Process all Bear notes in the source directory."""
        result = ProcessingResult()
        attachment_processor = AttachmentProcessor(config.global_config.cm_dir)

        try:
            # Ensure output directory exists
            self._ensure_dest_dir()

            # Process each markdown file
            for note_file in self.source_config.src_dir.glob("*.md"):
                try:
                    logger.info(f"Processing Bear note: {note_file.name}")
                    note_result = ProcessingResult()  # Track stats for this note

                    # Check for attachment folder
                    attachment_dir = self.source_config.src_dir / note_file.stem
                    has_attachments = attachment_dir.is_dir()

                    # Read note content
                    content = note_file.read_text(encoding='utf-8')

                    # Process attachments if they exist
                    if has_attachments:
                        content = self._process_attachments(
                            content,
                            attachment_dir,
                            attachment_processor,
                            config,
                            note_result
                        )

                    # Write processed note
                    output_file = self.source_config.dest_dir / note_file.name
                    output_file.write_text(content, encoding='utf-8')

                    result.merge(note_result)  # Merge note stats into overall stats
                    result.processed += 1
                    logger.info(f"Successfully processed: {note_file.name} ({note_result.images_processed} images, {note_result.documents_processed} documents)")

                except Exception as e:
                    error_msg = f"Error processing {note_file.name}: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

            logger.info(f"Completed bear source: {result.processed} processed, {result.skipped} skipped")

        finally:
            attachment_processor.cleanup()

        return result

    def _process_attachments(self, content: str, attachment_dir: Path,
                           attachment_processor: AttachmentProcessor,
                           config: Config,
                           result: ProcessingResult) -> str:
        """Process attachments and update note content."""
        # Find all attachment references
        image_pattern = r'!\[(.*?)\]\((.*?)\)'
        embed_pattern = r'\[(.*?)\]\((.*?)\)<!-- *{"embed":"true".*?} *-->'

        def replace_attachment(match: re.Match, is_image: bool = True) -> str:
            alt_text, path = match.groups()
            # URL decode the path
            decoded_path = urllib.parse.unquote(path)
            attachment_path = attachment_dir / Path(decoded_path).name

            # Skip .DS_Store files
            if attachment_path.name == '.DS_Store':
                return match.group(0)

            if not attachment_path.exists():
                logger.warning(f"Attachment not found: {attachment_path}")
                return match.group(0)

            try:
                temp_path, metadata = attachment_processor.process_file(
                    attachment_path,
                    force=config.global_config.force_generation,
                    result=result
                )

                if is_image and metadata.is_image:
                    result.images_processed += 1  # Only increment for image references
                    return self._format_image(
                        attachment_path,
                        metadata,
                        config,
                        result
                    )
                elif not is_image and not metadata.is_image:
                    result.documents_processed += 1  # Only increment for document references
                    return self._format_document_attachment(
                        alt_text,
                        attachment_path,
                        metadata,
                        result
                    )
                else:
                    # Mismatch between reference type and actual file type
                    logger.warning(f"Attachment type mismatch for {attachment_path}")
                    if is_image:
                        result.images_skipped += 1
                    return match.group(0)

            except Exception as e:
                logger.error(f"Error processing attachment {attachment_path}: {str(e)}")
                if is_image:
                    result.images_skipped += 1
                return match.group(0)

        # Process images and embedded documents
        content = re.sub(image_pattern, lambda m: replace_attachment(m, True), content)
        content = re.sub(embed_pattern, lambda m: replace_attachment(m, False), content)

        return content

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

        result.images_processed += 1  # Increment counter when image is successfully formatted

        return f"""
<!-- EMBEDDED IMAGE: {image_path.name} -->
<details>
<summary>🖼️ {image_path.name} ({dimensions[0]}x{dimensions[1]}, {size_kb:.0f}KB)</summary>

{description}

</details>
"""

    def _format_document_attachment(
        self,
        alt_text: str,
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
