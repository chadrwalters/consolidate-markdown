"""Cache management for consolidate_markdown."""

import hashlib
import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional, cast

logger = logging.getLogger(__name__)


def quick_hash(content: str) -> str:
    """Fast MD5 hash of content."""
    return hashlib.md5(content.encode()).hexdigest()


class CacheManager:
    """Manages caching of processed files and GPT analyses."""

    def __init__(self, cm_dir: Path) -> None:
        """Initialize cache manager with .cm directory path."""
        self.cache_dir = cm_dir / "cache"
        self.notes_file = self.cache_dir / "notes.json"
        self.gpt_file = self.cache_dir / "gpt.json"
        self.notes_lock = threading.Lock()
        self.gpt_lock = threading.Lock()
        self._init_cache()

    def _init_cache(self) -> None:
        """Create cache directory and files if they don't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize empty cache files if they don't exist
        if not self.notes_file.exists():
            self.notes_file.write_text("{}")
        if not self.gpt_file.exists():
            self.gpt_file.write_text("{}")

    def _load_cache(self, cache_file: Path) -> Dict[str, Any]:
        """Load a cache file, handling errors."""
        try:
            cache_data = cast(Dict[str, Any], json.loads(cache_file.read_text()))
            logger.debug(
                f"Loaded cache from {cache_file.name} ({len(cache_data)} entries)"
            )
            return cache_data
        except Exception as e:
            logger.warning(
                f"Failed to load cache {cache_file.name}, starting fresh: {e}"
            )
            return {}

    def _save_cache(self, cache_file: Path, data: Dict) -> None:
        """Save cache data, handling errors."""
        try:
            cache_file.write_text(json.dumps(data, indent=2))
            logger.debug(f"Saved cache to {cache_file.name} ({len(data)} entries)")
        except Exception as e:
            logger.error(f"Failed to save cache {cache_file.name}: {e}")

    def _normalize_path(self, path: str) -> str:
        """Normalize a path by converting to forward slashes and handling newlines.

        This method handles:
        - Windows-style paths (test\\note.md -> test/note.md)
        - Unix-style paths (test/note.md -> test/note.md)
        - Paths with newlines (test\nnote.md -> test/note.md)
        """
        # Convert the path to a string
        path = str(path)

        # Replace actual newlines with forward slashes
        path = path.replace("\n", "/")

        # Replace any backslashes with forward slashes
        path = path.replace("\\", "/")

        # Clean up any double slashes
        while "//" in path:
            path = path.replace("//", "/")

        return path

    def get_note_cache(self, note_path: str) -> Optional[dict]:
        """Get cached note info if it exists."""
        with self.notes_lock:
            cache = self._load_cache(self.notes_file)
            normalized_path = self._normalize_path(note_path)
            result = cache.get(normalized_path)
            if result is None:
                logger.debug(f"Cache miss for note: {normalized_path}")
            else:
                logger.debug(f"Cache hit for note: {normalized_path}")
            return result

    def update_note_cache(
        self,
        note_path: str,
        content_hash: str,
        timestamp: float,
        gpt_analyses: int = 0,
        processed_content: Optional[str] = None,
    ) -> None:
        """Update note cache with new hash, timestamp, GPT analysis count and processed content."""
        with self.notes_lock:
            cache = self._load_cache(self.notes_file)
            normalized_path = self._normalize_path(note_path)
            logger.debug(f"Updating cache for note: {normalized_path}")
            cache[normalized_path] = {
                "hash": content_hash,
                "timestamp": timestamp,
                "gpt_analyses": gpt_analyses,
                "processed_content": processed_content,
            }
            self._save_cache(self.notes_file, cache)

    def get_gpt_cache(self, image_hash: str) -> Optional[str]:
        """Get cached GPT analysis if it exists."""
        with self.gpt_lock:
            cache = self._load_cache(self.gpt_file)
            result = cache.get(image_hash)
            if result is None:
                logger.debug(f"Cache miss for GPT analysis: {image_hash}")
            else:
                logger.debug(f"Cache hit for GPT analysis: {image_hash}")
            return result

    def update_gpt_cache(self, image_hash: str, analysis: str) -> None:
        """Cache GPT analysis result."""
        with self.gpt_lock:
            cache = self._load_cache(self.gpt_file)
            logger.debug(f"Updating GPT analysis cache: {image_hash}")
            cache[image_hash] = analysis
            self._save_cache(self.gpt_file, cache)

    def clear_cache(self) -> None:
        """Clear all cache files (used by --force)."""
        logger.info("Clearing cache due to --force flag")
        with self.notes_lock:
            self._save_cache(self.notes_file, {})
        with self.gpt_lock:
            self._save_cache(self.gpt_file, {})
