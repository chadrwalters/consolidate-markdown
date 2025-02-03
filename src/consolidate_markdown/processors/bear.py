"""Process Bear notes."""

import logging
import re
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple

from rich.progress import Progress, TaskID

from ..attachments.processor import AttachmentProcessor
from ..cache import CacheManager, quick_hash
from ..config import Config, SourceConfig
from .base import SourceProcessor
from .result import ProcessingResult

logger = logging.getLogger(__name__)


class BearProcessor(SourceProcessor):
    """Process Bear notes and their attachments."""

    def __init__(self, source_config: SourceConfig):
        """Initialize processor."""
        super().__init__(source_config)
        self.validate()  # Call validate to ensure source directory exists
        self.cache_manager = CacheManager(source_config.dest_dir.parent)

    def _count_attachments(self, content: str, attachment_dir: Path) -> Tuple[int, int]:
        """Count images and documents in content.

        Returns:
            Tuple of (image_count, document_count)
        """
        image_count = 0
        doc_count = 0

        # Count images
        image_pattern = r"!\[(.*?)\]\((.*?)\)"
        for match in re.finditer(image_pattern, content):
            _, path = match.groups()
            decoded_path = urllib.parse.unquote(path)
            attachment_path = attachment_dir / Path(decoded_path).name
            if attachment_path.exists() and attachment_path.name != ".DS_Store":
                image_count += 1

        # Count embedded documents
        embed_pattern = r'\[(.*?)\]\((.*?)\)<!-- *{"embed":"true".*?} *-->'
        for match in re.finditer(embed_pattern, content):
            _, path = match.groups()
            decoded_path = urllib.parse.unquote(path)
            attachment_path = attachment_dir / Path(decoded_path).name
            if attachment_path.exists() and attachment_path.name != ".DS_Store":
                doc_count += 1

        return image_count, doc_count

    def _process_impl(self, config: Config) -> ProcessingResult:
        """Process all Bear notes in the source directory."""
        result = ProcessingResult()

        # Clear cache if force flag is set
        if config.global_config.force_generation:
            self.cache_manager.clear_cache()

        self._ensure_dest_dir()

        # Get all markdown files and apply limit if set
        note_files = list(self.source_config.src_dir.glob("*.md"))
        note_files = self._apply_limit(note_files)

        # Create progress tracking for notes
        if self._progress:
            note_task = self._progress.add_task(
                f"[cyan]Processing {len(note_files)} Bear notes...",
                total=len(note_files),
            )

        # Process each markdown file
        for note_file in note_files:
            try:
                logger.info(f"Processing Bear note: {note_file.name}")
                note_result = ProcessingResult()  # Track stats for this note

                # Count attachments for progress tracking
                content = note_file.read_text()
                img_count, doc_count = self._count_attachments(
                    content, note_file.parent / note_file.stem
                )

                # Create attachment progress if needed
                attachment_task = None
                if self._progress and (img_count + doc_count) > 0:
                    attachment_task = self._progress.add_task(
                        f"[blue]Processing {img_count + doc_count} attachments in {note_file.name}...",
                        total=img_count + doc_count,
                    )

                # Process the note
                self.process_note(
                    note_file,
                    config,
                    note_result,
                    self._progress if attachment_task else None,
                    attachment_task,
                )

                result.merge(note_result)  # Merge note stats into overall stats
                logger.info(
                    f"Successfully processed: {note_file.name} "
                    f"({note_result.images_processed} images, "
                    f"{note_result.documents_processed} documents)"
                )

                # Update note progress
                if self._progress:
                    self._progress.update(note_task, advance=1)

            except Exception as e:
                error_msg = f"Error processing {note_file.name}: {str(e)}"
                logger.error(error_msg)
                result.add_error(error_msg, self._processor_type)
                if self._progress:
                    self._progress.update(note_task, advance=1)

        logger.info(
            f"Completed bear source: {result.processed} processed "
            f"[{result.from_cache} from cache, {result.regenerated} regenerated], "
            f"{result.skipped} skipped"
        )

        return result

    def process_note(
        self,
        note_file: Path,
        config: Config,
        result: ProcessingResult,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None,
    ) -> None:
        """Process a single Bear note.

        Args:
            note_file: Path to the note file
            config: The configuration to use
            result: The processing result to update
            progress: Optional progress tracker
            task_id: Optional task ID for progress
        """
        # Check if we need to process this note
        content = note_file.read_text()
        content_hash = quick_hash(content)
        cached = self.cache_manager.get_note_cache(str(note_file))

        should_process = True
        if cached and not config.global_config.force_generation:
            if cached["hash"] == content_hash:
                # Check for any newer files in the note directory
                attachment_dir = note_file.parent / note_file.stem
                if attachment_dir.exists():
                    latest_file = max(
                        attachment_dir.glob("*"),
                        key=lambda p: p.stat().st_mtime if p.is_file() else 0,
                        default=None,
                    )
                    if (
                        latest_file
                        and latest_file.stat().st_mtime <= cached["timestamp"]
                    ):
                        should_process = False
                else:
                    # No attachments directory = safe to use cache
                    should_process = False

        if not should_process and cached and "processed_content" in cached:
            logger.debug(f"Using cached version of {note_file.name}")
            result.add_from_cache(self._processor_type)
            result.processed += 1  # Increment processed count for cached content

            # Write cached content
            output_file = self.source_config.dest_dir / note_file.name
            output_file.write_text(cached["processed_content"], encoding="utf-8")
            return

        # Process note from scratch
        logger.debug(f"Processing {note_file.name} from scratch")

        # Process attachments
        attachment_dir = note_file.parent / note_file.stem
        if attachment_dir.exists():
            content = self._process_attachments(
                content,
                attachment_dir,
                self.attachment_processor,
                config,
                result,
                progress,
                task_id,
            )

        # Write processed note
        output_file = self.source_config.dest_dir / note_file.name
        output_file.write_text(content, encoding="utf-8")

        # Update cache
        self.cache_manager.update_note_cache(
            str(note_file),
            content_hash,
            note_file.stat().st_mtime,
            processed_content=content,
        )

        # Add to result stats
        result.add_generated(self._processor_type)
        result.processed += 1  # Increment processed count for newly generated content

    def _process_attachments(
        self,
        content: str,
        attachment_dir: Path,
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None,
    ) -> str:
        """Process attachments in content."""
        # Create output attachments directory
        output_attachments_dir = self.source_config.dest_dir / "attachments"
        output_attachments_dir.mkdir(exist_ok=True)

        def replace_attachment(match: re.Match) -> str:
            """Replace an attachment reference with processed content."""
            alt_text, path = match.groups()
            is_image = match.group(0).startswith("!")

            # URL decode the path
            decoded_path = urllib.parse.unquote(path)
            attachment_path = attachment_dir / Path(decoded_path).name

            # Skip .DS_Store files
            if attachment_path.name == ".DS_Store":
                if progress and task_id is not None:
                    progress.advance(task_id)
                return match.group(0)

            if not attachment_path.exists():
                logger.warning(f"Attachment not found: {attachment_path}")
                if progress and task_id is not None:
                    progress.advance(task_id)
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
                progress=progress,
                task_id=task_id,
            )
            return markdown if markdown else match.group(0)

        # Replace image references
        content = re.sub(r"!\[(.*?)\]\((.*?)\)", replace_attachment, content)

        # Replace embedded document references
        content = re.sub(
            r'\[(.*?)\]\((.*?)\)<!-- *{"embed":"true".*?} *-->',
            replace_attachment,
            content,
        )

        return content
