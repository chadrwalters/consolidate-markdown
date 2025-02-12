"""Initialize consolidate_markdown package."""

import warnings

# Configure warning filters for SWIG-related deprecation warnings
# These warnings come from importlib during module loading and are related to SWIG's limited API usage
# We need to filter them in multiple places since they can appear in different contexts
warnings.filterwarnings("ignore", message=".*builtin type SwigPyPacked has no __module__ attribute", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*builtin type SwigPyObject has no __module__ attribute", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*builtin type swigvarlink has no __module__ attribute", category=DeprecationWarning)

# Filter the same warnings when they come from specific modules
warnings.filterwarnings("ignore", message=".*builtin type swigvarlink has no __module__ attribute", category=DeprecationWarning, module="importlib._bootstrap")
warnings.filterwarnings("ignore", message=".*builtin type swigvarlink has no __module__ attribute", category=DeprecationWarning, module="sys")

from consolidate_markdown.processors.bear import BearProcessor
from consolidate_markdown.processors.xbookmarks import XBookmarksProcessor
from consolidate_markdown.runner import Runner

# Register processors
Runner.PROCESSORS["bear"] = BearProcessor
Runner.PROCESSORS["xbookmarks"] = XBookmarksProcessor
