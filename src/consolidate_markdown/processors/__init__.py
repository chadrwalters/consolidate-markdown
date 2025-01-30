"""Source processors package."""

from .base import SourceProcessor
from .bear import BearProcessor
from .chatgpt import ChatGPTProcessor
from .result import ProcessingResult
from .xbookmarks import XBookmarksProcessor

PROCESSOR_TYPES = {
    "bear": BearProcessor,
    "chatgptexport": ChatGPTProcessor,
    "xbookmarks": XBookmarksProcessor,
}

__all__ = [
    "BearProcessor",
    "ChatGPTProcessor",
    "ProcessingResult",
    "SourceProcessor",
    "XBookmarksProcessor",
]
