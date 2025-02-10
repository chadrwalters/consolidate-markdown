import logging
from pathlib import Path

from markitdown import MarkItDown as MicrosoftMarkItDown

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Error during document conversion."""

    pass


class MarkItDown:
    """Convert various document formats to markdown using Microsoft's MarkItDown package."""

    def __init__(self, cm_dir: Path):
        """Initialize with Microsoft's MarkItDown converter."""
        self.cm_dir = cm_dir
        self.converter = MicrosoftMarkItDown()

    def convert_to_markdown(self, file_path: Path, force: bool = False) -> str:
        """Convert a document to markdown format using Microsoft's MarkItDown."""
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        if file_path.name == ".DS_Store":
            raise ConversionError("Skipping system file: .DS_Store")

        try:
            result = self.converter.convert(str(file_path))
            return result.text_content
        except Exception as e:
            raise ConversionError(f"Failed to convert {file_path}: {str(e)}")

    def cleanup(self) -> None:
        """Clean up temporary files."""
        # Microsoft's MarkItDown handles its own cleanup
        pass
