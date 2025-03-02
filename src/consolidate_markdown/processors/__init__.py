"""Source processors package."""

from .base import SourceProcessor
from .bear import BearProcessor
from .claude import ClaudeProcessor
from .result import ProcessingResult
from .xbookmarks import XBookmarksProcessor

PROCESSOR_TYPES = {
    "bear": BearProcessor,
    "xbookmarks": XBookmarksProcessor,
    "claude": ClaudeProcessor,
}

__all__ = [
    "BearProcessor",
    "ClaudeProcessor",
    "ProcessingResult",
    "SourceProcessor",
    "XBookmarksProcessor",
]
