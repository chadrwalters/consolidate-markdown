"""Common utility functions for consolidate_markdown."""

import logging  # Standard library
import re  # Standard library
import shutil  # Standard library
import urllib.parse  # Standard library
from pathlib import Path  # Standard library
from typing import Any, Dict, List, Optional, Tuple, TypeVar  # Standard library

from .cache import CacheManager, quick_hash
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def normalize_path(path: str) -> str:
    """Normalize a path by converting to forward slashes and handling newlines.

    This method handles:
    - Windows-style paths (test\\note.md -> test/note.md)
    - Unix-style paths (test/note.md -> test/note.md)
    - Paths with newlines (test\nnote.md -> test/note.md)

    Args:
        path: The path to normalize

    Returns:
        Normalized path string
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


def should_process_from_cache(
    file_path: Path,
    content: str,
    cache_manager: CacheManager,
    force_generation: bool,
    attachment_dir: Optional[Path] = None,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Determine if a file should be processed or loaded from cache.

    Args:
        file_path: Path to the file
        content: Content of the file
        cache_manager: Cache manager instance
        force_generation: Whether to force regeneration
        attachment_dir: Optional directory containing attachments

    Returns:
        Tuple of (should_process, cached_data)
    """
    content_hash = quick_hash(content)
    cached = cache_manager.get_note_cache(str(file_path))

    should_process = True
    if cached and not force_generation:
        if cached["hash"] == content_hash:
            # Check for any newer files in the attachment directory
            if attachment_dir and attachment_dir.exists():
                latest_file = max(
                    attachment_dir.glob("*"),
                    key=lambda p: p.stat().st_mtime if p.is_file() else 0,
                    default=None,
                )
                if latest_file and latest_file.stat().st_mtime <= cached["timestamp"]:
                    should_process = False
            else:
                # No attachments directory = safe to use cache
                should_process = False

    return (should_process, cached)


def apply_limit(items: List[T], limit: Optional[int] = None) -> List[T]:
    """Apply a limit to a list of items.

    Args:
        items: List of items
        limit: Optional limit to apply

    Returns:
        Limited list of items
    """
    if limit is not None and limit > 0:
        return items[:limit]
    return items


def extract_url_from_markdown(markdown_link: str) -> Tuple[str, str]:
    """Extract alt text and URL from a markdown link.

    Args:
        markdown_link: Markdown link in format ![alt](url) or [alt](url)

    Returns:
        Tuple of (alt_text, url)
    """
    # Match both image and regular links
    match = re.match(r"!?\[(.*?)\]\((.*?)\)", markdown_link)
    if match:
        alt_text, url = match.groups()
        # URL decode the path
        decoded_url = urllib.parse.unquote(url)
        return alt_text, decoded_url
    return "", ""


def ensure_directory(directory: Path) -> None:
    """Ensure a directory exists.

    Args:
        directory: Directory path to ensure exists
    """
    directory.mkdir(parents=True, exist_ok=True)


def check_command_exists(command: str) -> bool:
    """Check if a command exists in the system PATH.

    Args:
        command: The command to check

    Returns:
        True if the command exists, False otherwise
    """
    result = shutil.which(command) is not None
    logger.debug(f"Command check: {command} - {'Found' if result else 'Not found'}")
    return result


def validate_external_dependencies() -> None:
    """Validate that all required external dependencies are installed.

    This function checks for the presence of external command-line tools
    that are required by the application. It raises a DependencyError
    if any required dependency is missing.

    Raises:
        DependencyError: If a required dependency is missing
    """
    logger.debug("Validating external dependencies...")
    # Define required and optional dependencies
    image_converters = {
        "rsvg-convert": "SVG conversion (librsvg)",
        "inkscape": "SVG conversion (alternative)",
        "magick": "Image conversion (ImageMagick)",
        "sips": "Image conversion on macOS",
        "heif-convert": "HEIC conversion on Linux",
    }

    # Check for at least one SVG converter
    svg_converter_found = False
    for converter in ["rsvg-convert", "inkscape"]:
        if check_command_exists(converter):
            svg_converter_found = True
            logger.debug(f"Found SVG converter: {converter}")
            break

    if not svg_converter_found:
        logger.warning(
            "No SVG converter found. SVG files will not be processed correctly."
        )
        logger.warning("Please install librsvg (rsvg-convert) or Inkscape.")

    # Check for at least one image converter
    image_converter_found = False
    for converter in ["magick", "sips", "heif-convert"]:
        if check_command_exists(converter):
            image_converter_found = True
            logger.debug(f"Found image converter: {converter}")
            break

    if not image_converter_found:
        logger.warning(
            "No image converter found. HEIC and some image formats may not be processed correctly."
        )
        logger.warning("Please install ImageMagick or platform-specific tools.")

    logger.debug("External dependency validation complete")


def validate_api_keys(config: Any) -> None:
    """Validate that required API keys are present and well-formed.

    Args:
        config: The application configuration

    Raises:
        ConfigurationError: If a required API key is missing or malformed
    """
    logger.debug("Validating API keys...")
    # Check OpenAI API key if OpenAI is enabled
    if hasattr(config, "global_config"):
        if config.global_config.api_provider == "openai":
            logger.debug("API provider is OpenAI, checking for OpenAI API key")
            openai_key = config.global_config.openai_key
            if not openai_key and not config.global_config.no_image:
                logger.warning(
                    "OpenAI API key is missing but image processing is enabled."
                )
                logger.warning(
                    "Set OPENAI_API_KEY environment variable or add to config.toml."
                )
            elif openai_key and len(openai_key) < 20:  # Simple length check
                raise ConfigurationError(
                    "OpenAI API key appears to be malformed or truncated."
                )
            else:
                logger.debug("OpenAI API key validation successful")

        # Check OpenRouter API key if OpenRouter is enabled
        elif config.global_config.api_provider == "openrouter":
            logger.debug("API provider is OpenRouter, checking for OpenRouter API key")
            openrouter_key = config.global_config.openrouter_key
            if not openrouter_key and not config.global_config.no_image:
                logger.warning(
                    "OpenRouter API key is missing but image processing is enabled."
                )
                logger.warning(
                    "Set OPENROUTER_API_KEY environment variable or add to config.toml."
                )
            elif openrouter_key and len(openrouter_key) < 20:  # Simple length check
                raise ConfigurationError(
                    "OpenRouter API key appears to be malformed or truncated."
                )
            else:
                logger.debug("OpenRouter API key validation successful")
        else:
            logger.debug(
                f"API provider is {config.global_config.api_provider}, no API key validation needed"
            )
    else:
        logger.debug(
            "Config does not have global_config attribute, skipping API key validation"
        )

    logger.debug("API key validation complete")
