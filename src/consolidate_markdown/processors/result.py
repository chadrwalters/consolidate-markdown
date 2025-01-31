"""Processing result tracking."""

from typing import List


class ProcessingResult:
    """Track results of processing a set of notes."""

    def __init__(self):
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

    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)

    def merge(self, other: "ProcessingResult"):
        """Merge another result into this one."""
        self.processed += other.processed
        self.from_cache += other.from_cache
        self.regenerated += other.regenerated
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

    def add_from_cache(self):
        """Record a note loaded from cache."""
        self.processed += 1
        self.from_cache += 1

    def add_generated(self):
        """Record a generated note."""
        self.processed += 1
        self.regenerated += 1

    def add_skipped(self):
        """Record a skipped note."""
        self.skipped += 1

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
