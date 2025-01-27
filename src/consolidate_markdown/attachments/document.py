import csv
import io
import json
import logging
import subprocess
import re
from pathlib import Path
from typing import Optional, List

import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ConversionError(Exception):
    """Error during document conversion."""
    pass

class MarkItDown:
    """Convert various document formats to markdown."""

    SUPPORTED_FORMATS = {
        '.docx': 'pandoc --from docx --to markdown',
        '.pdf': 'pdftotext',  # PDF to text conversion
        '.csv': 'csv',        # Direct CSV conversion
        '.xlsx': 'xlsx',      # Excel conversion
        '.txt': 'text',       # Direct text conversion
        '.json': 'json',      # JSON pretty printing
        '.html': 'html'       # HTML to markdown
    }

    def __init__(self, cm_dir: Path):
        self.cm_dir = cm_dir
        self.temp_dir = cm_dir / "markitdown"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def convert_to_markdown(self, file_path: Path, force: bool = False) -> str:
        """Convert a document to markdown format."""
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        # Skip system files
        if file_path.name == '.DS_Store':
            raise ConversionError("Skipping system file: .DS_Store")

        if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ConversionError(f"Unsupported format: {file_path.suffix}")

        try:
            if file_path.suffix.lower() == '.docx':
                return self._convert_docx(file_path)
            elif file_path.suffix.lower() == '.pdf':
                return self._convert_pdf(file_path)
            elif file_path.suffix.lower() == '.csv':
                return self._convert_csv(file_path)
            elif file_path.suffix.lower() == '.xlsx':
                return self._convert_xlsx(file_path)
            elif file_path.suffix.lower() == '.txt':
                return self._convert_text(file_path)
            elif file_path.suffix.lower() == '.json':
                return self._convert_json(file_path)
            elif file_path.suffix.lower() == '.html':
                return self._convert_html(file_path)
            else:
                raise ConversionError(f"No converter implemented for: {file_path.suffix}")

        except Exception as e:
            raise ConversionError(f"Failed to convert {file_path}: {str(e)}")

    def _convert_docx(self, file_path: Path) -> str:
        """Convert DOCX to markdown using pandoc."""
        try:
            result = subprocess.run(
                ['pandoc', '--from', 'docx', '--to', 'markdown', str(file_path)],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"Pandoc conversion failed: {e.stderr}")
        except FileNotFoundError:
            raise ConversionError("Pandoc not found. Please install pandoc.")

    def _convert_pdf(self, file_path: Path) -> str:
        """Convert PDF to markdown using pdftotext."""
        try:
            result = subprocess.run(
                ['pdftotext', '-layout', str(file_path), '-'],
                capture_output=True,
                text=True,
                check=True
            )
            return f"```\n{result.stdout}\n```"
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"PDF conversion failed: {e.stderr}")
        except FileNotFoundError:
            raise ConversionError("pdftotext not found. Please install poppler-utils.")

    def _convert_csv(self, file_path: Path) -> str:
        """Convert CSV to markdown table."""
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        last_error = None

        for encoding in encodings:
            try:
                # Try reading with different encodings
                df = pd.read_csv(file_path, encoding=encoding)

                # Convert to markdown table with improved formatting
                table = df.to_markdown(index=False, tablefmt='pipe')

                # Clean up the table formatting
                table = re.sub(r'\s+\|\s+', ' | ', table)  # Normalize cell spacing
                table = re.sub(r'\n\s*\n+', '\n\n', table)  # Remove extra blank lines

                return table
            except UnicodeDecodeError as e:
                last_error = e
                continue
            except Exception as e:
                raise ConversionError(f"Failed to convert CSV: {str(e)}")

        raise ConversionError(f"Failed to decode CSV with any encoding: {str(last_error)}")

    def _convert_xlsx(self, file_path: Path) -> str:
        """Convert Excel to markdown tables."""
        try:
            # Read all sheets
            sheets = pd.read_excel(file_path, sheet_name=None)

            # Convert each sheet to markdown
            result = []
            for name, df in sheets.items():
                result.append(f"### Sheet: {name}\n\n{df.to_markdown(index=False)}\n")

            return "\n".join(result)
        except Exception as e:
            raise ConversionError(f"Failed to convert Excel file: {str(e)}")

    def _convert_text(self, file_path: Path) -> str:
        """Convert text file to markdown."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"```\n{content}\n```"
        except Exception as e:
            raise ConversionError(f"Failed to read text file: {str(e)}")

    def _convert_json(self, file_path: Path) -> str:
        """Convert JSON file to pretty-printed markdown."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            pretty = json.dumps(data, indent=2)
            return f"```json\n{pretty}\n```"
        except Exception as e:
            raise ConversionError(f"Failed to parse JSON file: {str(e)}")

    def _convert_html(self, file_path: Path) -> str:
        """Convert HTML to markdown using pandoc."""
        try:
            # First convert HTML to markdown
            result = subprocess.run(
                ['pandoc', '--from', 'html', '--to', 'gfm', '--wrap=none', '--columns=1000', str(file_path)],
                capture_output=True,
                text=True,
                check=True
            )

            # Clean up the markdown output
            markdown = result.stdout

            # Remove CSS classes, inline styles, and other attributes
            markdown = re.sub(r'\{[^}]*\}', '', markdown)
            markdown = re.sub(r'title="[^"]*"', '', markdown)
            markdown = re.sub(r'role="[^"]*"', '', markdown)

            # Clean up table formatting
            markdown = re.sub(r'\s+\|\s+', ' | ', markdown)  # Normalize table cell spacing
            markdown = re.sub(r'\n\s*\n+', '\n\n', markdown)  # Remove extra blank lines
            markdown = re.sub(r'(\n\+[-]+\+)+\n', '\n', markdown)  # Remove redundant table borders
            markdown = re.sub(r'(\n\|[-]+\|)+\n', '\n', markdown)  # Remove redundant table separators

            # Clean up JIRA-specific formatting
            markdown = re.sub(r'\[(?:Reopened|In Progress|Awaiting Approval|Need Business Feedback)\]', r'\g<0>', markdown)  # Keep status without formatting
            markdown = re.sub(r'\[\]\{[^}]*\}', '', markdown)  # Remove empty links with attributes
            markdown = re.sub(r':::\s*\{[^}]*\}[^:]*:::', '', markdown)  # Remove JIRA tooltips
            markdown = re.sub(r':::\s*end-of-[^:]*:::', '', markdown)  # Remove JIRA end markers

            # Clean up whitespace
            markdown = re.sub(r' +', ' ', markdown)  # Normalize spaces
            markdown = re.sub(r'\n{3,}', '\n\n', markdown)  # Normalize line breaks

            # Remove horizontal lines
            markdown = re.sub(r'-{3,}.*-{3,}\n', '', markdown)

            # Clean up table headers
            markdown = re.sub(r'\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*\|', '', markdown)

            return markdown.strip()
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"HTML conversion failed: {e.stderr}")
        except FileNotFoundError:
            raise ConversionError("Pandoc not found. Please install pandoc.")

    def cleanup(self) -> None:
        """Clean up temporary files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
