"""Claude conversation export processor."""

import hashlib
import json
import logging
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

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

    def __init__(self, source_config: SourceConfig):
        """Initialize processor with source configuration."""
        super().__init__(source_config)
        self.cache_manager = CacheManager(source_config.dest_dir.parent)
        self.validate()
        self._attachment_processor: Optional[AttachmentProcessor] = None
        self._artifact_versions: Dict[str, List[Dict[str, Any]]] = {}
        self._artifact_relationships: Dict[str, Set[str]] = {}

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

        # Check for conversations.json in source directory
        src_conversations_file = self.source_config.src_dir / "conversations.json"
        if not src_conversations_file.exists():
            raise ValueError(
                f"conversations.json not found in source directory: {self.source_config.src_dir}"
            )
        if not src_conversations_file.is_file():
            raise ValueError(
                f"conversations.json is not a file: {src_conversations_file}"
            )

        # Check for conversations.json and users.json in the cache directory
        cache_dir = self.cache_manager.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        conversations_file = cache_dir / "conversations.json"
        users_file = cache_dir / "users.json"

        # Create empty files in cache if they don't exist
        if not conversations_file.exists():
            conversations_file.write_text("[]")
        if not users_file.exists():
            users_file.write_text("{}")

        if not conversations_file.is_file():
            raise ValueError(f"conversations.json is not a file: {conversations_file}")
        if not users_file.is_file():
            raise ValueError(f"users.json is not a file: {users_file}")

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
            self._artifact_relationships[conversation_id] = set()
        self._artifact_relationships[conversation_id].add(artifact_id)

    def _process_impl(self, config: Config) -> ProcessingResult:
        """Process Claude export files.

        Args:
            config: The configuration to use.

        Returns:
            The processing result.
        """
        result = ProcessingResult()

        # Reset artifact tracking
        self._artifact_versions = {}
        self._artifact_relationships = {}

        # Create all necessary directories
        self.source_config.dest_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir = self.source_config.dest_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Load conversations from cache
        conversations_file = self.cache_manager.cache_dir / "conversations.json"
        try:
            conversations = json.loads(conversations_file.read_text())
            if not isinstance(conversations, list):
                conversations = [conversations]

            # Filter out None values and non-dict items
            conversations = [c for c in conversations if isinstance(c, dict)]

            # Sort conversations by creation date (most recent first)
            conversations.sort(
                key=lambda x: x.get("created_at", "") or "", reverse=True
            )

            # Apply limit if set
            if self.item_limit is not None:
                logger.debug(f"Limiting to {self.item_limit} most recent conversations")
                conversations = conversations[: self.item_limit]

        except json.JSONDecodeError as e:
            error_msg = f"Error parsing conversations.json: {str(e)}"
            logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)
            return result

        # Track conversations for index
        conversation_index = []

        # Process each conversation
        for conversation in conversations:
            try:
                if not isinstance(conversation, dict):
                    logger.warning(
                        f"Skipping invalid conversation type: {type(conversation)}"
                    )
                    result.add_skipped(self._processor_type)
                    continue

                # Validate conversation
                if not self._validate_conversation(conversation):
                    logger.warning(
                        f"Skipping invalid conversation: {conversation.get('uuid', 'unknown')}"
                    )
                    result.add_skipped(self._processor_type)
                    continue

                # Extract conversation metadata
                title = conversation.get("name", "Untitled Conversation")
                created_at = conversation.get("created_at")
                conversation_id = conversation.get("uuid", "unknown")

                # For warning context
                context = f"[{title}] ({conversation_id})"
                logger.debug(f"Processing conversation: {context}")

                # Generate output path
                output_file = self._get_output_path(title, created_at)

                # Track for index
                conversation_index.append(
                    {
                        "name": title,  # Use the original name
                        "created_at": created_at,
                        "path": output_file.name,  # Use just the filename
                        "id": conversation_id,
                    }
                )
                logger.debug(f"Added to index: {title} ({created_at})")

                # Check if we need to regenerate
                if not config.global_config.force_generation and output_file.exists():
                    result.add_from_cache(self._processor_type)
                    result.processed += 1
                    continue

                # Convert to markdown
                try:
                    markdown = self._convert_to_markdown(conversation, config, result)
                    logger.debug(
                        f"{context} - Generated markdown content length: {len(markdown) if markdown else 0}"
                    )
                    if markdown is None:
                        logger.warning(
                            f"{context} - Skipping conversation with no content"
                        )
                        result.add_skipped(self._processor_type)
                        conversation_index.pop()  # Remove from index if conversion failed
                        continue

                    # Write output file
                    logger.debug(f"{context} - Writing to file: {output_file}")
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(markdown, encoding="utf-8")
                    logger.debug(
                        f"{context} - Wrote {len(markdown)} bytes to: {output_file}"
                    )
                    result.add_generated(self._processor_type)
                    result.processed += 1
                except (TypeError, AttributeError) as e:
                    logger.error(
                        f"{context} - Error converting conversation to markdown: {str(e)}"
                    )
                    result.add_error(
                        f"Error converting conversation to markdown: {str(e)}",
                        self._processor_type,
                    )
                    result.add_skipped(self._processor_type)
                    conversation_index.pop()  # Remove from index if conversion failed
                    continue

            except Exception as e:
                error_msg = f"Error processing conversation: {str(e)}"
                logger.error(error_msg)
                result.add_error(error_msg, self._processor_type)
                result.add_skipped(self._processor_type)
                if conversation_index:
                    conversation_index.pop()  # Remove from index if processing failed

        # Write artifact files
        artifacts_index = ["# Generated Artifacts", ""]

        # Create artifacts directory if it doesn't exist
        artifacts_dir = self.source_config.dest_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        if self._artifact_versions:
            for artifact_id, versions in self._artifact_versions.items():
                # Write individual artifact file
                artifact_file = artifacts_dir / f"{artifact_id}.md"
                artifact_content = [
                    f"# Artifact {artifact_id}",
                    "",
                    "## Content",
                    "",
                    "```",
                    versions[-1]["content"],  # Latest version
                    "```",
                    "",
                    "## Version History",
                    "",
                ]
                for version in versions:
                    artifact_content.append(
                        f"- {version['timestamp']}: {version['conversation_id']}"
                    )

                # Add related artifacts section (even if empty)
                artifact_content.extend(["", "## Related Artifacts", ""])

                # Add related artifacts if any
                related = set()
                for conv_id, artifacts in self._artifact_relationships.items():
                    if artifact_id in artifacts:
                        related.update(artifacts - {artifact_id})

                if related:
                    for related_id in sorted(related):
                        artifact_content.append(f"- {related_id} (same conversation)")

                artifact_file.write_text("\n".join(artifact_content), encoding="utf-8")

                # Add to index with content preview
                preview = versions[-1]["content"][:100]
                if len(versions[-1]["content"]) > 100:
                    preview += "..."

                artifacts_index.extend(
                    [
                        f"- {artifact_id}",
                        "",
                    ]
                )
        else:
            # No artifacts found, but don't create a placeholder
            artifacts_index.extend(
                [
                    "No artifacts found in any conversations.",
                    "",
                ]
            )

        # Write artifacts index
        (artifacts_dir / "index.md").write_text(
            "\n".join(artifacts_index), encoding="utf-8"
        )

        # Generate index file (even if empty)
        index_path = self.source_config.dest_dir / "index.md"
        index_content = ["# Claude Conversations", ""]

        # Sort conversations by date (most recent first)
        conversation_index.sort(key=lambda x: x.get("created_at") or "", reverse=True)

        # Group conversations by month
        month_groups: dict[str, list[dict[str, Any]]] = {}
        undated: list[dict[str, Any]] = []

        for conversation in conversation_index:
            created_at = conversation.get("created_at")
            if not created_at:
                undated.append(conversation)
                continue

            # Parse the date from ISO format
            try:
                date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                # Use consistent month format for grouping
                month_year = date.strftime("%B %Y")  # e.g., "January 2024"
                if month_year not in month_groups:
                    month_groups[month_year] = []
                month_groups[month_year].append(
                    {"conversation": conversation, "date": date}
                )
            except (ValueError, AttributeError):
                undated.append(conversation)

        # Sort conversations within each month by date (most recent first)
        for month_year in month_groups:
            month_groups[month_year].sort(key=lambda x: x["date"], reverse=True)

        # Add conversations by month (most recent first)
        for month_year in sorted(
            month_groups.keys(),
            key=lambda x: datetime.strptime(x, "%B %Y"),
            reverse=True,
        ):
            logger.debug(f"Adding month section: {month_year}")
            index_content.append(f"## {month_year}")
            index_content.append("")  # Add blank line after header
            for i, item in enumerate(month_groups[month_year]):
                conversation = item["conversation"]
                title = conversation.get("name", "Untitled")
                path = conversation.get("path", "")
                logger.debug(f"Adding conversation: {title} ({item['date']})")
                index_content.append(f"- [{title}]({path})")

        # Add undated conversations at the end
        if undated:
            index_content.append("## Undated Conversations")
            index_content.append("")  # Add blank line after header
            for conversation in undated:
                title = conversation.get("name", "Untitled")
                path = conversation.get("path", "")
                index_content.append(f"- [{title}]({path})")

        # Write index file
        index_content_str = "\n".join(index_content)
        logger.debug(f"Writing index file:\n{index_content_str}")
        index_path.write_text(index_content_str, encoding="utf-8")
        logger.debug(f"Wrote index file: {index_path}")

        return result

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
            content = attachment.get("content", "")
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
            logger.error(f"Error formatting text attachment: {str(e)}")
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
            # Validate required fields
            if not isinstance(conversation, dict):
                logger.warning("Invalid conversation format: not a dictionary")
                return None

            title = conversation.get("name", "Untitled Conversation")
            created_at = conversation.get("created_at")
            updated_at = conversation.get("updated_at")
            conversation_id = conversation.get("uuid", "unknown")
            messages = conversation.get("chat_messages", [])

            if not isinstance(messages, list):
                logger.warning(
                    f"Invalid messages format in conversation {conversation_id}"
                )
                return None

            # Build markdown content
            content = [
                f"# {title}",
                "",
                f"Created: {created_at or 'Unknown'}",
            ]
            if updated_at:
                content.append(f"Updated: {updated_at}")
            content.extend([f"UUID: {conversation_id}", ""])

            # Process messages
            for message in messages:
                if not isinstance(message, dict):
                    logger.warning(
                        f"Skipping invalid message in conversation {conversation_id}"
                    )
                    continue

                # Get message metadata with consistent defaults
                sender = message.get("sender")
                if sender:
                    # Capitalize first letter for human/assistant
                    if sender.lower() in ["human", "assistant"]:
                        sender = sender.title()
                    else:
                        sender = sender  # Keep original case for other senders
                else:
                    sender = "unknown"  # Use lowercase "unknown" for missing sender

                timestamp = message.get("created_at", "")
                message_id = message.get("uuid", "unknown")
                message_content = message.get("content", [])

                if not isinstance(message_content, list):
                    logger.warning(f"Invalid content format in message {message_id}")
                    continue

                # Add message header with consistent formatting
                content.append(
                    f"## {sender} ({timestamp})"
                )  # Keep original case for sender
                content.append("")

                # Process text attachments if present
                attachments = message.get("attachments", [])
                if attachments and isinstance(attachments, list):
                    for attachment in attachments:
                        if not isinstance(attachment, dict):
                            continue
                        attachment_content = self._format_text_attachment(
                            attachment,
                            message_id,
                            result,
                        )
                        if attachment_content:
                            content.append(attachment_content)
                            content.append("")

                # Process content blocks
                for block in message_content:
                    if not isinstance(block, dict):
                        logger.warning(
                            f"Skipping invalid content block in message {message_id}"
                        )
                        continue

                    block_type = block.get("type", "")
                    block_text = block.get("text", "")

                    if block_type == "text" or block_text:  # Handle missing type field
                        # Process XML tags
                        while (
                            "<antThinking>" in block_text
                            and "</antThinking>" in block_text
                        ):
                            start = block_text.find("<antThinking>")
                            end = block_text.find("</antThinking>") + len(
                                "</antThinking>"
                            )
                            thinking_text = block_text[
                                start
                                + len("<antThinking>") : block_text.find(
                                    "</antThinking>"
                                )
                            ]

                            # Process nested artifact tags
                            artifact_text = None
                            if (
                                "<antArtifact>" in thinking_text
                                and "</antArtifact>" in thinking_text
                            ):
                                art_start = thinking_text.find("<antArtifact>")
                                art_end = thinking_text.find("</antArtifact>") + len(
                                    "</antArtifact>"
                                )
                                artifact_text = thinking_text[
                                    art_start
                                    + len("<antArtifact>") : thinking_text.find(
                                        "</antArtifact>"
                                    )
                                ]
                                thinking_text = (
                                    thinking_text[:art_start] + thinking_text[art_end:]
                                )

                            block_text = (
                                block_text[:start]
                                + "\n\n💭 **Thinking Process:**\n\n"
                                + thinking_text
                                + "\n\n"
                                + block_text[end:]
                            )

                            if artifact_text:
                                block_text = (
                                    block_text[:start]
                                    + "\n\n🔨 **Generated Artifact:**\n\n```\n"
                                    + artifact_text
                                    + "\n```\n\n"
                                    + block_text[start:]
                                )
                                self._track_artifact(
                                    artifact_text, message_id, conversation_id
                                )

                        # Process remaining artifact tags
                        while (
                            "<antArtifact>" in block_text
                            and "</antArtifact>" in block_text
                        ):
                            start = block_text.find("<antArtifact>")
                            end = block_text.find("</antArtifact>") + len(
                                "</antArtifact>"
                            )
                            logger.debug(f"Block text: '{block_text}'")
                            logger.debug(f"Start index: {start}")
                            logger.debug(f"End index: {end}")

                            # Extract the artifact text between the tags
                            artifact_text = block_text[
                                start
                                + len("<antArtifact>") : block_text.find(
                                    "</antArtifact>"
                                )
                            ]
                            # Log the extracted text for debugging
                            logger.debug(f"Extracted artifact text: '{artifact_text}'")

                            # Format the block text with the artifact
                            block_text = (
                                block_text[:start]
                                + "\n\n🔨 **Generated Artifact:**\n\n```\n"
                                + artifact_text
                                + "\n```\n\n"
                                + block_text[end:]
                            )
                            logger.debug(f"Updated block text: '{block_text}'")

                            # Track the artifact
                            self._track_artifact(
                                artifact_text, message_id, conversation_id
                            )

                        content.append(block_text)
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
                        content.append("```tool-result")
                        content.append(json.dumps(block.get("content", {}), indent=2))
                        content.append("```")
                        content.append("")

            return "\n".join(content)
        except Exception as e:
            logger.error(f"Error converting conversation to markdown: {str(e)}")
            return None

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

    def _process_message_content(self, message: Dict[str, Any]) -> List[str]:
        """Process message content blocks into markdown lines.

        Args:
            message: The message to process.

        Returns:
            List of markdown lines.
        """
        lines: List[str] = []
        content = message.get("content", [])

        if not isinstance(content, list):
            logger.warning(
                f"Invalid content format in message {message.get('uuid', 'unknown')}"
            )
            return lines

        for block in content:
            if not isinstance(block, dict):
                logger.warning("Skipping invalid content block")
                continue

            # Handle text blocks
            text = block.get("text")
            if text is not None:  # Allow empty strings
                lines.extend(self._process_text_block(text))
                continue

            # Handle other block types
            block_type = block.get("type")
            if block_type:
                if block_type == "text":
                    lines.extend(self._process_text_block(block.get("text", "")))
                # Add handling for other block types as needed

        return lines

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
