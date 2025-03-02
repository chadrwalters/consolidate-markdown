"""Processing result tracking."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ProcessorStats:
    """Statistics for a single processor."""

    processed: int = 0
    from_cache: int = 0
    regenerated: int = 0
    skipped: int = 0
    documents_processed: int = 0
    documents_generated: int = 0
    documents_from_cache: int = 0
    documents_skipped: int = 0
    images_processed: int = 0
    images_generated: int = 0
    images_from_cache: int = 0
    images_skipped: int = 0
    gpt_cache_hits: int = 0
    gpt_new_analyses: int = 0
    gpt_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    processor_type: Optional[str] = None

    def merge(self, other: "ProcessorStats") -> None:
        """Merge another processor's stats into this one."""
        # If all items in either result are from cache, set regenerated to 0
        if (self.from_cache > 0 and self.from_cache == self.processed) or (
            other.from_cache > 0 and other.from_cache == other.processed
        ):
            self.regenerated = 0
        # If this result has no items yet, copy the regenerated count
        elif self.processed == 0:
            self.regenerated = other.regenerated
        # Otherwise, only add regenerated if the other result has no cached items
        elif other.from_cache == 0:
            self.regenerated += other.regenerated

        self.processed += other.processed
        self.from_cache += other.from_cache
        self.skipped += other.skipped
        self.documents_processed += other.documents_processed
        self.documents_generated += other.documents_generated
        self.documents_from_cache += other.documents_from_cache
        self.documents_skipped += other.documents_skipped
        self.images_processed += other.images_processed
        self.images_generated += other.images_generated
        self.images_from_cache += other.images_from_cache
        self.images_skipped += other.images_skipped
        self.gpt_cache_hits += other.gpt_cache_hits
        self.gpt_new_analyses += other.gpt_new_analyses
        self.gpt_skipped += other.gpt_skipped
        self.errors.extend(other.errors)
        if other.processor_type:
            self.processor_type = other.processor_type


