import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .processors.result import ProcessingResult

logger = logging.getLogger(__name__)

# Global console instance for consistent styling
console = Console()


class OutputError(Exception):
    """Error during output generation."""

    pass


class OutputGenerator:
    """Generate and write consolidated markdown output."""

    def __init__(self, dest_dir: Path, backup_dir: Optional[Path] = None):
        self.dest_dir = dest_dir
        self.backup_dir = backup_dir or (dest_dir.parent / f"{dest_dir.name}_backup")

    def write_output(self, filename: str, content: str, force: bool = False) -> Path:
        """Write content to output file atomically."""
        output_path = self.dest_dir / filename

        # Create parent directories
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Check for collisions
        if output_path.exists():
            if output_path.is_dir():
                raise OutputError(f"Cannot write to {output_path}: path is a directory")
            if not force:
                raise OutputError(f"Output file already exists: {output_path}")

        # Create temporary file in the same directory
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".md",
                delete=False,
                dir=output_path.parent,
                prefix=".tmp_",
            )
            temp_path = Path(temp_file.name)

            # Write content
            temp_path.write_text(content)

            # Create backup if needed
            if output_path.exists() and self.backup_dir:
                self._create_backup(output_path)

            # Atomic move
            shutil.move(str(temp_path), str(output_path))
            return output_path

        except Exception as e:
            # Clean up temp file if something went wrong
            if temp_file:
                try:
                    Path(temp_file.name).unlink(missing_ok=True)
                except Exception:
                    pass  # Best effort cleanup
            raise OutputError(f"Failed to write output: {str(e)}")

        finally:
            if temp_file:
                temp_file.close()

    def _create_backup(self, file_path: Path) -> None:
        """Create a backup of an existing file."""
        try:
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Generate backup path
            backup_path = self.backup_dir / file_path.name

            # Copy file with metadata
            shutil.copy2(str(file_path), str(backup_path))
            logger.info(f"Created backup: {backup_path}")

        except Exception as e:
            raise OutputError(f"Failed to create backup of {file_path}: {str(e)}")

    def format_document(
        self, title: str, content: str, metadata: Optional[dict] = None
    ) -> str:
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
        self, title: str, content: str, doc_type: str, metadata: Optional[dict] = None
    ) -> str:
        """Format an embedded document section."""
        lines = []

        # Add document header
        lines.append(f"<!-- EMBEDDED {doc_type.upper()}: {title} -->")
        lines.append("<details>")

        # Add summary with metadata
        summary_parts = [f"📄 {title}"]
        if metadata:
            size_kb = metadata.get("size_bytes", 0) / 1024
            summary_parts.append(f"({size_kb:.0f}KB)")
        lines.append(f"<summary>{' '.join(summary_parts)}</summary>")
        lines.append("")

        # Add content
        lines.append(content.strip())
        lines.append("")
        lines.append("</details>")

        return "\n".join(lines)

    def format_embedded_image(
        self, title: str, description: str, metadata: Optional[dict] = None
    ) -> str:
        """Format an embedded image section."""
        lines = []

        # Add image header
        lines.append(f"<!-- EMBEDDED IMAGE: {title} -->")
        lines.append("<details>")

        # Add summary with metadata
        summary_parts = [f"🖼️ {title}"]
        if metadata:
            size = metadata.get("size", (0, 0))
            size_kb = metadata.get("file_size", 0) / 1024
            summary_parts.append(f"({size[0]}x{size[1]}, {size_kb:.0f}KB)")
        lines.append(f"<summary>{' '.join(summary_parts)}</summary>")
        lines.append("")

        # Add description
        lines.append(description.strip())
        lines.append("")
        lines.append("</details>")

        return "\n".join(lines)


def format_count(count: int) -> str:
    """Format a count for display.

    Args:
        count: The number to format

    Returns:
        Formatted string with thousands separator
    """
    return f"{count:,}"


def print_summary(result: ProcessingResult) -> None:
    """Print a formatted summary of processing results.

    Args:
        result: The processing results to display
    """
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric")
    table.add_column("Count", justify="right")

    # Core metrics
    table.add_row("Total Processed", format_count(result.processed))
    table.add_row("Generated", format_count(result.regenerated))
    table.add_row("From Cache", format_count(result.from_cache))
    table.add_row("Skipped", format_count(result.skipped))

    # Add separator
    table.add_section()

    # Document metrics
    table.add_row(
        "Documents Processed",
        format_count(result.documents_processed),
    )
    table.add_row(
        "Documents Generated",
        format_count(result.documents_generated),
    )
    table.add_row(
        "Documents From Cache",
        format_count(result.documents_from_cache),
    )
    table.add_row(
        "Documents Skipped",
        format_count(result.documents_skipped),
    )

    # Add separator
    table.add_section()

    # Image metrics
    table.add_row(
        "Images Processed",
        format_count(result.images_processed),
    )
    table.add_row(
        "Images Generated",
        format_count(result.images_generated),
    )
    table.add_row(
        "Images From Cache",
        format_count(result.images_from_cache),
    )
    table.add_row(
        "Images Skipped",
        format_count(result.images_skipped),
    )

    # Add separator
    table.add_section()

    # GPT metrics
    table.add_row(
        "GPT Cache Hits",
        format_count(result.gpt_cache_hits),
    )
    table.add_row(
        "GPT New Analyses",
        format_count(result.gpt_new_analyses),
    )
    table.add_row(
        "GPT Analyses Skipped",
        format_count(result.gpt_skipped),
    )

    # Create panel with table
    panel = Panel(
        table,
        title="[bold green]Consolidation Summary[/bold green]",
        expand=False,
    )

    # Print the summary
    console.print(panel)

    # If there are errors, print them in a separate panel
    if result.errors:
        error_table = Table(show_header=True, header_style="bold red")
        error_table.add_column("Error Messages")

        for error in result.errors:
            error_table.add_row(f"[red]{error}[/red]")

        error_panel = Panel(
            error_table,
            title="[bold red]Processing Errors[/bold red]",
            expand=False,
        )
        console.print(error_panel)


def print_deletion_message(path: str) -> None:
    """Print a formatted deletion message.

    Args:
        path: The path being deleted
    """
    console.print(f"[bold red]Deleting: {path}[/bold red]")


def print_processing_message(message: str, debug: bool = False) -> None:
    """Print a formatted processing message.

    Args:
        message: The message to print
        debug: Whether this is a debug message
    """
    if debug:
        console.print(f"[blue]DEBUG:[/blue] {message}")
    else:
        console.print(f"[green]INFO:[/green] {message}")
