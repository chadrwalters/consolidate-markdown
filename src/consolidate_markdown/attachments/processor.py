import logging
import mimetypes
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from ..processors.result import ProcessingResult
from .document import MarkItDown
from .image import ImageProcessor
from .logging import attachment_logger, log_media_processing_error

logger = logging.getLogger(__name__)


@dataclass
class AttachmentMetadata:
    """Metadata for an attachment.

    This class stores metadata about an attachment file, including its path, size,
    type, dimensions (for images), and content (for documents). This metadata is used
    to generate comment-based representations of attachments in markdown files.
    """

    path: Path
    is_image: bool
    size: int
    alt_text: Optional[str] = None
    mime_type: str = ""
    dimensions: Optional[tuple[int, int]] = None
    markdown_content: str = ""
    created_time: Optional[float] = None
    modified_time: Optional[float] = None
    file_hash: Optional[str] = None
    error: Optional[str] = None


class AttachmentProcessor:
    """Process attachments and manage temporary files.

    This class handles the processing of attachment files, including images and documents.
    It extracts metadata, converts files to appropriate formats if needed, and manages
    temporary files.
    """

    def __init__(self, output_dir: Path):
        """Initialize the processor.

        Args:
            output_dir: The output directory for processed files
        """
        self.output_dir = output_dir
        self.temp_dir = output_dir / ".cm" / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Initialize processors for specific file types
        self.image_processor = ImageProcessor(self.temp_dir.parent)
        self.markitdown = MarkItDown(self.temp_dir.parent)

    def process_file(
        self,
        file_path: Path,
        force: bool = False,
        result: Optional[ProcessingResult] = None,
    ) -> Tuple[Path, AttachmentMetadata]:
        """Process a file and return its temporary path and metadata.

        This method processes an attachment file, extracting metadata and converting
        it to an appropriate format if needed. The processed file is stored in a
        temporary directory, and its metadata is returned.

        For images, it extracts dimensions and size, and converts HEIC to JPG and
        SVG to PNG for GPT analysis if needed.

        For documents, it extracts content using MarkItDown and other metadata.

        Args:
            file_path: Path to the attachment file
            force: Whether to force processing even if the file has been processed before
            result: Optional processing result for tracking statistics

        Returns:
            A tuple containing the path to the processed file and its metadata

        Raises:
            FileNotFoundError: If the attachment file does not exist
        """
        if not file_path.exists():
            error_msg = f"Attachment not found: {file_path}"
            attachment_logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Get basic metadata
        mime_type, _ = mimetypes.guess_type(str(file_path))
        size_bytes = file_path.stat().st_size
        is_image = bool(mime_type and mime_type.startswith("image/"))
        is_svg = file_path.suffix.lower() == ".svg"
        is_wav = file_path.suffix.lower() == ".wav"

        # SVGs are always treated as images
        if is_svg:
            is_image = True

        # Get file timestamps
        stat = file_path.stat()
        created_time = stat.st_ctime
        modified_time = stat.st_mtime

        # Calculate file hash for caching
        file_hash: Optional[str] = None

        # Create metadata object
        metadata = AttachmentMetadata(
            path=file_path,
            is_image=is_image,
            size=size_bytes,
            mime_type=mime_type or "",
            created_time=created_time,
            modified_time=modified_time,
            file_hash=file_hash,
        )

        # Create temporary path
        temp_path = self.temp_dir / file_path.name
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        # Process based on file type
        error_msg_doc = None
        try:
            attachment_logger.debug(f"Processing attachment: {file_path}")
            attachment_logger.debug(f"File type: {'image' if is_image else 'document'}")
            attachment_logger.debug(f"MIME type: {mime_type}")

            if is_wav:
                attachment_logger.debug(f"Processing WAV file: {file_path}")
                # Special handling for WAV files
                shutil.copy2(file_path, temp_path)
                metadata.markdown_content = f"[Audio file: {file_path.name}]"
                attachment_logger.debug(f"WAV file copied to: {temp_path}")
            elif is_image:
                # Process image files
                attachment_logger.debug(f"Processing image file: {file_path}")
                temp_path, image_metadata = self.image_processor.process_image(
                    file_path, force
                )

                # Update metadata with image-specific information
                metadata.dimensions = image_metadata.get("dimensions")
                if "inlined_content" in image_metadata:
                    metadata.markdown_content = image_metadata["inlined_content"]

                attachment_logger.debug(
                    f"Image processed: dimensions={metadata.dimensions}"
                )
            else:
                # Process document files
                attachment_logger.debug(f"Processing document file: {file_path}")
                temp_path = self.temp_dir / file_path.name
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, temp_path)

                # Handle PDF files
                if file_path.suffix.lower() == ".pdf":
                    try:
                        # PDF handling is now done in the MarkItDown class using PyMuPDF
                        attachment_logger.debug(
                            f"Converting PDF to markdown: {file_path}"
                        )
                        markdown_content = self.markitdown.convert_to_markdown(
                            file_path, force
                        )
                        if not markdown_content:
                            error_msg_doc = "PDF conversion produced no content"
                            attachment_logger.error(error_msg_doc)
                        else:
                            metadata.markdown_content = markdown_content
                            attachment_logger.debug(
                                f"PDF converted successfully, content length: {len(markdown_content)}"
                            )
                    except Exception as e:
                        error_msg_doc = f"PDF conversion failed: {str(e)}"
                        log_media_processing_error(file_path, error_msg_doc, "PDF")
                else:
                    # Try to convert other document types to markdown
                    try:
                        unsupported_extensions = [".mov", ".3gp", ".qtvr"]
                        if file_path.suffix.lower() not in unsupported_extensions:
                            attachment_logger.debug(
                                f"Converting document to markdown: {file_path}"
                            )
                            metadata.markdown_content = (
                                self.markitdown.convert_to_markdown(file_path, force)
                            )
                            attachment_logger.debug(
                                f"Document converted successfully, content length: {len(metadata.markdown_content)}"
                            )
                        else:
                            attachment_logger.warning(
                                f"Skipping unsupported file type: {file_path.name}"
                            )
                            metadata.markdown_content = (
                                f"[Unsupported file type: {file_path.name}]"
                            )
                    except Exception as e:
                        error_msg_doc = f"Document conversion failed: {str(e)}"
                        log_media_processing_error(file_path, error_msg_doc, "document")
                        metadata.markdown_content = (
                            f"[Error converting {file_path.name}: {str(e)}]"
                        )

        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            log_media_processing_error(file_path, error_msg, "attachment")
            attachment_logger.warning(
                f"{error_msg} for {file_path.name}, using basic copy"
            )
            temp_path = self.temp_dir / file_path.name
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, temp_path)

        metadata.error = error_msg_doc
        return temp_path, metadata

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.markitdown.cleanup()
        self.image_processor.cleanup()
