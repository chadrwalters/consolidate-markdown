"""ChatGPT conversation export processor.

This module provides a processor for ChatGPT conversation exports, converting them
into markdown files while efficiently handling large JSON files and attachments.

Key features:
- Streaming JSON parsing for memory-efficient processing of large files
- Tree reconstruction of conversations from parent-child relationships
- Comment-based attachment handling without creating physical attachment files
- Caching to avoid reprocessing unchanged conversations
- Flat output directory structure with only markdown files
"""

import json
import logging
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, cast

import ijson  # type: ignore
from rich.progress import Progress, TaskID

from ..attachments.processor import AttachmentProcessor
from ..cache import CacheManager
from ..config import Config, SourceConfig
from .base import AttachmentHandlerMixin, SourceProcessor
from .result import ProcessingResult

logger = logging.getLogger(__name__)


class ChatGPTProcessor(SourceProcessor, AttachmentHandlerMixin):
    """Process ChatGPT conversation exports into Markdown.

    This processor handles ChatGPT exports, which contain large JSON files with
    conversation data and image attachments. It uses streaming JSON parsing to
    efficiently process large files without loading them entirely into memory.

    The processor generates a flat output directory structure with only markdown files.
    Attachments are not copied to the output directory; instead, information about
    attachments is embedded as comments in the markdown output.

    Key features:
    - Streaming JSON parsing using ijson for memory-efficient processing
    - Tree reconstruction of conversations from parent-child relationships
    - Handling of image attachments referenced by asset pointers
    - Integration with the caching system to avoid reprocessing unchanged conversations
    - Progress reporting for both individual conversations and the overall process

    The comment format for images is:
    ```
    <!-- ATTACHMENT: IMAGE: filename.jpg (dimensions, size) -->
    <!-- GPT Description: description text -->
    ![description]()
    ```

    Configuration options:
    - source_dir: Directory containing ChatGPT export files
    - dest_dir: Directory where markdown files will be created
    - no_image: Whether to skip GPT image description generation
    - cache: Whether to use caching to avoid reprocessing unchanged files
    """

    def __init__(
        self, source_config: SourceConfig, cache_manager: Optional[CacheManager] = None
    ):
        """Initialize processor with source configuration."""
        # Initialize instance variables before calling super().__init__
        self._temp_dir = None
        super().__init__(source_config, cache_manager)

    @property
    def attachment_processor(self) -> AttachmentProcessor:
        """Get the attachment processor instance."""
        if self._attachment_processor is None:
            self._attachment_processor = AttachmentProcessor(
                self.source_config.dest_dir
            )
        return self._attachment_processor

    @property
    def _processor_type(self) -> str:
        """Get the processor type for the AttachmentHandlerMixin.

        Returns:
            The processor type string
        """
        return "chatgpt"

    def validate(self) -> None:
        """Validate source configuration.

        Raises:
            ValueError: If source configuration is invalid.
        """
        super().validate()

        # Check if the source directory exists
        if not self.source_config.src_dir.exists():
            raise ValueError(
                f"Source directory does not exist: {self.source_config.src_dir}"
            )

        # Check if the source directory contains expected files
        # For ChatGPT exports, we expect at least one conversation.json file
        # This could be in the root directory or in subdirectories
        has_conversation_files = False

        # Check root directory
        if (self.source_config.src_dir / "conversations.json").exists():
            has_conversation_files = True
        else:
            # Check subdirectories for conversation.json files
            for path in self.source_config.src_dir.glob("**/conversation.json"):
                has_conversation_files = True
                break

        if not has_conversation_files:
            raise ValueError(
                f"Source directory does not contain any ChatGPT conversation files: {self.source_config.src_dir}"
            )

    def _get_output_path(self, metadata: Dict[str, Any]) -> Path:
        """Generate output path for a conversation.

        Args:
            metadata: The conversation metadata.

        Returns:
            Path to save the markdown file.
        """
        # Extract title and creation date from metadata
        title = metadata.get("title", "Untitled")
        created_at = metadata.get("create_time")

        # Format the filename
        if created_at:
            try:
                # Parse the date from timestamp
                date = datetime.fromtimestamp(created_at)
                # Format as YYYYMMDD
                date_prefix = date.strftime("%Y%m%d")
            except (ValueError, TypeError):
                date_prefix = "00000000"  # Use placeholder for invalid dates
        else:
            date_prefix = "00000000"  # Use placeholder for missing dates

        # Clean the title for use in filename
        filename = title.strip()
        if not filename:
            filename = "Untitled"

        # Replace problematic characters and handle unicode
        filename = re.sub(r'[<>:"/\\|?*#]', "_", filename)  # Replace special chars
        filename = re.sub(r"[/\\]", "_", filename)  # Handle path separators
        filename = re.sub(r"\s+", "_", filename)  # Replace whitespace with underscore

        # Handle unicode characters - keep alphanumeric and common symbols
        clean_filename = ""
        for c in filename:
            cat = unicodedata.category(c)
            # Keep letters, numbers, dashes, underscores, and some punctuation
            if cat.startswith(("L", "N")) or c in "_-":
                clean_filename += c
            # Replace other characters with underscore
            else:
                clean_filename += "_"

        # Truncate if too long
        if len(clean_filename) > 100:
            clean_filename = clean_filename[:100]

        # Combine date and title
        full_filename = f"{date_prefix}_{clean_filename}.md"

        # Return the full path
        return self.source_config.dest_dir / full_filename

    def _load_metadata(self, metadata_path: Path) -> Dict[str, Any]:
        """Load metadata from a metadata.json file.

        Args:
            metadata_path: Path to the metadata.json file.

        Returns:
            Dictionary containing metadata.
        """
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return cast(Dict[str, Any], json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load metadata from {metadata_path}: {str(e)}")
            return {}

    def _parse_conversation_json(self, file_path: Path) -> Dict[str, Any]:
        """Parse a conversation.json file using streaming JSON parser.

        Args:
            file_path: Path to the conversation.json file.

        Returns:
            Dictionary containing conversation data.
        """
        try:
            # For conversation.json files, they're typically small enough to load directly
            # If we encounter memory issues, we can switch to streaming parsing
            with open(file_path, "r", encoding="utf-8") as f:
                return cast(Dict[str, Any], json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to parse {file_path}: {str(e)}")
            return {}

    def _parse_conversations_json(
        self,
        file_path: Path,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Parse the conversations.json file using streaming JSON parsing.

        This method uses ijson to stream the JSON array of conversations, yielding
        one conversation at a time to avoid loading the entire file into memory.
        This is crucial for handling large exports that can be hundreds of megabytes.

        The method also updates the progress bar if provided, to give feedback on
        the processing status.

        Args:
            file_path: Path to the conversations.json file.
            progress: Optional progress bar.
            task_id: Optional task ID for progress reporting.

        Returns:
            Generator yielding conversation data dictionaries.
        """
        try:
            with open(file_path, "rb") as f:
                # Use ijson to stream the JSON array
                for conversation in ijson.items(f, "item"):
                    # Yield one conversation at a time to avoid loading all into memory
                    yield conversation

                    # Update progress if provided
                    if progress and task_id:
                        progress.update(task_id, advance=1)
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {str(e)}")
            raise

    def _reconstruct_message_tree(
        self, mapping: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Reconstruct the message tree from parent-child relationships.

        Args:
            mapping: Dictionary of messages keyed by ID.

        Returns:
            List of messages in tree order.
        """
        if not mapping:
            return []

        # Create a dictionary of messages keyed by ID
        messages = {}
        for msg_id, msg_data in mapping.items():
            messages[msg_id] = msg_data

        # Find root messages (those with no parent or system-generated parent)
        root_messages = []
        for msg_id, msg_data in messages.items():
            parent_id = msg_data.get("parent")
            if not parent_id or (
                parent_id in messages and not messages[parent_id].get("message")
            ):
                root_messages.append(msg_id)

        # Sort root messages by create time if available
        root_messages.sort(
            key=lambda msg_id: messages[msg_id].get("create_time", 0)
            if messages[msg_id].get("create_time")
            else 0
        )

        # Build the tree by traversing from roots
        conversation = []
        for root_id in root_messages:
            branch = self._build_message_branch(root_id, messages)
            if branch:
                conversation.append(branch)

        return conversation

    def _build_message_branch(
        self, msg_id: str, messages: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Build a branch of the message tree.

        Args:
            msg_id: ID of the root message of this branch.
            messages: Dictionary of all messages keyed by ID.

        Returns:
            Dictionary containing the message and its children.
        """
        if msg_id not in messages:
            return None

        msg_data = messages[msg_id]

        # Skip messages without content
        if not msg_data.get("message"):
            return None

        # Create a copy of the message data
        branch = cast(Dict[str, Any], msg_data.copy())

        # Add children
        children = []
        child_ids = msg_data.get("children", [])

        # Sort children by create time if available
        child_ids.sort(
            key=lambda child_id: messages[child_id].get("create_time", 0)
            if child_id in messages and messages[child_id].get("create_time")
            else 0
        )

        for child_id in child_ids:
            child_branch = self._build_message_branch(child_id, messages)
            if child_branch:
                children.append(child_branch)

        branch["children"] = children
        return branch

    def _process_attachment_from_asset_pointer(
        self,
        asset_pointer: str,
        export_dir: Path,
        output_dir: Path,
        config: Config,
        result: ProcessingResult,
    ) -> Optional[str]:
        """Process an attachment from an asset pointer.

        This method handles image attachments referenced by asset pointers in ChatGPT exports.
        It searches for the attachment file in multiple locations:
        1. The 'attachments' subdirectory of the export directory
        2. The export directory itself
        3. The parent directory of the export directory (for consolidated exports)

        Instead of copying the attachment file to the output directory, it generates
        a comment-based representation of the attachment using the AttachmentHandlerMixin.

        Args:
            asset_pointer: The asset pointer string (e.g., 'file-service://file-1qPqkFADL5KFETEUBrpyTF')
            export_dir: The export directory containing the attachment files
            output_dir: The output directory for processed attachments (kept for compatibility but not used for file operations)
            config: Configuration
            result: Processing result

        Returns:
            Markdown representation of the attachment as comments, or None if not found
        """
        if not asset_pointer.startswith("file-service://file-"):
            logger.warning(f"Unsupported asset pointer format: {asset_pointer}")
            return None

        # Extract the file ID from the asset pointer
        file_id = asset_pointer.replace("file-service://file-", "")

        # Look for matching files in the export directory
        # First check in the attachments subdirectory if it exists
        attachments_dir = export_dir / "attachments"
        if attachments_dir.exists() and attachments_dir.is_dir():
            for attachment_file in attachments_dir.glob(f"file-{file_id}*"):
                return self._process_attachment(
                    attachment_file,
                    output_dir,  # This is now the main destination directory
                    self.attachment_processor,
                    config,
                    result,
                    is_image=True,
                )

        # If not found in attachments dir, check the export directory itself
        for attachment_file in export_dir.glob(f"file-{file_id}*"):
            return self._process_attachment(
                attachment_file,
                output_dir,  # This is now the main destination directory
                self.attachment_processor,
                config,
                result,
                is_image=True,
            )

        # If still not found, check parent directory (for consolidated exports)
        for attachment_file in export_dir.parent.glob(f"file-{file_id}*"):
            return self._process_attachment(
                attachment_file,
                output_dir,  # This is now the main destination directory
                self.attachment_processor,
                config,
                result,
                is_image=True,
            )

        logger.warning(f"Attachment not found for asset pointer: {asset_pointer}")
        return None

    def _process_message_content(
        self,
        message: Dict[str, Any],
        export_dir: Path,
        output_dir: Path,
        config: Config,
        result: ProcessingResult,
    ) -> str:
        """Process message content, handling attachments.

        This method processes the content of a message, including any attachments.
        For text content, it simply returns the text.
        For image attachments (identified by asset pointers), it processes the attachment
        using the _process_attachment_from_asset_pointer method, which generates a
        comment-based representation of the attachment.

        Args:
            message: The message object
            export_dir: The export directory containing attachment files
            output_dir: The output directory for processed attachments
            config: Configuration
            result: Processing result

        Returns:
            Processed message content as markdown
        """
        if not message.get("message") or not message["message"].get("content"):
            return ""

        content = message["message"]["content"]
        parts = content.get("parts", [])

        # Process each part of the message
        processed_parts = []

        for part in parts:
            if (
                isinstance(part, dict)
                and part.get("content_type") == "image_asset_pointer"
            ):
                # This is an image attachment
                asset_pointer = part.get("asset_pointer", "")
                attachment_md = self._process_attachment_from_asset_pointer(
                    asset_pointer, export_dir, output_dir, config, result
                )
                if attachment_md:
                    processed_parts.append(attachment_md)
                else:
                    # Fallback if attachment processing failed
                    processed_parts.append(f"[Image: {asset_pointer}]")
            elif isinstance(part, str):
                # Regular text content
                processed_parts.append(part)

        return "\n\n".join(processed_parts)

    def _format_message_content(
        self,
        message: Dict[str, Any],
        export_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        config: Optional[Config] = None,
        result: Optional[ProcessingResult] = None,
    ) -> str:
        """Format message content as markdown.

        Args:
            message: The message object
            export_dir: Optional export directory for attachment processing
            output_dir: Optional output directory for processed attachments
            config: Optional configuration
            result: Optional processing result

        Returns:
            Formatted message content
        """
        if not message.get("message") or not message["message"].get("content"):
            return ""

        # If we have export_dir, output_dir, config, and result, process attachments
        if export_dir and output_dir and config and result:
            return self._process_message_content(
                message, export_dir, output_dir, config, result
            )

        # Otherwise, fall back to basic formatting without attachment processing
        content = message["message"]["content"]
        parts = content.get("parts", [])

        # Process each part of the message
        processed_parts = []

        for part in parts:
            if (
                isinstance(part, dict)
                and part.get("content_type") == "image_asset_pointer"
            ):
                # Just include a placeholder for the image
                asset_pointer = part.get("asset_pointer", "")
                processed_parts.append(f"[Image: {asset_pointer}]")
            elif isinstance(part, str):
                # Regular text content
                processed_parts.append(part)

        return "\n\n".join(processed_parts)

    def _generate_markdown(
        self,
        conversation: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        export_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        config: Optional[Config] = None,
        result: Optional[ProcessingResult] = None,
    ) -> str:
        """Generate markdown from conversation tree.

        This method generates a markdown representation of a conversation tree.
        It includes the conversation title, creation time, and all messages in the conversation.
        Messages are formatted based on their author (user or assistant) and content.

        For messages with attachments, it processes the attachments using the
        _process_message_content method, which generates comment-based representations
        of the attachments instead of copying the actual files.

        The output is a single markdown file with the following structure:
        ```
        # Conversation Title
        *Created: YYYY-MM-DD HH:MM:SS*

        ## User:
        User message content

        ## Assistant:
        Assistant message content

        <!-- ATTACHMENT: IMAGE: filename.jpg (dimensions, size) -->
        <!-- GPT Description: description text -->
        ![description]()
        ```

        Args:
            conversation: The conversation tree
            metadata: Conversation metadata
            export_dir: Optional export directory for attachment processing
            output_dir: Optional output directory (kept for compatibility but not used for file operations)
            config: Optional configuration
            result: Optional processing result

        Returns:
            Markdown representation of the conversation
        """
        # Start with the title and metadata
        title = metadata.get("title", "Untitled Conversation")
        create_time = metadata.get("create_time")

        lines = [f"# {title}"]

        if create_time:
            try:
                # Convert timestamp to datetime
                if isinstance(create_time, (int, float)):
                    dt = datetime.fromtimestamp(create_time)
                    lines.append(f"*Created: {dt.strftime('%Y-%m-%d %H:%M:%S')}*")
                else:
                    lines.append(f"*Created: {create_time}*")
            except (ValueError, TypeError):
                # If conversion fails, just use the raw value
                lines.append(f"*Created: {create_time}*")

        lines.append("")  # Add a blank line after metadata

        # Process the conversation tree
        def process_message_tree(
            messages: List[Dict[str, Any]], depth: int = 0
        ) -> None:
            for message in messages:
                if not message:
                    continue

                msg_data = message.get("message", {})
                author = msg_data.get("author", {}).get("role", "unknown")

                # Format the message based on author
                if author == "user":
                    lines.append("## User:")
                elif author == "assistant":
                    lines.append("## Assistant:")
                else:
                    lines.append(f"## {author.capitalize()}:")

                # Format the content
                if export_dir and output_dir and config and result:
                    content = self._format_message_content(
                        message, export_dir, output_dir, config, result
                    )
                else:
                    content = self._format_message_content(message)

                lines.append(content)
                lines.append("")  # Add a blank line after each message

                # Process children
                children = message.get("children", [])
                if children:
                    process_message_tree(children, depth + 1)

        # Start processing from the root
        process_message_tree(conversation)

        return "\n".join(lines)

    def _process_conversation(
        self, conv_dir: Path, config: Config, result: ProcessingResult
    ) -> str:
        """Process a single conversation directory.

        Args:
            conv_dir: Path to the conversation directory.
            config: Configuration.
            result: Processing result.

        Returns:
            Generated markdown content.
        """
        try:
            # Load conversation and metadata
            conv_json = conv_dir / "conversation.json"
            metadata_json = conv_dir / "metadata.json"

            conversation_data = self._parse_conversation_json(conv_json)
            metadata = self._load_metadata(metadata_json)

            # Reconstruct message tree
            mapping = conversation_data.get("mapping", {})
            message_tree = self._reconstruct_message_tree(mapping)

            # No longer creating output directory for attachments
            # Use the main destination directory for all output

            # Check for attachments directory
            attachments_dir = conv_dir / "attachments"
            if not attachments_dir.exists():
                logger.debug(f"No attachments directory found in {conv_dir}")

            # Generate markdown with attachment processing
            markdown = self._generate_markdown(
                message_tree,
                metadata,
                conv_dir,
                self.source_config.dest_dir,
                config,
                result,
            )

            return markdown
        except Exception as e:
            logger.error(f"Error processing conversation {conv_dir}: {str(e)}")
            result.add_error(str(conv_dir), str(e))
            # Return empty string on error to avoid breaking the cache mechanism
            return ""

    def _process_conversations_file(
        self,
        file_path: Path,
        config: Config,
        result: ProcessingResult,
        progress: Optional[Progress] = None,
    ) -> None:
        """Process a conversations.json file.

        This method processes a conversations.json file, which contains multiple conversations.
        It uses streaming JSON parsing with ijson to efficiently process large files without
        loading them entirely into memory. Each conversation is processed individually and
        saved as a separate markdown file.

        The method includes progress reporting to track the processing of potentially
        hundreds or thousands of conversations.

        Args:
            file_path: Path to the conversations.json file.
            config: The configuration.
            result: The processing result.
            progress: Optional Progress instance for reporting progress.
        """
        try:
            self._process_conversations_file_impl(file_path, config, result, progress)
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {str(e)}")
            result.add_error(str(file_path), str(e))
            result.add_skipped(self._processor_type)

    def _process_conversations_file_impl(
        self,
        file_path: Path,
        config: Config,
        result: ProcessingResult,
        progress: Optional[Progress] = None,
    ) -> None:
        """Process a conversations.json file.

        Args:
            file_path: Path to the conversations.json file
            config: Configuration
            result: Processing result
            progress: Optional progress bar
        """
        # Create a progress bar for this file
        file_progress = None
        file_task_id = None
        if progress:
            file_progress = progress
            file_task_id = progress.add_task(
                f"Processing {file_path.name}...", total=None
            )
        else:
            file_progress = Progress()
            file_task_id = file_progress.add_task(
                f"Processing {file_path.name}...", total=None
            )

        try:
            # Get the export directory
            # Removing unused variable: export_dir = self._get_source_dir(config)

            # Parse the conversations.json file
            conversations = list(
                self._parse_conversations_json(file_path, file_progress, file_task_id)
            )

            # Update the progress bar with the total number of conversations
            if file_progress and file_task_id is not None:
                file_progress.update(file_task_id, total=len(conversations))
                file_progress.update(file_task_id, completed=0)

            # Process each conversation
            for conversation in conversations:
                try:
                    # Get the conversation ID
                    conversation_id = conversation.get("id", "unknown")

                    # Extract metadata
                    metadata = {
                        "id": conversation_id,
                        "title": conversation.get("title", "Untitled Conversation"),
                        "create_time": conversation.get("create_time", ""),
                        "update_time": conversation.get("update_time", ""),
                    }

                    # Generate output path
                    output_path = self._get_output_path(metadata)

                    # Get the conversation content
                    conv_content = json.dumps(conversation)

                    # Process the conversation
                    self.process_file_with_cache(
                        # Use a virtual path based on the conversation ID
                        Path(f"{file_path.parent}/conversation_{conversation_id}.json"),
                        conv_content,
                        output_path,
                        config,
                        result,
                        None,  # No attachments directory for conversations.json entries
                        lambda _: self._generate_markdown(
                            self._reconstruct_message_tree(
                                {
                                    msg["id"]: msg
                                    for msg in conversation.get("mapping", {}).values()
                                }
                            ),
                            metadata,
                        ),
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to process conversation {conversation_id}: {str(e)}"
                    )
                    result.add_error(f"conversation_{conversation_id}", str(e))

                # Update progress (already handled in _parse_conversations_json)
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {str(e)}")
            result.add_error(str(file_path), str(e))
        finally:
            # Clean up the local progress if we created one
            if file_progress:
                file_progress.__exit__(None, None, None)

    def _get_source_dir(self, config: Config) -> Path:
        """Get the source directory.

        Args:
            config: The configuration.

        Returns:
            The source directory.
        """
        return self.source_config.src_dir

    def _process_impl(self, config: Config) -> ProcessingResult:
        """Process ChatGPT conversations.

        Args:
            config: Configuration

        Returns:
            Processing result
        """
        result = ProcessingResult()

        # Get the source directory
        export_dir = self._get_source_dir(config)

        # Create a progress bar
        with Progress() as progress:
            # Add a task for the overall processing
            task_id = progress.add_task(
                "Processing ChatGPT conversations...", total=None
            )

            # Find all conversations.json files
            conversations_files = []
            for path in export_dir.glob("**/conversations.json"):
                conversations_files.append(path)

            # Update the progress bar with the total number of files
            progress.update(task_id, total=len(conversations_files))
            progress.update(task_id, completed=0)

            # Process each conversations.json file
            for file_path in self._apply_limit(conversations_files):
                try:
                    self._process_conversations_file(
                        file_path, config, result, progress
                    )
                    progress.advance(task_id)
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {str(e)}")
                    result.add_error(str(file_path), str(e))
                    result.add_skipped(self._processor_type)
                    progress.advance(task_id)

        # Log the result
        logger.info(f"Completed processing ChatGPT conversations: {result}")
        return result
