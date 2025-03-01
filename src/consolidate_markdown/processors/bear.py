"""Process Bear notes."""
# mypy: disable-error-code="no-any-return"

import logging
import re
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple

from rich.progress import Progress, TaskID

from ..attachments.processor import AttachmentProcessor
from ..cache import CacheManager
from ..config import Config, SourceConfig
from ..utils import ensure_directory
from .base import SourceProcessor
from .result import ProcessingResult

logger = logging.getLogger(__name__)


class BearProcessor(SourceProcessor):
    """Process Bear notes and their attachments."""

    def __init__(
        self, source_config: SourceConfig, cache_manager: Optional[CacheManager] = None
    ):
        """Initialize processor."""
        super().__init__(source_config, cache_manager)
        self.validate()  # Call validate to ensure source directory exists

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
        # Read the note content
        content = note_file.read_text()

        # Get the attachment directory
        attachment_dir = note_file.parent / note_file.stem

        # Output file path
        output_file = self.source_config.dest_dir / note_file.name

        # Define a custom processor function with explicit string return type
        def process_func(content_to_process: str) -> str:  # type: ignore
            if not attachment_dir.exists():
                return content_to_process

            # Process attachments in the content
            result_content = self._process_attachments(
                content_to_process,
                attachment_dir,
                self.attachment_processor,
                config,
                result,
                progress,
                task_id,
            )
            # Ensure we return a string
            return result_content

        # Process the file with caching
        self.process_file_with_cache(
            note_file,
            content,
            output_file,
            config,
            result,
            attachment_dir,
            process_func,
        )

    def _process_attachments(
        self,
        content: str,
        attachment_dir: Path,
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None,
    ) -> str:  # type: ignore
        """Process attachments in content."""
        # Create output attachments directory
        output_attachments_dir = self.source_config.dest_dir / "attachments"
        ensure_directory(output_attachments_dir)

        def replace_attachment(match: re.Match) -> str:  # type: ignore
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

            logger.info(
                f"Processing attachment: {attachment_path} (is_image={is_image})"
            )

            # Process the attachment using the base class method
            markdown_result = self._process_attachment(
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

            # Handle the Optional[str] return type
            if markdown_result is None:
                return match.group(0)

            logger.info(
                f"Generated markdown for {attachment_path.name}: {markdown_result[:200]}"
            )
            return markdown_result

        # Replace image references
        result_content: str = re.sub(
            r"!\[(.*?)\]\((.*?)\)", replace_attachment, content
        )

        # First try to replace embedded document references with Bear's format or our PDF format
        result_content = re.sub(
            r'\[(.*?)\]\((.*?)\)(?:<!-- *(?:{"embed":"true".*?}|EMBEDDED PDF: .*?) *-->)',
            replace_attachment,
            result_content,
        )

        # Then replace any remaining PDF links that don't have comments and haven't been replaced
        result_content = re.sub(
            r'\[(.*?)\]\((.*?\.pdf)\)(?!<!-- *(?:{"embed":"true".*?}|EMBEDDED PDF: .*?) *-->)',
            replace_attachment,
            result_content,
        )

        return result_content
