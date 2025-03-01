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

    This class handles the processing of attachment files (images and documents),
    extracting metadata and converting them to appropriate formats if needed.

    For images, it can:
    - Extract dimensions and size
    - Convert HEIC to JPG
    - Convert SVG to PNG for GPT analysis
    - Handle various image formats

    For documents, it can:
    - Extract content using MarkItDown
    - Extract size and other metadata
    - Handle various document formats

    The processed attachments are not copied to the output directory; instead,
    their metadata is used to generate comment-based representations in markdown files.
    """

    def __init__(self, cm_dir: Path):
        """Initialize the attachment processor.

        Args:
            cm_dir: The consolidate markdown directory for temporary files
        """
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
            raise FileNotFoundError(f"Attachment not found: {file_path}")

        # Get basic metadata
        mime_type, _ = mimetypes.guess_type(str(file_path))
        size_bytes = file_path.stat().st_size
        is_image = mime_type and mime_type.startswith("image/")
        is_svg = file_path.suffix.lower() == ".svg"

        # SVGs are always treated as images
        if is_svg:
            is_image = True

        # Get file timestamps
        stat = file_path.stat()
        created_time = stat.st_ctime
        modified_time = stat.st_mtime

        # Calculate file hash for caching
        file_hash: Optional[str] = None
        try:
            import hashlib

            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate file hash: {str(e)}")

        # Initialize metadata
        metadata = AttachmentMetadata(
            path=file_path,
            is_image=bool(is_image),
            size=size_bytes,
            mime_type=mime_type or "application/octet-stream",
            created_time=created_time,
            modified_time=modified_time,
            file_hash=file_hash,
        )

        # Process based on file type
        temp_path: Optional[Path] = None
        dimensions: Optional[Tuple[int, int]] = None
        error_msg_doc: Optional[str] = None

        try:
            if is_image:
                # Process image
                temp_path, img_metadata = self.image_processor.process_image(
                    file_path, force
                )
                dimensions = img_metadata.get("dimensions")
                metadata.dimensions = dimensions

                # Handle SVG files
                if file_path.suffix.lower() == ".svg":
                    width = dimensions[0] if dimensions else 0
                    height = dimensions[1] if dimensions else 0
                    metadata.markdown_content = f"""![{file_path.name}](attachments/{file_path.name})

<!-- EMBEDDED IMAGE: {file_path.name} -->
<details>
<summary> {file_path.name} ({width}x{height}, {size_bytes//1024}KB)</summary>

{img_metadata.get('inlined_content', '[Error analyzing image]')}

</details>"""
            else:
                # Process document files
                temp_path = self.temp_dir / file_path.name
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, temp_path)

                # Handle PDF files
                if file_path.suffix.lower() == ".pdf":
                    try:
                        # PDF handling is now done in the MarkItDown class using PyMuPDF
                        markdown_content = self.markitdown.convert_to_markdown(
                            file_path, force
                        )
                        if not markdown_content:
                            error_msg_doc = "PDF conversion produced no content"
                            logger.error(error_msg_doc)
                        else:
                            metadata.markdown_content = markdown_content
                    except Exception as e:
                        error_msg_doc = f"PDF conversion failed: {str(e)}"
                        logger.error(error_msg_doc, exc_info=True)
                else:
                    # Try to convert other document types to markdown
                    try:
                        unsupported_extensions = [".mov", ".3gp", ".qtvr"]
                        if file_path.suffix.lower() not in unsupported_extensions:
                            metadata.markdown_content = (
                                self.markitdown.convert_to_markdown(file_path, force)
                            )
                        else:
                            logger.warning(
                                f"Skipping unsupported file type: {file_path.name}"
                            )
                            metadata.markdown_content = (
                                f"[Unsupported file type: {file_path.name}]"
                            )
                    except Exception as e:
                        error_msg_doc = f"Document conversion failed: {str(e)}"
                        logger.error(error_msg_doc, exc_info=True)
                        metadata.markdown_content = (
                            f"[Error converting {file_path.name}: {str(e)}]"
                        )

        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            logger.warning(f"{error_msg} for {file_path.name}, using basic copy")
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
