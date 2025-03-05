"""Claude conversation export processor."""

import hashlib
import json
import logging
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.progress import Progress, TaskID

from ..attachments.processor import AttachmentProcessor
from ..cache import CacheManager
from ..config import Config, SourceConfig
from .base import SourceProcessor
from .result import ProcessingResult

logger = logging.getLogger(__name__)


class ClaudeProcessor(SourceProcessor):
    """Process Claude conversation exports into Markdown.

    Note: Claude exports only provide metadata and extracted text from attachments,
    unlike other processors that can access the actual files. This processor handles
    these limitations by clearly indicating the extracted nature of attachments in
    the output.
    """

    def __init__(
        self, source_config: SourceConfig, cache_manager: Optional[CacheManager] = None
    ):
        """Initialize processor with source configuration."""
        super().__init__(source_config, cache_manager)
        self.validate()

        # Initialize artifact tracking
        self._artifact_versions: Dict[str, List[Dict[str, Any]]] = {}
        self._artifact_relationships: Dict[str, List[str]] = {}

    @property
    def attachment_processor(self) -> AttachmentProcessor:
        """Get the attachment processor instance."""
        if self._attachment_processor is None:
            self._attachment_processor = AttachmentProcessor(
                self.source_config.dest_dir
            )
        return self._attachment_processor

    def validate(self) -> None:
        """Validate source configuration.

        Raises:
            ValueError: If source configuration is invalid.
        """
        super().validate()

    def _get_output_path(self, title: str, created_at: Optional[str] = None) -> Path:
        """Generate output path for a conversation.

        Args:
            title: The conversation title.
            created_at: Optional creation timestamp.

        Returns:
            Path to save the markdown file.
        """
        # Format the filename
        if created_at:
            try:
                # Parse the date from ISO format
                date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                # Format as YYYYMMDD
                date_prefix = date.strftime("%Y%m%d")
            except (ValueError, AttributeError):
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

        filename = clean_filename

        # Remove consecutive underscores
        filename = re.sub(r"_+", "_", filename)
        # Remove leading/trailing underscores
        filename = filename.strip("_")

        # Ensure we have a valid filename
        if not filename:
            filename = "Untitled"

        # Combine date and title
        if date_prefix == "00000000":
            filename = filename  # No date prefix for missing/invalid dates
        else:
            filename = f"{date_prefix}-{filename}"

        # Ensure the filename is valid and has .md extension
        if not filename:
            filename = "Untitled"
        filename = f"{filename}.md"

        # Create output directory if it doesn't exist
        self.source_config.dest_dir.mkdir(parents=True, exist_ok=True)

        # Create and return the output path
        output_path = self.source_config.dest_dir / filename
        return output_path

    def _track_artifact(
        self, artifact_text: str, message_id: str, conversation_id: str
    ) -> None:
        """Track an artifact for version history and relationships.

        Args:
            artifact_text: The artifact content.
            message_id: The ID of the message containing the artifact.
            conversation_id: The ID of the conversation.
        """
        # Generate a stable identifier for the artifact based on its content
        # We want different content to get different IDs, but same content to get same ID
        # Use the raw content for hashing to preserve all differences
        logger.debug(f"Raw artifact text: '{artifact_text}'")
        logger.debug(f"Message ID: {message_id}")
        logger.debug(f"Conversation ID: {conversation_id}")

        # Normalize the content to ensure consistent hashing while preserving structure:
        # 1. Strip leading/trailing whitespace
        # 2. Normalize line endings to \n
        # 3. Convert to bytes using UTF-8 encoding
        # 4. Use SHA-256 for better hash distribution
        # 5. Take first 12 chars of hex digest
        normalized_text = artifact_text.strip()
        normalized_text = normalized_text.replace("\r\n", "\n").replace(
            "\r", "\n"
        )  # Normalize line endings
        content_bytes = normalized_text.encode("utf-8")
        logger.debug(f"Normalized text: '{normalized_text}'")
        logger.debug(f"Content bytes: {content_bytes!r}")
        content_hash = hashlib.sha256(content_bytes).hexdigest()[:12]
        logger.debug(f"Generated hash: {content_hash}")
        logger.debug(f"Full hex digest: {hashlib.sha256(content_bytes).hexdigest()}")
        artifact_id = content_hash

        # Track version
        if artifact_id not in self._artifact_versions:
            self._artifact_versions[artifact_id] = []

        self._artifact_versions[artifact_id].append(
            {
                "content": artifact_text,
                "message_id": message_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
        )

        # Track relationships (artifacts in the same conversation)
        if conversation_id not in self._artifact_relationships:
            self._artifact_relationships[conversation_id] = []
        self._artifact_relationships[conversation_id].append(artifact_id)

    def _process_impl(self, config: Config) -> ProcessingResult:
        """Process Claude export files.

        Args:
            config: The configuration to use.

        Returns:
            The processing result.
        """
        result = ProcessingResult()

        # Create destination directory if it doesn't exist
        self.source_config.dest_dir.mkdir(parents=True, exist_ok=True)

        # Check if source directory exists and has the conversations.json file
        conversations_file = self.source_config.src_dir / "conversations.json"
        if (
            not self.source_config.src_dir.exists()
            or not self.source_config.src_dir.is_dir()
        ):
            logger.info(
                f"Source directory does not exist: {self.source_config.src_dir}"
            )
            logger.info("No Claude conversations to process")
            return result

        if not conversations_file.is_file():
            logger.info(f"No conversations.json found in {self.source_config.src_dir}")
            logger.info("No Claude conversations to process")
            return result

        try:
            with open(conversations_file, "r", encoding="utf-8") as f:
                conversations = json.load(f)

            # Handle both single conversation and array of conversations
            if isinstance(conversations, dict):
                conversations = [conversations]
            elif not isinstance(conversations, list):
                error_msg = f"Invalid conversations format in {conversations_file}"
                logger.error(error_msg)
                result.add_error(error_msg, self._processor_type)
                return result

            # Log the total number of conversations to process
            logger.info(f"Processing {len(conversations)} Claude conversations...")

            # Track processing statistics
            processed_count = 0
            skipped_count = 0
            errors_count = 0

            # Process each conversation
            for i, conversation in enumerate(conversations):
                try:
                    # Process the conversation
                    self._process_conversation(conversation, config, result)

                    # Update statistics based on the last action
                    if result.last_action == "generated":
                        processed_count += 1
                    elif result.last_action == "from_cache":
                        processed_count += 1
                    elif result.last_action == "skipped":
                        skipped_count += 1

                    # Log batch progress every 20 conversations or at the end
                    if (i + 1) % 20 == 0 or i + 1 == len(conversations):
                        logger.info("-" * 30)
                        logger.info(
                            f"Processed {i + 1}/{len(conversations)} Claude conversations "
                            f"({processed_count} successful, {skipped_count} skipped, {errors_count} errors)"
                        )
                except Exception as e:
                    logger.error(f"Error processing conversation {i}: {str(e)}")
                    result.add_error(f"conversation_{i}", str(e))
                    errors_count += 1

        except Exception as e:
            error_msg = (
                f"Error reading conversations file {conversations_file}: {str(e)}"
            )
            logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)

        # Use the standardized format_completion_summary method
        logger.info(self.format_completion_summary(result))

        return result

    def _validate_conversation(self, conversation: Dict[str, Any]) -> bool:
        """Validate a conversation has required fields and valid content.

        Args:
            conversation: The conversation to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not isinstance(conversation, dict):
            logger.warning("Invalid conversation format: not a dictionary")
            return False

        # Check required fields
        if "chat_messages" not in conversation:
            logger.warning("Missing required field: chat_messages")
            return False

        # Name is optional, will use default if missing
        if not conversation.get("name"):
            conversation["name"] = "Untitled Conversation"

        # UUID is optional, will use "unknown" if missing
        if "uuid" not in conversation:
            conversation["uuid"] = "unknown"

        # Check messages
        messages = conversation.get("chat_messages", [])
        if not isinstance(messages, list):
            logger.warning("Invalid 'chat_messages' format - expected list")
            return False

        # Allow empty conversations
        if not messages:
            return True

        # Check if any message has valid content
        has_valid_content = False
        for message in messages:
            if not isinstance(message, dict):
                continue

            # Check for required message fields
            if "sender" not in message:
                continue

            content = message.get("content", [])
            if content is None:
                content = []

            if not isinstance(content, list):
                continue

            # Consider empty content valid
            if not content:
                has_valid_content = True
                continue

            # Check for any valid content block
            for block in content:
                if not isinstance(block, dict):
                    continue
                # Consider any block with text or type valid
                if block.get("text") is not None or block.get("type"):
                    has_valid_content = True
                    break

            if has_valid_content:
                break

        return True  # Allow all conversations through validation

    def _process_conversation(
        self, conversation: Dict[str, Any], config: Config, result: ProcessingResult
    ) -> None:
        """Process a conversation into markdown format.

        Args:
            conversation: The conversation to process.
            config: The configuration to use.
            result: The processing result to update.
        """
        try:
            # Validate conversation
            if not self._validate_conversation(conversation):
                logger.warning(
                    f"Skipping invalid conversation: {conversation.get('uuid', 'unknown')}"
                )
                result.add_skipped(self._processor_type)
                return

            # Extract conversation metadata
            title = conversation.get("name", "Untitled Conversation")
            created_at = conversation.get("created_at")

            # For warning context
            context = f"[{title}] ({conversation.get('uuid', 'unknown')})"
            logger.debug(f"Processing conversation: {context}")

            # Generate output path
            output_file = self._get_output_path(title, created_at)

            # Check if we need to regenerate
            if not config.global_config.force_generation and output_file.exists():
                logger.debug(f"{context} - Using cached version")
                result.add_from_cache(self._processor_type)
                return

            # Convert to markdown
            try:
                markdown = self._convert_to_markdown(conversation, config, result)
                logger.debug(
                    f"{context} - Generated markdown content length: {len(markdown) if markdown else 0}"
                )
                if markdown is None:
                    # For verbosity level 0-1, use debug level instead of warning
                    if (
                        hasattr(config.global_config, "verbosity")
                        and config.global_config.verbosity <= 1
                    ):
                        logger.debug(
                            f"{context} - Skipping conversation with no content"
                        )
                    else:
                        logger.warning(
                            f"{context} - Skipping conversation with no content"
                        )
                    result.add_skipped(self._processor_type)
                    return

                # Write output file
                logger.debug(f"{context} - Writing to file: {output_file}")
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(markdown, encoding="utf-8")
                logger.debug(
                    f"{context} - Wrote {len(markdown)} bytes to: {output_file}"
                )
                result.add_generated(self._processor_type)
            except (TypeError, AttributeError) as e:
                logger.error(
                    f"{context} - Error converting conversation to markdown: {str(e)}"
                )
                result.add_error(
                    f"Error converting conversation to markdown: {str(e)}",
                    self._processor_type,
                )
                result.add_skipped(self._processor_type)
                return

        except Exception as e:
            error_msg = f"Error processing conversation: {str(e)}"
            logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)
            result.add_skipped(self._processor_type)

    def _format_file_size(self, size_in_bytes: int) -> str:
        """Format file size in human readable format.

        Args:
            size_in_bytes: File size in bytes

        Returns:
            Formatted size string (e.g., "1.2MB")
        """
        size_float = float(size_in_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size_float < 1024:
                return f"{size_float:.1f}{unit}"
            size_float /= 1024
        return f"{size_float:.1f}TB"

    def _get_attachment_icon(self, file_type: str) -> str:
        """Get appropriate icon for file type.

        Args:
            file_type: The type of file

        Returns:
            Emoji icon representing the file type
        """
        type_lower = file_type.lower()
        if "pdf" in type_lower:
            return "📄"
        elif any(x in type_lower for x in ["doc", "docx", "txt", "text"]):
            return "📝"
        elif any(x in type_lower for x in ["jpg", "jpeg", "png", "gif", "image"]):
            return "🖼️"
        elif "json" in type_lower:
            return "📊"
        elif "csv" in type_lower:
            return "📈"
        elif any(x in type_lower for x in ["py", "js", "java", "cpp", "script"]):
            return "💻"
        return "📎"

    def _format_text_attachment(
        self,
        attachment: Dict[str, Any],
        message_id: str,
        result: ProcessingResult,
    ) -> Optional[str]:
        """Format a text attachment for markdown output.

        Note: Claude exports only provide metadata and extracted content.
        This is not the original file, but rather Claude's extracted representation.

        Args:
            attachment: The attachment data from the message
            message_id: The ID of the message containing the attachment
            result: The processing result to update

        Returns:
            The markdown representation of the attachment, or None if invalid
        """
        try:
            file_type = attachment.get("file_type", "")
            file_name = attachment.get("file_name", "")
            content = attachment.get("content", attachment.get("extracted_content", ""))
            file_size = attachment.get("file_size", 0)

            if not file_type or not file_name:
                logger.warning(
                    f"Invalid text attachment in message {message_id}: missing type or name"
                )
                return None

            # Update processing result
            result.documents_processed += 1

            # Format size if available
            size_str = (
                f" ({self._format_file_size(file_size)} {file_type})"
                if file_size
                else f" ({file_type})"
            )

            # Get appropriate icon
            icon = self._get_attachment_icon(file_type)

            # If content is empty, show metadata with a note
            if not content:
                logger.warning(
                    f"Empty content in attachment {file_name} ({message_id})"
                )
                return f"""
