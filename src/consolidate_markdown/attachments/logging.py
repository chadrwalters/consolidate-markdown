"""Logging utilities for attachment processing."""

import logging
from pathlib import Path
from typing import Optional, Union

# Create a dedicated logger for attachment processing
attachment_logger = logging.getLogger("consolidate_markdown.attachments")


def setup_attachment_logging(log_level: Union[str, int] = logging.DEBUG) -> None:
    """Set up enhanced logging for attachment processing.

    Args:
        log_level: The logging level to use for attachment processing
    """
    # Set the level for the attachment logger
    attachment_logger.setLevel(log_level)

    # Make sure the logger propagates to the root logger
    attachment_logger.propagate = True

    # Log that attachment logging has been configured
    attachment_logger.debug("Attachment logging configured successfully")


def log_file_search(file_id: str, search_dir: Path, matches: list[Path]) -> None:
    """Log information about file search operations.

    Args:
        file_id: The file ID being searched for
        search_dir: The directory being searched
        matches: The list of matching files found
    """
    attachment_logger.debug(f"Searching for file ID: {file_id} in {search_dir}")
    attachment_logger.debug(f"Directory exists: {search_dir.exists()}")

    if matches:
        attachment_logger.debug(f"Found {len(matches)} matches in {search_dir}")
        attachment_logger.debug(f"Matches: {[str(m) for m in matches]}")
    else:
        attachment_logger.debug(f"No matches found in {search_dir}")


def log_file_processing(file_path: Path, file_type: str, exists: bool = True) -> None:
    """Log information about file processing.

    Args:
        file_path: The path to the file being processed
        file_type: The type of file (e.g., 'image', 'audio', 'document')
        exists: Whether the file exists
    """
    attachment_logger.debug(f"Processing {file_type} file: {file_path}")
    attachment_logger.debug(f"File exists: {exists}")

    if not exists:
        attachment_logger.warning(
            f"{file_type.capitalize()} file not found: {file_path}"
        )


def log_media_processing_error(file_path: Path, error_msg: str, file_type: str) -> None:
    """Log detailed information about media processing errors.

    Args:
        file_path: The path to the file that had an error
        error_msg: The error message
        file_type: The type of file (e.g., 'image', 'audio', 'document')
    """
    attachment_logger.error(
        f"Error processing {file_type} file {file_path}: {error_msg}", exc_info=True
    )


def log_dalle_processing(file_id: str, dalle_dir: Path, matches: list[Path]) -> None:
    """Log detailed information about DALL-E image processing.

    Args:
        file_id: The file ID being searched for
        dalle_dir: The DALL-E directory being searched
        matches: The list of matching files found
    """
    attachment_logger.debug(f"Processing DALL-E image with ID: {file_id}")
    attachment_logger.debug(f"DALL-E directory: {dalle_dir}")
    attachment_logger.debug(f"DALL-E directory exists: {dalle_dir.exists()}")

    if matches:
        attachment_logger.debug(f"Found {len(matches)} DALL-E matches")
        attachment_logger.debug(f"DALL-E matches: {[str(m) for m in matches]}")
    else:
        attachment_logger.debug(f"No DALL-E matches found for ID: {file_id}")


def log_wav_processing(
    file_path: Path, success: bool, error_msg: Optional[str] = None
) -> None:
    """Log detailed information about WAV file processing.

    Args:
        file_path: The path to the WAV file
        success: Whether processing was successful
        error_msg: Optional error message if processing failed
    """
    attachment_logger.debug(f"Processing WAV file: {file_path}")

    if success:
        attachment_logger.debug(f"Successfully processed WAV file: {file_path}")
    else:
        attachment_logger.error(
            f"Failed to process WAV file {file_path}: {error_msg}", exc_info=True
        )
