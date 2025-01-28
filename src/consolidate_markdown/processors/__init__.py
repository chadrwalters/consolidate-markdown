"""Processor package initialization."""

from .base import ProcessingResult, SourceProcessor
from .bear import BearProcessor
from .xbookmarks import XBookmarksProcessor

__all__ = [
    "ProcessingResult",
    "SourceProcessor",
    "BearProcessor",
    "XBookmarksProcessor",
]
