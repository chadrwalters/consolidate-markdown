import json
import logging
import re
from pathlib import Path

import pandas as pd
from markitdown import MarkItDown as MicrosoftMarkItDown
from markitdown._markitdown import UnsupportedFormatException
from pdfminer.high_level import extract_text

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Error during document conversion."""

    pass


class MarkItDown:
    """Convert various document formats to markdown using Microsoft's MarkItDown package and custom handlers."""

    CUSTOM_FORMATS = {
        ".csv": "csv",  # Direct CSV conversion
        ".txt": "text",  # Direct text conversion
        ".json": "json",  # JSON pretty printing
        ".pdf": "pdf",  # Custom PDF conversion
    }

    def __init__(self, cm_dir: Path):
        """Initialize with Microsoft's MarkItDown converter."""
        self.cm_dir = cm_dir
        self.temp_dir = cm_dir / "markitdown"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.converter = MicrosoftMarkItDown()

    def convert_to_markdown(self, file_path: Path, force: bool = False) -> str:
        """Convert a document to markdown format using Microsoft's MarkItDown or custom handlers."""
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        if file_path.name == ".DS_Store":
            raise ConversionError("Skipping system file: .DS_Store")

        # Try custom handlers first for known formats
        suffix = file_path.suffix.lower()
        if suffix in self.CUSTOM_FORMATS:
            try:
                logger.debug(f"Using custom handler for {suffix}")
                return self._convert_with_custom_handler(file_path, suffix)
            except Exception as e:
                logger.debug(f"Custom handler failed: {str(e)}", exc_info=True)
                # Fall back to Microsoft's MarkItDown

        try:
            # Try Microsoft's MarkItDown
            logger.debug(f"Attempting to convert {file_path} using MarkItDown")
            result = self.converter.convert(str(file_path))
            logger.debug(f"MarkItDown result: {result}")
            if result and hasattr(result, "text_content"):
                logger.debug(f"Text content: {result.text_content}")
                return result.text_content
            raise ConversionError("No text content returned")
        except UnsupportedFormatException:
            # Fall back to custom handlers for unsupported formats
            if suffix in self.CUSTOM_FORMATS:
                logger.debug(f"Using custom handler for {suffix}")
                return self._convert_with_custom_handler(file_path, suffix)
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
        """Convert PDF to markdown using pdfminer-six."""
        try:
            text = extract_text(str(file_path))
            # Clean up the text
            text = re.sub(
                r"\s+", " ", text
            ).strip()  # Replace multiple whitespace with single space
            text = re.sub(
                r"\f", "\n\n", text
            )  # Replace form feeds with double newlines
            return text
        except Exception as e:
            raise ConversionError(f"Failed to convert PDF: {str(e)}")

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)
