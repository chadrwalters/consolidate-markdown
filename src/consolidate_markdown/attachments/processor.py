import logging
import mimetypes
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from ..processors.result import ProcessingResult
from .document import MarkItDown
from .image import ImageProcessor

logger = logging.getLogger(__name__)


@dataclass
class AttachmentMetadata:
    """Metadata for an attachment file."""

    original_path: Path
    mime_type: str
    size_bytes: int
    is_image: bool
    dimensions: Optional[tuple[int, int]] = None
    markdown_content: str = ""  # Default to empty string instead of None
    created_time: Optional[float] = None
    modified_time: Optional[float] = None
    file_hash: Optional[str] = None
    error: Optional[str] = None


class AttachmentProcessor:
    """Process attachments and manage temporary files."""

    def __init__(self, cm_dir: Path):
        self.cm_dir = cm_dir
        self.temp_dir = cm_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.markitdown = MarkItDown(cm_dir)
        self.image_processor = ImageProcessor(cm_dir)

    def process_file(
        self,
        file_path: Path,
        force: bool = False,
        result: Optional[ProcessingResult] = None,
    ) -> Tuple[Path, AttachmentMetadata]:
        """Process a file and return its temporary path and metadata."""
        if not file_path.exists():
            raise FileNotFoundError(f"Attachment not found: {file_path}")

        # Get basic metadata
        mime_type, _ = mimetypes.guess_type(str(file_path))
        size_bytes = file_path.stat().st_size
        is_image = mime_type and mime_type.startswith("image/")

        # Get file timestamps
        stat = file_path.stat()
        created_time = stat.st_ctime
        modified_time = stat.st_mtime

        # Calculate file hash for caching
        file_hash: Optional[str] = None
        try:
            import hashlib

            file_hash = hashlib.md5(file_path.read_bytes()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate hash for {file_path}: {str(e)}")

        # Process image files
        if is_image:
            try:
                temp_path, img_metadata = self.image_processor.process_image(
                    file_path, force
                )
                metadata = AttachmentMetadata(
                    original_path=file_path,
                    mime_type=mime_type or "application/octet-stream",
                    size_bytes=img_metadata["size_bytes"],
                    is_image=True,
                    dimensions=img_metadata["dimensions"],
                    created_time=created_time,
                    modified_time=modified_time,
                    file_hash=file_hash,
                )
                return temp_path, metadata
            except Exception as e:
                error_msg = f"Image processing failed: {str(e)}"
                logger.warning(f"{error_msg} for {file_path.name}, using basic copy")
                # Fallback to basic copy if image processing fails
                temp_path = self.temp_dir / file_path.name
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, temp_path)
                metadata = AttachmentMetadata(
                    original_path=file_path,
                    mime_type=mime_type or "application/octet-stream",
                    size_bytes=size_bytes,
                    is_image=True,
                    dimensions=None,
                    created_time=created_time,
                    modified_time=modified_time,
                    file_hash=file_hash,
                    error=error_msg,
                )
                return temp_path, metadata

        # Process document files
        try:
            # Create temp path preserving directory structure
            temp_path = self.temp_dir / file_path.name
            temp_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if we need to process
            if not force and temp_path.exists():
                # For Bear attachments in iCloud, don't use timestamps
                if "com~apple~CloudDocs/_BearNotes" in str(file_path):
                    return temp_path, AttachmentMetadata(
                        original_path=file_path,
                        mime_type=mime_type or "application/octet-stream",
                        size_bytes=size_bytes,
                        is_image=False,
                        created_time=created_time,
                        modified_time=modified_time,
                        file_hash=file_hash,
                    )
                # For other files, use timestamp check
                elif temp_path.stat().st_mtime >= file_path.stat().st_mtime:
                    return temp_path, AttachmentMetadata(
                        original_path=file_path,
                        mime_type=mime_type or "application/octet-stream",
                        size_bytes=size_bytes,
                        is_image=False,
                        created_time=created_time,
                        modified_time=modified_time,
                        file_hash=file_hash,
                    )

            # Copy to temp location
            shutil.copy2(file_path, temp_path)

            # Convert document to markdown if applicable
            markdown_content: str = ""  # Initialize with empty string
            error_msg_doc: Optional[str] = None
            if file_path.suffix.lower() in MarkItDown.SUPPORTED_FORMATS:
                try:
                    # convert_to_markdown always returns str or raises an exception
                    markdown_content = self.markitdown.convert_to_markdown(
                        file_path, force
                    )
                except Exception as e:
                    error_msg_doc = f"Document conversion failed: {str(e)}"
                    markdown_content = f"[Error converting {file_path.name}: {str(e)}]"

            metadata = AttachmentMetadata(
                original_path=file_path,
                mime_type=mime_type or "application/octet-stream",
                size_bytes=size_bytes,
                is_image=False,
                markdown_content=markdown_content,
                created_time=created_time,
                modified_time=modified_time,
                file_hash=file_hash,
                error=error_msg_doc,
            )
            return temp_path, metadata
        except Exception as e:
            error_msg = f"Document processing failed: {str(e)}"
            logger.warning(f"{error_msg} for {file_path.name}, using basic copy")
            # Fallback to basic copy
            temp_path = self.temp_dir / file_path.name
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, temp_path)
            metadata = AttachmentMetadata(
                original_path=file_path,
                mime_type=mime_type or "application/octet-stream",
                size_bytes=size_bytes,
                is_image=False,
                created_time=created_time,
                modified_time=modified_time,
                file_hash=file_hash,
                error=error_msg,
            )
            return temp_path, metadata

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.markitdown.cleanup()
        self.image_processor.cleanup()
