"""Source processors package."""

from .base import SourceProcessor
from .bear import BearProcessor
from .chatgpt import ChatGPTProcessor
from .claude import ClaudeProcessor
from .result import ProcessingResult
from .xbookmarks import XBookmarksProcessor

PROCESSOR_TYPES = {
    "bear": BearProcessor,
    "xbookmarks": XBookmarksProcessor,
    "claude": ClaudeProcessor,
    "chatgpt": ChatGPTProcessor,
}

__all__ = [
    "BearProcessor",
    "ChatGPTProcessor",
    "ClaudeProcessor",
    "ProcessingResult",
    "SourceProcessor",
    "XBookmarksProcessor",
]
