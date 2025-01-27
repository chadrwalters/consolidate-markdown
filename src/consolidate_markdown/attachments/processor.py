import mimetypes
import shutil
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict

from .document import MarkItDown
from .image import ImageProcessor
from ..processors.base import ProcessingResult

logger = logging.getLogger(__name__)

@dataclass
class AttachmentMetadata:
    """Metadata for an attachment file."""
    original_path: Path
    mime_type: str
    size_bytes: int
    is_image: bool
    dimensions: Optional[tuple[int, int]] = None
    markdown_content: Optional[str] = None

class AttachmentProcessor:
    """Process attachments and manage temporary files."""

    def __init__(self, cm_dir: Path):
        self.cm_dir = cm_dir
        self.temp_dir = cm_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.markitdown = MarkItDown(cm_dir)
        self.image_processor = ImageProcessor(cm_dir)

    def process_file(self, file_path: Path, force: bool = False, result: Optional[ProcessingResult] = None) -> Tuple[Path, AttachmentMetadata]:
        """Process a file and return its temporary path and metadata."""
        if not file_path.exists():
            raise FileNotFoundError(f"Attachment not found: {file_path}")

        # Get basic metadata
        mime_type, _ = mimetypes.guess_type(str(file_path))
        size_bytes = file_path.stat().st_size
        is_image = mime_type and mime_type.startswith('image/')

        # Process image files
        if is_image:
            try:
                temp_path, img_metadata = self.image_processor.process_image(file_path, force)
                metadata = AttachmentMetadata(
                    original_path=file_path,
                    mime_type=mime_type or 'application/octet-stream',
                    size_bytes=img_metadata['size_bytes'],
                    is_image=True,
                    dimensions=img_metadata['dimensions']
                )
                return temp_path, metadata
            except Exception as e:
                logger.warning(f"Image processing failed for {file_path.name}, using basic copy: {str(e)}")
                # Fallback to basic copy if image processing fails
                temp_path = self.temp_dir / file_path.name
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, temp_path)
                metadata = AttachmentMetadata(
                    original_path=file_path,
                    mime_type=mime_type or 'application/octet-stream',
                    size_bytes=size_bytes,
                    is_image=True
                )
                return temp_path, metadata

        # Process document files
        try:
            # Create temp path preserving directory structure
            temp_path = self.temp_dir / file_path.name
            temp_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if we need to process
            if not force and temp_path.exists():
                if temp_path.stat().st_mtime >= file_path.stat().st_mtime:
                    return temp_path, AttachmentMetadata(
                        original_path=file_path,
                        mime_type=mime_type or 'application/octet-stream',
                        size_bytes=size_bytes,
                        is_image=False
                    )

            # Copy to temp location
            shutil.copy2(file_path, temp_path)

            # Convert document to markdown if applicable
            markdown_content = None
            if file_path.suffix.lower() in MarkItDown.SUPPORTED_FORMATS:
                try:
                    markdown_content = self.markitdown.convert_to_markdown(file_path, force)
                except Exception as e:
                    markdown_content = f"[Error converting {file_path.name}: {str(e)}]"

            metadata = AttachmentMetadata(
                original_path=file_path,
                mime_type=mime_type or 'application/octet-stream',
                size_bytes=size_bytes,
                is_image=False,
                markdown_content=markdown_content
            )
            return temp_path, metadata
        except Exception as e:
            logger.warning(f"Document conversion failed for {file_path.name}, using basic copy: {str(e)}")
            # Fallback to basic copy
            temp_path = self.temp_dir / file_path.name
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, temp_path)
            metadata = AttachmentMetadata(
                original_path=file_path,
                mime_type=mime_type or 'application/octet-stream',
                size_bytes=size_bytes,
                is_image=False
            )
            return temp_path, metadata

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.markitdown.cleanup()
        self.image_processor.cleanup()
