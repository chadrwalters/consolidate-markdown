"""Initialize consolidate_markdown package."""

from consolidate_markdown.processors.bear import BearProcessor
from consolidate_markdown.processors.xbookmarks import XBookmarksProcessor
from consolidate_markdown.runner import Runner

# Register processors
Runner.PROCESSORS["bear"] = BearProcessor
Runner.PROCESSORS["xbookmarks"] = XBookmarksProcessor
