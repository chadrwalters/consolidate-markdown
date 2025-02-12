"""Initialize consolidate_markdown package."""

import logging
import warnings
from typing import Dict, Type

from consolidate_markdown.processors.base import SourceProcessor
from consolidate_markdown.processors.bear import BearProcessor
from consolidate_markdown.processors.xbookmarks import XBookmarksProcessor
from consolidate_markdown.runner import Runner

# Configure warning filters for SWIG-related deprecation warnings
# These warnings come from importlib during module loading and are related to SWIG's limited API usage
# We need to filter them in multiple places since they can appear in different contexts
warnings.filterwarnings(
    "ignore",
    message=".*builtin type SwigPyPacked has no __module__ attribute",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*builtin type SwigPyObject has no __module__ attribute",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*builtin type swigvarlink has no __module__ attribute",
    category=DeprecationWarning,
)

# Filter the same warnings when they come from specific modules
warnings.filterwarnings(
    "ignore",
    message=".*builtin type swigvarlink has no __module__ attribute",
    category=DeprecationWarning,
    module="importlib._bootstrap",
)
warnings.filterwarnings(
    "ignore",
    message=".*builtin type swigvarlink has no __module__ attribute",
    category=DeprecationWarning,
    module="sys",
)

# Configure logging
logger = logging.getLogger(__name__)

# Define processor types
PROCESSOR_TYPES: Dict[str, Type[SourceProcessor]] = {}


def register_processor(name: str, processor_class: Type[SourceProcessor]) -> None:
    """Register a processor type."""
    PROCESSOR_TYPES[name] = processor_class


# Register processors
register_processor("bear", BearProcessor)
register_processor("xbookmarks", XBookmarksProcessor)

__all__ = [
    "SourceProcessor",
    "BearProcessor",
    "XBookmarksProcessor",
    "Runner",
    "PROCESSOR_TYPES",
    "register_processor",
]
