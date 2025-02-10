import json
import logging
import re
from pathlib import Path

import fitz  # PyMuPDF for better PDF handling
import pandas as pd
from markitdown import MarkItDown as MicrosoftMarkItDown

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Error during document conversion."""

    pass


class MarkItDown:
    """Convert various document formats to markdown.

    Note on PDF Handling:
    We use PyMuPDF (fitz) instead of Microsoft's MarkItDown for PDF processing because:
    1. Better text extraction with layout preservation
    2. Support for extracting images and tables
    3. More reliable handling of complex PDF structures
    4. Active maintenance and comprehensive documentation
    """

    CUSTOM_FORMATS = {
        ".csv": "csv",  # Direct CSV conversion
        ".txt": "text",  # Direct text conversion
        ".json": "json",  # JSON pretty printing
        ".pdf": "pdf",  # Custom PDF conversion using PyMuPDF
    }

    def __init__(self, cm_dir: Path):
        """Initialize with Microsoft's MarkItDown converter."""
        self.cm_dir = cm_dir
        self.temp_dir = cm_dir / "markitdown"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.converter = MicrosoftMarkItDown()

    def convert_to_markdown(self, file_path: Path, force: bool = False) -> str:
        """Convert a document to markdown format.

        Args:
            file_path: Path to the document file
            force: If True, force reconversion even if cached

        Returns:
            Markdown formatted string

        Raises:
            ConversionError: If conversion fails
            FileNotFoundError: If file not found
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        if file_path.name == ".DS_Store":
            logger.debug("Skipping system file: .DS_Store")
            return ""  # Return empty string instead of raising error

        # Try custom handlers first for known formats
        suffix = file_path.suffix.lower()
        try:
            # Try Microsoft's MarkItDown
            logger.debug(f"Attempting to convert {file_path}")
            result = self.converter.convert(str(file_path))
            logger.debug(f"MarkItDown result: {result}")
            if result and hasattr(result, "text_content"):
                logger.debug(f"Text content: {result.text_content}")
                return result.text_content

            # If MarkItDown fails, check for custom handlers
            if suffix in self.CUSTOM_FORMATS:
                logger.debug(f"Using custom handler for {suffix}")
                return self._convert_with_custom_handler(file_path, suffix)

            # For media files, just return a link
            media_extensions = [".mov", ".mp4", ".avi", ".wmv", ".flv", ".mkv"]
            if suffix in media_extensions:
                logger.debug(f"Creating link for media file: {file_path.name}")
                return f"[Media: {file_path.name}](attachments/{file_path.name})"

            # If we get here, no handler could process it
            raise ConversionError(f"Format not supported: {suffix}")
        except Exception as e:
            logger.debug(f"Conversion failed: {str(e)}", exc_info=True)
            raise ConversionError(f"Failed to convert {file_path}: {str(e)}")

    def _convert_with_custom_handler(self, file_path: Path, suffix: str) -> str:
        """Convert using custom handlers for specific formats."""
        try:
            if suffix == ".csv":
                return self._convert_csv(file_path)
            elif suffix == ".txt":
                return self._convert_text(file_path)
            elif suffix == ".json":
                return self._convert_json(file_path)
            elif suffix == ".pdf":
                return self._convert_pdf(file_path)
            else:
                raise ConversionError(f"No custom handler for: {suffix}")
        except Exception as e:
            raise ConversionError(f"Custom handler failed for {suffix}: {str(e)}")

    def _convert_csv(self, file_path: Path) -> str:
        """Convert CSV to markdown table."""
        encodings = ["utf-8", "latin1", "cp1252", "iso-8859-1"]
        last_error = None

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                table = df.to_markdown(index=False, tablefmt="pipe")
                table = re.sub(r"\s+\|\s+", " | ", table)
                table = re.sub(r"\n\s*\n+", "\n\n", table)
                return table
            except UnicodeDecodeError as e:
                last_error = e
                continue
            except Exception as e:
                raise ConversionError(f"Failed to convert CSV: {str(e)}")

        raise ConversionError(
            f"Failed to decode CSV with any encoding: {str(last_error)}"
        )

    def _convert_text(self, file_path: Path) -> str:
        """Convert text file to markdown."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return f"```\n{content}\n```"
        except Exception as e:
            raise ConversionError(f"Failed to read text file: {str(e)}")

    def _convert_json(self, file_path: Path) -> str:
        """Convert JSON file to pretty-printed markdown."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            pretty = json.dumps(data, indent=2)
            return f"```json\n{pretty}\n```"
        except Exception as e:
            raise ConversionError(f"Failed to parse JSON file: {str(e)}")

    def _convert_pdf(self, file_path: Path) -> str:
        """Convert PDF to markdown using PyMuPDF.

        PyMuPDF provides superior PDF handling compared to Microsoft's MarkItDown:
        - Better text extraction with layout preservation
        - Support for extracting images and tables
        - More reliable handling of complex PDF structures
        """
        try:
            # Open the PDF
            doc = fitz.open(file_path)

            # Extract text with layout preservation
            content = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Get text blocks with their layout information
                blocks = page.get_text("dict")["blocks"]

                # Process each text block
                for block in blocks:
                    if block.get("type") == 0:  # Text block
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text = span.get("text", "").strip()
                                if text:
                                    content.append(text)

            # Join content with proper spacing
            text = "\n".join(content)

            # If no content was extracted, try a simpler approach
            if not text.strip():
                text = ""
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text += page.get_text() + "\n\n"

            # Format as markdown with metadata
            page_count = len(doc)
            size_kb = file_path.stat().st_size // 1024

            # Close the document
            doc.close()

            # Only include text content if we have some
            text = text.strip()
            text_block = (
                f"""```pdf
{text}
```"""
                if text
                else "[PDF content could not be extracted]"
            )

            return f"""<!-- EMBEDDED PDF: {file_path.name} -->
<details>
<summary>📄 {file_path.name} ({size_kb}KB, {page_count} pages)</summary>

{text_block}

[View PDF](attachments/{file_path.name})
</details>"""

        except Exception as e:
            raise ConversionError(f"Failed to convert PDF: {str(e)}")

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)
