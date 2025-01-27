import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class OutputError(Exception):
    """Error during output generation."""
    pass

class OutputGenerator:
    """Generate and write consolidated markdown output."""

    def __init__(self, dest_dir: Path, backup_dir: Optional[Path] = None):
        self.dest_dir = dest_dir
        self.backup_dir = backup_dir or (dest_dir.parent / f"{dest_dir.name}_backup")

    def write_output(self, content: str, filename: str, force: bool = False) -> Path:
        """Write content to output file atomically."""
        output_path = self.dest_dir / filename

        # Check for collisions
        if output_path.exists() and not force:
            raise OutputError(f"Output file already exists: {output_path}")

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            try:
                # Write content to temp file
                temp_file.write(content)
                temp_file.flush()

                # Create backup if needed
                if output_path.exists() and self.backup_dir:
                    self._create_backup(output_path)

                # Ensure directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Atomic move
                shutil.move(temp_path, output_path)
                return output_path

            finally:
                # Clean up temp file if something went wrong
                if temp_path.exists():
                    temp_path.unlink()

    def format_document(self, title: str, content: str, metadata: Optional[dict] = None) -> str:
        """Format a document with consistent styling."""
        lines = []

        # Add title
        lines.append(f"# {title}")
        lines.append("")

        # Add metadata if provided
        if metadata:
            lines.append("## Metadata")
            for key, value in metadata.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        # Add main content
        lines.append(content.strip())

        return "\n".join(lines)

    def format_embedded_document(
        self,
        title: str,
        content: str,
        doc_type: str,
        metadata: Optional[dict] = None
    ) -> str:
        """Format an embedded document section."""
        lines = []

        # Add document header
        lines.append(f"<!-- EMBEDDED {doc_type.upper()}: {title} -->")
        lines.append("<details>")

        # Add summary with metadata
        summary_parts = [f"📄 {title}"]
        if metadata:
            size_kb = metadata.get('size_bytes', 0) / 1024
            summary_parts.append(f"({size_kb:.0f}KB)")
        lines.append(f"<summary>{' '.join(summary_parts)}</summary>")
        lines.append("")

        # Add content
        lines.append(content.strip())
        lines.append("")
        lines.append("</details>")

        return "\n".join(lines)

    def format_embedded_image(
        self,
        title: str,
        description: str,
        metadata: Optional[dict] = None
    ) -> str:
        """Format an embedded image section."""
        lines = []

        # Add image header
        lines.append(f"<!-- EMBEDDED IMAGE: {title} -->")
        lines.append("<details>")

        # Add summary with metadata
        summary_parts = [f"🖼️ {title}"]
        if metadata:
            size = metadata.get('size', (0, 0))
            size_kb = metadata.get('file_size', 0) / 1024
            summary_parts.append(f"({size[0]}x{size[1]}, {size_kb:.0f}KB)")
        lines.append(f"<summary>{' '.join(summary_parts)}</summary>")
        lines.append("")

        # Add description
        lines.append(description.strip())
        lines.append("")
        lines.append("</details>")

        return "\n".join(lines)

    def _create_backup(self, file_path: Path) -> None:
        """Create a backup of an existing file."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = self.backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup of {file_path}: {str(e)}")
