"""Cache management for consolidate_markdown."""
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)

def quick_hash(content: str) -> str:
    """Fast MD5 hash of content."""
    return hashlib.md5(content.encode()).hexdigest()

class CacheManager:
    """Manages caching of processed files and GPT analyses."""

    def __init__(self, cm_dir: Path):
        """Initialize cache manager with .cm directory path."""
        self.cache_dir = cm_dir / "cache"
        self.notes_file = self.cache_dir / "notes.json"
        self.gpt_file = self.cache_dir / "gpt.json"
        self._init_cache()

    def _init_cache(self):
        """Create cache directory and files if they don't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize empty cache files if they don't exist
        if not self.notes_file.exists():
            self.notes_file.write_text("{}")
        if not self.gpt_file.exists():
            self.gpt_file.write_text("{}")

    def _load_cache(self, cache_file: Path) -> Dict:
        """Load a cache file, handling errors."""
        try:
            return json.loads(cache_file.read_text())
        except Exception as e:
            logger.warning(f"Failed to load cache {cache_file.name}, starting fresh: {e}")
            return {}

    def _save_cache(self, cache_file: Path, data: Dict):
        """Save cache data, handling errors."""
        try:
            cache_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save cache {cache_file.name}: {e}")

    def get_note_cache(self, note_path: str) -> Optional[dict]:
        """Get cached note info if it exists."""
        cache = self._load_cache(self.notes_file)
        # Normalize path for consistent lookup
        note_path = str(note_path).replace('\\', '/').replace('\n', '')
        return cache.get(note_path)

    def update_note_cache(self, note_path: str, content_hash: str, timestamp: float, gpt_analyses: int = 0, processed_content: Optional[str] = None):
        """Update note cache with new hash, timestamp, GPT analysis count and processed content."""
        cache = self._load_cache(self.notes_file)
        # Normalize path for consistent lookup
        note_path = str(note_path).replace('\\', '/').replace('\n', '')
        cache[note_path] = {
            "hash": content_hash,
            "timestamp": timestamp,
            "gpt_analyses": gpt_analyses,
            "processed_content": processed_content
        }
        self._save_cache(self.notes_file, cache)

    def get_gpt_cache(self, image_hash: str) -> Optional[str]:
        """Get cached GPT analysis if it exists."""
        cache = self._load_cache(self.gpt_file)
        return cache.get(image_hash)

    def update_gpt_cache(self, image_hash: str, analysis: str):
        """Cache GPT analysis result."""
        cache = self._load_cache(self.gpt_file)
        cache[image_hash] = analysis
        self._save_cache(self.gpt_file, cache)

    def clear_cache(self):
        """Clear all cache files (used by --force)."""
        logger.info("Clearing cache due to --force flag")
        self._save_cache(self.notes_file, {})
        self._save_cache(self.gpt_file, {})
