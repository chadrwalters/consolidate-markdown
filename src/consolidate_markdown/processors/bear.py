"""Process Bear notes."""

import logging
import re
import urllib.parse
from pathlib import Path

from ..attachments.processor import AttachmentProcessor
from ..cache import CacheManager, quick_hash
from ..config import Config, SourceConfig
from .base import ProcessingResult, SourceProcessor

logger = logging.getLogger(__name__)


class BearProcessor(SourceProcessor):
    """Process Bear notes and their attachments."""

    def __init__(self, source_config: SourceConfig):
        """Initialize processor."""
        super().__init__(source_config)
        self.validate()  # Call validate to ensure source directory exists
        self.cache_manager = CacheManager(source_config.dest_dir.parent)

    def _process_impl(self, config: Config) -> ProcessingResult:
        """Process all Bear notes in the source directory."""
        result = ProcessingResult()

        # Clear cache if force flag is set
        if config.global_config.force_generation:
            self.cache_manager.clear_cache()

        # Ensure output directory exists
        self._ensure_dest_dir()

        # Get all markdown files and apply limit if set
        note_files = list(self.source_config.src_dir.glob("*.md"))
        note_files = self._apply_limit(note_files)

        # Process each markdown file
        for note_file in note_files:
            try:
                logger.info(f"Processing Bear note: {note_file.name}")
                note_result = ProcessingResult()  # Track stats for this note
                self.process_note(note_file, config, note_result)
                result.merge(note_result)  # Merge note stats into overall stats
                logger.info(
                    f"Successfully processed: {note_file.name} "
                    f"({note_result.images_processed} images, "
                    f"{note_result.documents_processed} documents)"
                )

            except Exception as e:
                error_msg = f"Error processing {note_file.name}: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        logger.info(
            f"Completed bear source: {result.processed} processed "
            f"[{result.from_cache} from cache, {result.regenerated} regenerated], "
            f"{result.skipped} skipped"
        )

        return result

    def _process_attachments(
        self,
        content: str,
        attachment_dir: Path,
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult,
    ) -> str:
        """Process attachments in content."""
        # Create output attachments directory
        output_attachments_dir = self.source_config.dest_dir / "attachments"
        output_attachments_dir.mkdir(exist_ok=True)

        def replace_attachment(match: re.Match, is_image: bool = True) -> str:
            alt_text, path = match.groups()
            # URL decode the path
            decoded_path = urllib.parse.unquote(path)
            attachment_path = attachment_dir / Path(decoded_path).name

            # Skip .DS_Store files
            if attachment_path.name == ".DS_Store":
                return match.group(0)

            if not attachment_path.exists():
                logger.warning(f"Attachment not found: {attachment_path}")
                return match.group(0)

            # Process the attachment using the base class method
            markdown = self._process_attachment(
                attachment_path,
                output_attachments_dir,
                attachment_processor,
                config,
                result,
                alt_text=alt_text,
                is_image=is_image,
            )
            return markdown if markdown else match.group(0)

        # Process images and embedded documents
        image_pattern = r"!\[(.*?)\]\((.*?)\)"
        embed_pattern = r'\[(.*?)\]\((.*?)\)<!-- *{"embed":"true".*?} *-->'
        content = re.sub(image_pattern, replace_attachment, content)
        content = re.sub(embed_pattern, lambda m: replace_attachment(m, False), content)

        return content

    def process_note(
        self, note_file: Path, config: Config, result: ProcessingResult
    ) -> None:
        """Process a single Bear note."""
        note_path = str(note_file.resolve()).replace("\n", "")
        logger.debug(f"Processing Bear note: {note_path}")

        # Check if we can use cached version
        cached = self.cache_manager.get_note_cache(note_path)
        content_hash = quick_hash(note_file.read_text())

        if (
            cached is not None
            and cached["hash"] == content_hash
            and not config.global_config.force_generation
        ):
            logger.debug(f"Using cached version of {note_file.name}")
            result.from_cache += 1
            result.processed += 1

            # Track cached documents and images
            if "documents" in cached:
                result.documents_from_cache += len(cached["documents"])
                result.documents_processed += len(cached["documents"])
            if "images" in cached:
                result.images_from_cache += len(cached["images"])
                result.images_processed += len(cached["images"])
            if "gpt_analyses" in cached:
                result.gpt_cache_hits += cached["gpt_analyses"]

            # Use cached processed content if available
            if "processed_content" in cached:
                output_file = self.source_config.dest_dir / note_file.name
                output_file.write_text(cached["processed_content"], encoding="utf-8")
                return

        # Process the note from scratch
        logger.debug(f"Processing {note_file.name} from scratch")
        result.regenerated += 1
        result.processed += 1

        # Process note content and attachments
        note_content = note_file.read_text()
        processed_content = self._process_attachments(
            note_content,
            note_file.parent / note_file.stem,
            self.attachment_processor,
            config,
            result,
        )

        # Write processed content
        output_file = self.source_config.dest_dir / note_file.name
        output_file.write_text(processed_content, encoding="utf-8")

        # Update cache with new content
        self.cache_manager.update_note_cache(
            note_path,
            content_hash,
            0.0,  # Ignore timestamps for Bear notes
            gpt_analyses=result.gpt_new_analyses,
            processed_content=processed_content,
        )
