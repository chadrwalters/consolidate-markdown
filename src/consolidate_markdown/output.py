import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .processors.result import ProcessingResult

logger = logging.getLogger(__name__)

# Global console instance for consistent styling
console = Console()

# Define ordered processors for consistent display
ORDERED_PROCESSORS = ["bear", "xbookmarks", "claude"]

# Define metric rows for summary table with grouping
METRIC_ROWS = [
    # Overall stats
    ("Total Processed", lambda r: r.processed),
    ("Generated", lambda r: r.regenerated),
    ("From Cache", lambda r: r.from_cache),
    ("Skipped", lambda r: r.skipped),
    ("", lambda r: ""),  # Separator
    # Document stats
    ("Docs Processed", lambda r: r.documents_processed),
    ("Docs Generated", lambda r: r.documents_generated),
    ("Docs From Cache", lambda r: r.documents_from_cache),
    ("Docs Skipped", lambda r: r.documents_skipped),
    ("", lambda r: ""),  # Separator
    # Image stats
    ("Images Processed", lambda r: r.images_processed),
    ("Images Generated", lambda r: r.images_generated),
    ("Images From Cache", lambda r: r.images_from_cache),
    ("Images Skipped", lambda r: r.images_skipped),
    ("", lambda r: ""),  # Separator
    # GPT stats
    ("GPT Processed", lambda r: r.gpt_cache_hits + r.gpt_new_analyses),
    ("GPT Generated", lambda r: r.gpt_new_analyses),
    ("GPT From Cache", lambda r: r.gpt_cache_hits),
    ("GPT Skipped", lambda r: r.gpt_skipped),
]


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
    # Create main summary table with double-line style for better separation
    table = Table(show_header=True, header_style="bold cyan", box=box.DOUBLE)
    table.add_column("Metric", justify="left", style="bold")

    # Add processor columns
    for proc in ORDERED_PROCESSORS:
        display_name = (
            "Bear Notes"
            if proc == "bear"
            else (
                "X Bookmarks"
                if proc == "xbookmarks"
                else "Claude" if proc == "claude" else proc.title()
            )
        )
        table.add_column(display_name, justify="right")

    # Add metric rows with style for separators
    for label, extractor in METRIC_ROWS:
        if not label:  # It's a separator row
            table.add_row(*[""] * (len(ORDERED_PROCESSORS) + 1), style="dim")
            continue
        row = [label]
        for proc in ORDERED_PROCESSORS:
            # Get processor stats if available
            proc_stats = result.processor_stats.get(proc)
            value = extractor(proc_stats) if proc_stats else 0
            # Format value with commas for thousands
            row.append(format_count(value))
        table.add_row(*row)

    # Create and display summary panel with padding
    summary_panel = Panel(
        table,
        title="[bold green]Consolidation Summary[/bold green]",
        expand=False,
        padding=(1, 2),  # Add padding inside panel
    )
    console.print("\n")  # Add space before panel
    console.print(summary_panel)
    console.print("\n")  # Add space after panel

    # Display errors if any
    error_lines = []
    for proc in ORDERED_PROCESSORS:
        proc_stats = result.processor_stats.get(proc)
        if proc_stats and proc_stats.errors:
            error_lines.append(f"[bold red]{proc.title()} Errors:[/bold red]")
            for err in proc_stats.errors:
                error_lines.append(f" • {err}")
            error_lines.append("")

    # Add any unassociated errors
    unassociated_errors = [
        err
        for err in result.errors
        if not any(err in stats.errors for stats in result.processor_stats.values())
    ]
    if unassociated_errors:
        error_lines.append("[bold red]General Errors:[/bold red]")
        for err in unassociated_errors:
            error_lines.append(f" • {err}")
        error_lines.append("")

    if error_lines:
        error_panel = Panel(
            "\n".join(error_lines),
            title="[bold red]Errors Detected[/bold red]",
            border_style="red",
            expand=False,
            padding=(1, 2),  # Add padding inside panel
        )
        console.print(error_panel)
    else:
        console.print("[bold green]No errors detected.[/bold green]")


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