class ProcessingResult:
    """Track results of processing a set of notes."""

    def __init__(self) -> None:
        """Initialize empty result."""
        self.processed = 0
        self.from_cache = 0
        self.regenerated = 0
        self.skipped = 0
        self.documents_processed = 0
        self.documents_generated = 0
        self.documents_from_cache = 0
        self.documents_skipped = 0
        self.images_processed = 0
        self.images_generated = 0
        self.images_from_cache = 0
        self.images_skipped = 0
        self.gpt_cache_hits = 0
        self.gpt_new_analyses = 0
        self.gpt_skipped = 0
        self.errors: List[str] = []
        self.processor_stats: Dict[str, ProcessorStats] = {}
        self.last_action: str = ""

    def get_processor_stats(self, processor_type: str) -> ProcessorStats:
        """Get or create stats for a processor type.

        Args:
            processor_type: The type of processor

        Returns:
            The processor's stats
        """
        if processor_type not in self.processor_stats:
            stats = ProcessorStats()
            stats.processor_type = processor_type
            self.processor_stats[processor_type] = stats
        return self.processor_stats[processor_type]

    def add_error(self, error: str, processor_type: Optional[str] = None) -> None:
        """Add an error message.

        This method adds an error message to the result and optionally associates it
        with a specific processor type. It formats the error message to be more
        user-friendly by removing excessive technical details when displayed to users.

        Args:
            error: The error message
            processor_type: Optional processor type to associate with the error
        """
        # Format the error message to be more user-friendly
        user_friendly_error = self._format_error_for_user(error)

        # Add to global errors list
        self.errors.append(user_friendly_error)

        # Add to processor-specific errors if processor_type is provided
        if processor_type:
            self.get_processor_stats(processor_type).errors.append(user_friendly_error)

    def _format_error_for_user(self, error: str) -> str:
        """Format an error message to be more user-friendly.

        This method processes error messages to make them more readable and
        actionable for users by:
        1. Removing excessive stack traces
        2. Providing context about the error type
        3. Suggesting possible solutions when applicable

        Args:
            error: The original error message

        Returns:
            A user-friendly formatted error message
        """
        # Truncate very long error messages
        if len(error) > 500:
            error = error[:497] + "..."

        # Check for common error patterns and provide more helpful messages
        if "API key" in error.lower() or "apikey" in error.lower():
            return f"API Key Error: {error} - Please check your API key configuration in config.toml or environment variables."

        if "permission" in error.lower() or "access denied" in error.lower():
            return (
                f"Permission Error: {error} - Please check file/directory permissions."
            )

        if "not found" in error.lower() or "no such file" in error.lower():
            return f"File Not Found: {error} - Please verify the file path exists."

        if "timeout" in error.lower() or "timed out" in error.lower():
            return f"Timeout Error: {error} - The operation took too long to complete. Try again or check your network connection."

        if "network" in error.lower() or "connection" in error.lower():
            return f"Network Error: {error} - Please check your internet connection."

        if "command" in error.lower() and (
            "not found" in error.lower() or "missing" in error.lower()
        ):
            return f"Missing Dependency: {error} - Please install the required external tool."

        # If no specific pattern matches, return the original error with a generic prefix
        return f"Error: {error}"

    def merge(self, other: "ProcessingResult") -> None:
        """Merge another result into this one.

        Args:
            other: The result to merge
        """
        # If all items in either result are from cache, set regenerated to 0
        if (self.from_cache > 0 and self.from_cache == self.processed) or (
            other.from_cache > 0 and other.from_cache == other.processed
        ):
            self.regenerated = 0
        # If this result has no items yet, copy the regenerated count
        elif self.processed == 0:
            self.regenerated = other.regenerated
        # Otherwise, only add regenerated if the other result has no cached items
        elif other.from_cache == 0:
            self.regenerated += other.regenerated

        self.processed += other.processed
        self.from_cache += other.from_cache
        self.skipped += other.skipped
        self.documents_processed += other.documents_processed
        self.documents_generated += other.documents_generated
        self.documents_from_cache += other.documents_from_cache
        self.documents_skipped += other.documents_skipped
        self.images_processed += other.images_processed
        self.images_generated += other.images_generated
        self.images_from_cache += other.images_from_cache
        self.images_skipped += other.images_skipped
        self.gpt_cache_hits += other.gpt_cache_hits
        self.gpt_new_analyses += other.gpt_new_analyses
        self.gpt_skipped += other.gpt_skipped
        self.errors.extend(other.errors)

        # Merge processor stats
        for proc_type, stats in other.processor_stats.items():
            if proc_type in self.processor_stats:
                self.processor_stats[proc_type].merge(stats)
            else:
                self.processor_stats[proc_type] = stats

    def add_from_cache(self, processor_type: str) -> None:
        """Record a note loaded from cache.

        Args:
            processor_type: The type of processor that processed the note
        """
        self.from_cache += 1
        self.regenerated = 0  # Reset regenerated counter for cached items
        stats = self.get_processor_stats(processor_type)
        stats.processed += 1
        stats.from_cache += 1
        stats.regenerated = 0  # Reset regenerated counter in processor stats too
        self.last_action = "from_cache"

    def add_generated(self, processor_type: str) -> None:
        """Record a generated note.

        Args:
            processor_type: The type of processor that generated the note
        """
        self.regenerated += 1  # Increment instead of setting to 1
        stats = self.get_processor_stats(processor_type)
        stats.processed += 1
        stats.regenerated += 1  # Increment regenerated in processor stats too
        self.last_action = "generated"

    def add_skipped(self, processor_type: str) -> None:
        """Record a skipped note.

        Args:
            processor_type: The type of processor that skipped the note
        """
        self.skipped += 1
        stats = self.get_processor_stats(processor_type)
        stats.skipped += 1
        self.last_action = "skipped"

    def add_document_generated(self, processor_type: str) -> None:
        """Record a generated document.

        Args:
            processor_type: The type of processor that generated the document
        """
        self.documents_processed += 1
        self.documents_generated += 1
        stats = self.get_processor_stats(processor_type)
        stats.documents_processed += 1
        stats.documents_generated += 1

    def add_document_from_cache(self, processor_type: str) -> None:
        """Record a document loaded from cache.

        Args:
            processor_type: The type of processor that loaded the document
        """
        self.documents_processed += 1
        self.documents_from_cache += 1
        stats = self.get_processor_stats(processor_type)
        stats.documents_processed += 1
        stats.documents_from_cache += 1

    def add_document_skipped(self, processor_type: str) -> None:
        """Record a skipped document.

        Args:
            processor_type: The type of processor that skipped the document
        """
        self.documents_skipped += 1
        stats = self.get_processor_stats(processor_type)
        stats.documents_skipped += 1

    def add_image_generated(self, processor_type: str) -> None:
        """Record a generated image.

        Args:
            processor_type: The type of processor that generated the image
        """
        self.images_processed += 1
        self.images_generated += 1
        stats = self.get_processor_stats(processor_type)
        stats.images_processed += 1
        stats.images_generated += 1

    def add_image_from_cache(self, processor_type: str) -> None:
        """Record an image loaded from cache.

        Args:
            processor_type: The type of processor that loaded the image
        """
        self.images_processed += 1
        self.images_from_cache += 1
        stats = self.get_processor_stats(processor_type)
        stats.images_processed += 1
        stats.images_from_cache += 1

    def add_image_skipped(self, processor_type: str) -> None:
        """Record a skipped image.

        Args:
            processor_type: The type of processor that skipped the image
        """
        self.images_skipped += 1
        stats = self.get_processor_stats(processor_type)
        stats.images_skipped += 1

    def add_gpt_generated(self, processor_type: str) -> None:
        """Record a generated GPT analysis.

        Args:
            processor_type: The type of processor that generated the analysis
        """
        self.gpt_new_analyses += 1
        stats = self.get_processor_stats(processor_type)
        stats.gpt_new_analyses += 1

    def add_gpt_from_cache(self, processor_type: str) -> None:
        """Record a GPT analysis loaded from cache.

        Args:
            processor_type: The type of processor that loaded the analysis
        """
        self.gpt_cache_hits += 1
        stats = self.get_processor_stats(processor_type)
        stats.gpt_cache_hits += 1

    def add_gpt_skipped(self, processor_type: str) -> None:
        """Record a skipped GPT analysis.

        Args:
            processor_type: The type of processor that skipped the analysis
        """
        self.gpt_skipped += 1
        stats = self.get_processor_stats(processor_type)
        stats.gpt_skipped += 1

    def __str__(self) -> str:
        """Return string representation."""
        parts = []

        # Core processing stats
        if self.processed > 0:
            parts.append(f"{self.processed} processed")
            if self.from_cache > 0:
                parts.append(f"{self.from_cache} from cache")
            if self.regenerated > 0:
                parts.append(f"{self.regenerated} generated")
        if self.skipped > 0:
            parts.append(f"{self.skipped} skipped")

        # Document stats
        if self.documents_processed > 0:
            doc_parts = []
            doc_parts.append(f"{self.documents_processed} documents processed")
            if self.documents_from_cache > 0:
                doc_parts.append(f"{self.documents_from_cache} from cache")
            if self.documents_generated > 0:
                doc_parts.append(f"{self.documents_generated} generated")
            if self.documents_skipped > 0:
                doc_parts.append(f"{self.documents_skipped} skipped")
            parts.append(" (".join(doc_parts) + ")")

        # Image stats
        if self.images_processed > 0:
            img_parts = []
            img_parts.append(f"{self.images_processed} images processed")
            if self.images_from_cache > 0:
                img_parts.append(f"{self.images_from_cache} from cache")
            if self.images_generated > 0:
                img_parts.append(f"{self.images_generated} generated")
            if self.images_skipped > 0:
                img_parts.append(f"{self.images_skipped} skipped")
            parts.append(" (".join(img_parts) + ")")

        # GPT analysis stats
        if self.gpt_cache_hits > 0 or self.gpt_new_analyses > 0 or self.gpt_skipped > 0:
            gpt_parts = []
            if self.gpt_cache_hits > 0:
                gpt_parts.append(f"{self.gpt_cache_hits} GPT analyses from cache")
            if self.gpt_new_analyses > 0:
                gpt_parts.append(f"{self.gpt_new_analyses} new GPT analyses")
            if self.gpt_skipped > 0:
                gpt_parts.append(f"{self.gpt_skipped} GPT analyses skipped")
            parts.append(" (".join(gpt_parts) + ")")

        # Error summary
        if self.errors:
            parts.append(f"{len(self.errors)} errors")

        return ", ".join(parts) if parts else "No results"