<!-- CLAUDE EXPORT: Empty attachment {file_name} -->
<details>
<summary>{icon} {file_name}{size_str} - Empty Attachment</summary>

Original File Information:
- Type: {file_type}
- Size: {self._format_file_size(file_size) if file_size else 'Unknown'}
- Extracted: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
- Status: No content available in Claude export

</details>
"""

            # Format the content with details tag
            return f"""
<!-- CLAUDE EXPORT: Extracted content from {file_name} -->
<details>
<summary>{icon} {file_name}{size_str} - Extracted Content</summary>

Original File Information:
- Type: {file_type}
- Size: {self._format_file_size(file_size) if file_size else 'Unknown'}
- Extracted: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

Extracted Content:
```{file_type}
{content}
```

</details>
"""

        except Exception as e:
            error_msg = (
                f"Error formatting text attachment in message {message_id}: {str(e)}"
            )
            logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)
            return None

    def _convert_to_markdown(
        self, conversation: Dict[str, Any], config: Config, result: ProcessingResult
    ) -> Optional[str]:
        """Convert a conversation to markdown format.

        Args:
            conversation: The conversation to convert.
            config: The configuration to use.
            result: The processing result to update.

        Returns:
            The markdown content, or None if conversion failed.
        """
        try:
            # Extract conversation metadata
            title = conversation.get("name", "Untitled Conversation")
            created_at = conversation.get("created_at")

            # Format title and metadata
            content = []
            content.append(f"# {title}")
            content.append("")

            if created_at:
                try:
                    # Parse the date from ISO format
                    date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    # Format as human readable
                    content.append(f"Created: {date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    content.append("")
                except (ValueError, AttributeError):
                    pass  # Skip invalid dates

            # Process messages
            messages = conversation.get("chat_messages", [])
            if not isinstance(messages, list):
                logger.warning(f"{title} - Invalid messages format")
                return None

            # Skip empty conversations
            if not messages:
                # For verbosity level 0-1, use debug level instead of warning
                if (
                    hasattr(config.global_config, "verbosity")
                    and config.global_config.verbosity <= 1
                ):
                    logger.debug(f"{title} - No messages")
                else:
                    logger.warning(f"{title} - No messages")
                return None

            # Process each message
            for message in messages:
                if not isinstance(message, dict):
                    continue

                # Get sender and timestamp
                sender = message.get("sender", "unknown")
                message_time = message.get("created_at")

                # Format sender line
                content.append(f"## {sender}")
                if message_time:
                    try:
                        date = datetime.fromisoformat(
                            message_time.replace("Z", "+00:00")
                        )
                        content.append(f"Time: {date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    except (ValueError, AttributeError):
                        pass

                content.append("")

                # Process text attachments
                for attachment in message.get("attachments", []):
                    if attachment.get("extracted_content"):
                        attachment_md = self._format_text_attachment(
                            attachment,
                            message.get("uuid", "unknown"),
                            result,  # Pass result directly
                        )
                        if attachment_md:
                            content.append(attachment_md)
                            content.append("")

                # Process message content
                content.extend(self._process_message_content(message, result))
                content.append("")  # Add blank line between messages

            # Join content with newlines
            return "\n".join(content)

        except Exception as e:
            error_msg = f"Error converting conversation to markdown: {str(e)}"
            logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)
            return None

    def _process_message_content(
        self, message: Dict[str, Any], result: ProcessingResult
    ) -> List[str]:
        """Process message content blocks into markdown lines.

        Args:
            message: The message to process.
            result: The processing result to update.

        Returns:
            List of markdown lines.
        """
        content = []
        message_id = message.get("uuid", "unknown")

        # Handle case where message content is a list
        message_content = message.get("content", [])
        if not isinstance(message_content, list):
            message_content = []

        for block in message_content:
            if not isinstance(block, dict):
                continue

            block_type = block.get("type", "text")
            block_text = block.get("text", "")

            if not block_text:
                continue

            if block_type == "text":
                content.extend(self._process_text_block(block_text))
                content.append("")

            elif block_type == "thinking":
                content.append("💭 **Thinking Process:**")
                content.append("")
                content.extend(self._process_text_block(block_text))
                content.append("")

            elif block_type == "tool_use":
                content.append("🛠️ **Tool Usage:**")
                content.append("")
                content.append(f"Tool: {block.get('name', 'unknown')}")
                content.append("```tool-use")
                content.append(json.dumps(block.get("input", {}), indent=2))
                content.append("```")
                content.append("")

            elif block_type == "tool_result":
                content.append("📋 **Tool Result:**")
                content.append("")
                content.append(
                    f"Status: {'SUCCESS' if not block.get('is_error') else 'ERROR'}"
                )
                if block.get("output"):
                    content.append("```")
                    content.append(block["output"])
                    content.append("```")
                content.append("")

            elif block_type == "attachment":
                attachment_text = self._format_text_attachment(
                    block, message_id, result
                )
                if attachment_text:
                    content.append(attachment_text)
                    content.append("")

        return content

    def _process_attachment(
        self,
        attachment_path: Path,
        output_dir: Path,
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult,
        alt_text: Optional[str] = None,
        is_image: bool = True,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None,
    ) -> Optional[str]:
        """Process a single attachment and return its markdown representation."""
        try:
            if not attachment_path.exists():
                logger.warning(f"Attachment not found: {attachment_path}")
                if progress and task_id is not None:
                    progress.advance(task_id)
                return None

            # Process the file
            temp_path, metadata = attachment_processor.process_file(
                attachment_path,
                force=config.global_config.force_generation,
                result=result,
            )

            # Copy processed file to output directory
            output_path = output_dir / attachment_path.name
            if temp_path.suffix != attachment_path.suffix:
                # If the extension changed (e.g. svg -> jpg), update the output path
                output_path = output_path.with_suffix(temp_path.suffix)
            shutil.copy2(temp_path, output_path)

            # Format based on type
            if metadata.is_image:
                result.add_image_generated(self._processor_type)
                formatted = self._format_image(output_path, metadata, config, result)
            else:
                result.add_document_generated(self._processor_type)
                formatted = self._format_document(
                    output_path, metadata, alt_text, result
                )

            if progress and task_id is not None:
                progress.advance(task_id)
            return formatted

        except Exception as e:
            logger.error(f"Error processing attachment {attachment_path}: {str(e)}")
            if is_image:
                result.add_image_skipped(self._processor_type)
            else:
                result.add_document_skipped(self._processor_type)
            if progress and task_id is not None:
                progress.advance(task_id)
            return None

    def _process_text_block(self, text: str) -> List[str]:
        """Process a text block into markdown lines.

        Args:
            text: The text content to process.

        Returns:
            List of markdown lines.
        """
        if not text:
            return []

        # Split text into lines and handle XML-like tags
        lines: List[str] = []
        for line in text.split("\n"):
            # Process any XML-like tags
            if "<antThinking>" in line:
                line = line.replace("<antThinking>", "_Thinking: ")
                line = line.replace("</antThinking>", "_")
            # Note: We don't replace antArtifact tags here anymore, as they're handled
            # in _convert_to_markdown
            lines.append(line)

        return lines
