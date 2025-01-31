"""ChatGPT conversation export processor."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..attachments.gpt import GPTProcessor
from ..attachments.processor import AttachmentProcessor
from ..cache import CacheManager
from ..config import Config, SourceConfig
from .base import SourceProcessor
from .result import ProcessingResult

logger = logging.getLogger(__name__)


class ChatGPTProcessor(SourceProcessor):
    """Process ChatGPT conversation exports into Markdown."""

    def __init__(self, source_config: SourceConfig):
        """Initialize processor with source configuration."""
        super().__init__(source_config)
        self.validate()

        # Initialize cache manager
        self.cache_manager = CacheManager(source_config.dest_dir.parent)

    def validate(self) -> None:
        """Validate source configuration.

        Raises:
            ValueError: If source configuration is invalid.
        """
        super().validate()

        # Check for conversations.json
        conversations_file = self.source_config.src_dir / "conversations.json"
        if not conversations_file.exists():
            raise ValueError(
                f"conversations.json not found in source directory: {self.source_config.src_dir}"
            )
        if not conversations_file.is_file():
            raise ValueError(f"conversations.json is not a file: {conversations_file}")

    def _process_impl(self, config: Config) -> ProcessingResult:
        """Process ChatGPT export files.

        Args:
            config: The configuration to use.

        Returns:
            The processing result.
        """
        result = ProcessingResult()

        # Create output directory if it doesn't exist
        self.source_config.dest_dir.mkdir(parents=True, exist_ok=True)

        # Process each conversation
        for conversation in self._get_conversations():
            try:
                self._process_conversation(conversation, config, result)
            except Exception as e:
                error_msg = f"Error processing conversation: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        return result

    def _process_conversation(
        self, conversation: Dict[str, Any], config: Config, result: ProcessingResult
    ) -> None:
        """Process a single conversation."""
        try:
            if not isinstance(conversation, dict):
                logger.warning(
                    f"Skipping invalid conversation type: {type(conversation)}"
                )
                result.skipped += 1
                return

            # Extract conversation metadata
            title = conversation.get("title", "Untitled Conversation")
            create_time = conversation.get("create_time")
            conversation_id = conversation.get("id", "unknown")

            # For warning context
            context = f"[{title}] ({conversation_id})"
            logger.debug(f"Processing conversation: {context}")

            # Generate output path
            output_file = self._get_output_path(title or "Untitled", create_time)

            # Check if we need to regenerate
            if not config.global_config.force_generation and output_file.exists():
                result.from_cache += 1
                return

            # Convert to markdown
            try:
                markdown = self._convert_to_markdown(conversation, config, result)
                if not markdown:
                    logger.warning(f"{context} - Skipping conversation with no content")
                    result.skipped += 1
                    return

                # Write output file
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(markdown, encoding="utf-8")
                logger.debug(f"Wrote conversation to: {output_file}")
                result.regenerated += 1
                result.processed += 1
            except (TypeError, AttributeError) as e:
                logger.error(
                    f"{context} - Error converting conversation to markdown: {str(e)}"
                )
                result.errors.append(
                    f"Error converting conversation to markdown: {str(e)}"
                )
                result.skipped += 1
                return

        except Exception as e:
            logger.error(f"Error processing conversation: {str(e)}")
            result.errors.append(f"Error processing conversation: {str(e)}")
            result.skipped += 1
            return

    def _convert_to_markdown(
        self, conversation: Dict[str, Any], config: Config, result: ProcessingResult
    ) -> str:
        """Convert conversation to markdown format.

        Args:
            conversation: The conversation data to convert
            config: Global configuration
            result: Processing result tracker

        Returns:
            Markdown formatted string
        """
        if conversation is None:
            logger.debug("Cannot convert None conversation to markdown")
            return ""

        # Extract metadata
        title = conversation.get("title") or "Untitled Conversation"
        create_time = conversation.get("create_time")
        update_time = conversation.get("update_time")
        model = conversation.get("model", "Unknown Model")
        conversation_id = conversation.get("id", "unknown")

        # For warning context
        context = f"[{title}] ({conversation_id})"
        logger.debug(f"Processing conversation: {context}")

        # Build markdown content - standardized format
        lines = [
            f"# {title}",
            "",
            f"Created: {self._format_timestamp(create_time)}",
        ]
        if update_time:
            lines.append(f"Updated: {self._format_timestamp(update_time)}")
        if model:
            lines.append(f"Model: {model}")
        lines.append("")

        # Add messages
        messages: List[Dict[str, Any]] = []
        mapping = conversation.get("mapping")
        if mapping is None:
            # Try legacy format with direct messages list
            messages = conversation.get("messages", [])
            if not messages:
                logger.debug(f"{context} - No messages found")
                return "\n".join(lines)
        else:
            try:
                # Build a map of parent to children
                parent_to_children: Dict[
                    Optional[str], List[Tuple[str, Dict[str, Any]]]
                ] = {}
                for msg_id, msg_data in mapping.items():
                    # Skip if msg_data is None
                    if msg_data is None:
                        logger.debug(
                            f"{context} - Skipping None message data for ID: {msg_id}"
                        )
                        continue

                    # Get message safely with fallback to empty dict
                    message = (
                        msg_data.get("message", {})
                        if isinstance(msg_data, dict)
                        else {}
                    )

                    # Skip if message is invalid
                    if not isinstance(message, dict):
                        logger.debug(
                            f"{context} - Skipping invalid message format for ID: {msg_id}"
                        )
                        continue

                    parent_id = message.get("parent")
                    if parent_id not in parent_to_children:
                        parent_to_children[parent_id] = []
                    parent_to_children[parent_id].append((msg_id, message))

                # Start with root messages (parent=None)
                root_messages = parent_to_children.get(None, [])
                message_chain = []

                # Helper function to traverse the tree in order
                def traverse_messages(msg_list):
                    for msg_id, message in sorted(msg_list, key=lambda x: x[0]):
                        if isinstance(message, dict):  # Only add valid messages
                            message_chain.append(message)
                            children = parent_to_children.get(msg_id, [])
                            traverse_messages(children)
                        else:
                            logger.debug(
                                f"{context} - Skipping invalid message in traversal: {msg_id}"
                            )

                # Traverse the tree
                traverse_messages(root_messages)
                messages = message_chain

                if messages:
                    logger.debug(
                        f"{context} - Found {len(messages)} messages in tree traversal"
                    )
                else:
                    logger.debug(
                        f"{context} - No valid messages found in tree traversal"
                    )

            except Exception as e:
                logger.debug(f"{context} - Error processing mapping: {str(e)}")
                # Try legacy format as fallback
                messages = conversation.get("messages", [])
                if messages:
                    logger.debug(
                        f"{context} - Falling back to legacy format with {len(messages)} messages"
                    )

        # Process messages
        for message in messages:
            try:
                if not isinstance(message, dict):
                    continue

                message_text = self._process_message(message, context, result, config)
                if message_text:
                    lines.extend([message_text, ""])
                    logger.debug(f"{context} - Added message")

            except Exception as e:
                logger.debug(f"{context} - Error processing message: {str(e)}")
                continue

        return "\n".join(lines)

    def _extract_content_text(
        self,
        content: Any,
        context: str,
        result: ProcessingResult,
        config: Config,
    ) -> Optional[str]:
        """Extract text content from various content formats."""
        if content is None:
            return None

        if isinstance(content, str):
            return content.strip()
        elif isinstance(content, list):
            content_parts = []
            for part in content:
                if part is None:
                    continue
                if isinstance(part, str):
                    content_parts.append(part.strip())
                elif isinstance(part, dict):
                    if "type" in part:
                        part_type = part.get("type")
                        if part_type == "text":
                            text = part.get("text", "")  # Don't strip text parts
                            if text:
                                content_parts.append(text)
                        elif part_type == "code":
                            language = part.get("language", "")
                            code = part.get("text", "").strip()
                            if code:
                                content_parts.append(f"```{language}\n{code}\n```")
                        elif part_type == "image_url":
                            # Handle inline base64 images
                            image_url = part.get("image_url", {}).get("url", "")
                            logger.debug(
                                f"{context} - Processing image URL: {image_url[:100]}..."
                            )
                            if image_url.startswith("data:image/"):
                                try:
                                    import base64

                                    # Parse data URL
                                    header, encoded = image_url.split(",", 1)
                                    image_data = base64.b64decode(encoded)
                                    # Get format from header
                                    format_match = header.split(";")[0].split("/")[-1]
                                    ext = f".{format_match}" if format_match else ".jpg"

                                    # Create temp file
                                    temp_dir = self._create_temp_dir(config)
                                    temp_file = (
                                        temp_dir
                                        / f"inline_image_{result.images_processed}{ext}"
                                    )
                                    temp_file.write_bytes(image_data)
                                    logger.debug(
                                        f"{context} - Saved base64 image to: {temp_file}"
                                    )

                                    # Create output attachments directory
                                    output_attachments_dir = (
                                        self.source_config.dest_dir / "attachments"
                                    )
                                    output_attachments_dir.mkdir(exist_ok=True)

                                    # Process like a regular image
                                    attachment_content = self._process_attachment(
                                        Path(str(temp_file)),
                                        output_attachments_dir,
                                        self.attachment_processor,
                                        config,
                                        result,
                                        is_image=True,
                                    )
                                    if attachment_content:
                                        content_parts.append(attachment_content)
                                        logger.debug(
                                            f"{context} - Successfully processed base64 image"
                                        )
                                    else:
                                        logger.warning(
                                            f"{context} - Failed to process base64 image"
                                        )
                                except Exception as e:
                                    logger.error(
                                        f"{context} - Error processing base64 image: {str(e)}"
                                    )
                                    content_parts.append(
                                        "[Error processing inline image]"
                                    )
                            else:
                                # Handle regular image URLs
                                logger.debug(
                                    f"{context} - Processing regular image URL"
                                )
                                # Create output attachments directory
                                output_attachments_dir = (
                                    self.source_config.dest_dir / "attachments"
                                )
                                output_attachments_dir.mkdir(exist_ok=True)
                                attachment_content = self._process_attachment(
                                    Path(image_url),
                                    output_attachments_dir,
                                    self.attachment_processor,
                                    config,
                                    result,
                                    is_image=True,
                                )
                                if attachment_content:
                                    content_parts.append(attachment_content)
                                    logger.debug(
                                        f"{context} - Successfully processed image URL"
                                    )
                                else:
                                    logger.warning(
                                        f"{context} - Failed to process image URL"
                                    )
                        elif part_type == "file":
                            # Handle file attachments
                            file_url = part.get("file_url", {}).get("url", "")
                            metadata = part.get("metadata", {})
                            language = metadata.get("language", "")
                            logger.debug(f"{context} - Processing file URL: {file_url}")
                            try:
                                # Read file content directly
                                file_path = Path(file_url)
                                if file_path.exists():
                                    file_content = file_path.read_text(encoding="utf-8")
                                    result.documents_processed += 1
                                    # Check file extension first
                                    ext = file_path.suffix.lower()
                                    if ext == ".zip":
                                        content_parts.append(
                                            f"[Archive: {file_path.name}]"
                                        )
                                    elif ext == ".pdf":
                                        content_parts.append(
                                            f"<!-- EMBEDDED DOCUMENT: {file_path.name} -->\n<details>\n<summary>📄 {file_path.name}</summary>\n\n{file_content}\n\n</details>"
                                        )
                                    elif language:
                                        content_parts.append(
                                            f"```{language}\n{file_content}\n```"
                                        )
                                    else:
                                        content_parts.append(file_content)
                                else:
                                    # Try processing as attachment
                                    output_attachments_dir = (
                                        self.source_config.dest_dir / "attachments"
                                    )
                                    output_attachments_dir.mkdir(exist_ok=True)
                                    attachment_content = self._process_attachment(
                                        file_path,
                                        output_attachments_dir,
                                        self.attachment_processor,
                                        config,
                                        result,
                                    )
                                    if attachment_content:
                                        result.documents_processed += 1
                                        # Check file extension first
                                        ext = file_path.suffix.lower()
                                        if ext == ".zip":
                                            content_parts.append(
                                                f"[Archive: {file_path.name}]"
                                            )
                                        elif ext == ".pdf":
                                            content_parts.append(
                                                f"<!-- EMBEDDED DOCUMENT: {file_path.name} -->\n<details>\n<summary>📄 {file_path.name}</summary>\n\n{attachment_content}\n\n</details>"
                                            )
                                        elif language:
                                            content_parts.append(
                                                f"```{language}\n{attachment_content}\n```"
                                            )
                                        else:
                                            content_parts.append(attachment_content)
                                    else:
                                        logger.warning(
                                            f"{context} - Failed to process file"
                                        )
                            except Exception as e:
                                logger.error(
                                    f"{context} - Error processing file: {str(e)}"
                                )
                                content_parts.append(
                                    f"[Error processing file: {str(e)}]"
                                )
                        elif part_type == "tool_use":
                            # Handle tool usage
                            tool = part.get("tool", "")
                            input_text = part.get("input", "").strip()
                            if input_text:
                                content_parts.append(
                                    f"Tool: {tool}\nInput:\n```\n{input_text}\n```"
                                )
                        elif part_type == "tool_result":
                            # Handle tool results
                            output = part.get("output", "").strip()
                            if output:
                                content_parts.append(f"Output: {output}")
                        elif part_type == "table":
                            # Handle tables
                            headers = part.get("headers", [])
                            rows = part.get("rows", [])
                            if headers and rows:
                                table_parts = []
                                # Add headers
                                table_parts.append("| " + " | ".join(headers) + " |")
                                # Add separator
                                table_parts.append(
                                    "| " + " | ".join(["---"] * len(headers)) + " |"
                                )
                                # Add rows
                                for row in rows:
                                    table_parts.append(
                                        "| "
                                        + " | ".join(str(cell) for cell in row)
                                        + " |"
                                    )
                                content_parts.append("\n".join(table_parts))
                        elif part_type == "math":
                            # Handle math equations
                            latex = part.get("latex", "").strip()
                            if latex:
                                content_parts.append(f"$${latex}$$")
                        elif part_type == "mermaid":
                            # Handle mermaid diagrams
                            diagram = part.get("diagram", "").strip()
                            if diagram:
                                content_parts.append(f"```mermaid\n{diagram}\n```")
                    elif "text" in part:
                        text = part.get("text", "")  # Don't strip text parts
                        if text:
                            if part.get("type") == "code":
                                language = part.get("language", "")
                                content_parts.append(f"```{language}\n{text}\n```")
                            else:
                                content_parts.append(text)
            return "\n\n".join(content_parts) if content_parts else None
        elif isinstance(content, dict):
            if "type" in content:
                part_type = content.get("type")
                if part_type == "text":
                    text = content.get("text", "")  # Don't strip text parts
                    if text:
                        return text
                elif part_type == "code":
                    language = content.get("language", "")
                    code = content.get("text", "").strip()
                    if code:
                        return f"```{language}\n{code}\n```"
                elif part_type == "image_url":
                    # Handle inline base64 images (same as above)
                    image_url = content.get("image_url", {}).get("url", "")
                    logger.debug(
                        f"{context} - Processing image URL: {image_url[:100]}..."
                    )
                    if image_url.startswith("data:image/"):
                        try:
                            import base64

                            # Parse data URL
                            header, encoded = image_url.split(",", 1)
                            image_data = base64.b64decode(encoded)
                            # Get format from header
                            format_match = header.split(";")[0].split("/")[-1]
                            ext = f".{format_match}" if format_match else ".jpg"

                            # Create temp file
                            temp_dir = self._create_temp_dir(config)
                            temp_file = (
                                temp_dir
                                / f"inline_image_{result.images_processed}{ext}"
                            )
                            temp_file.write_bytes(image_data)
                            logger.debug(
                                f"{context} - Saved base64 image to: {temp_file}"
                            )

                            # Create output attachments directory
                            output_attachments_dir = (
                                self.source_config.dest_dir / "attachments"
                            )
                            output_attachments_dir.mkdir(exist_ok=True)

                            # Process like a regular image
                            attachment_content = self._process_attachment(
                                Path(str(temp_file)),
                                output_attachments_dir,
                                self.attachment_processor,
                                config,
                                result,
                                is_image=True,
                            )
                            if attachment_content:
                                logger.debug(
                                    f"{context} - Successfully processed base64 image"
                                )
                                return attachment_content
                            else:
                                logger.warning(
                                    f"{context} - Failed to process base64 image"
                                )
                                return "[Error processing inline image]"
                        except Exception as e:
                            logger.error(
                                f"{context} - Error processing base64 image: {str(e)}"
                            )
                            return "[Error processing inline image]"
                    else:
                        # Handle regular image URLs
                        logger.debug(f"{context} - Processing regular image URL")
                        # Create output attachments directory
                        output_attachments_dir = (
                            self.source_config.dest_dir / "attachments"
                        )
                        output_attachments_dir.mkdir(exist_ok=True)
                        attachment_content = self._process_attachment(
                            Path(image_url),
                            output_attachments_dir,
                            self.attachment_processor,
                            config,
                            result,
                            is_image=True,
                        )
                        if attachment_content:
                            logger.debug(
                                f"{context} - Successfully processed image URL"
                            )
                            return attachment_content
                        else:
                            logger.warning(f"{context} - Failed to process image URL")
                            return "[Error processing image URL]"
                elif part_type == "file":
                    # Handle file attachments
                    file_url = content.get("file_url", {}).get("url", "")
                    metadata = content.get("metadata", {})
                    language = metadata.get("language", "")
                    logger.debug(f"{context} - Processing file URL: {file_url}")
                    try:
                        # Read file content directly
                        file_path = Path(file_url)
                        if file_path.exists():
                            file_content = file_path.read_text(encoding="utf-8")
                            result.documents_processed += 1
                            # Check file extension first
                            ext = file_path.suffix.lower()
                            if ext == ".zip":
                                return f"[Archive: {file_path.name}]"
                            elif ext == ".pdf":
                                return f"<!-- EMBEDDED DOCUMENT: {file_path.name} -->\n<details>\n<summary>📄 {file_path.name}</summary>\n\n{file_content}\n\n</details>"
                            elif language:
                                return f"```{language}\n{file_content}\n```"
                            return file_content
                        else:
                            # Try processing as attachment
                            output_attachments_dir = (
                                self.source_config.dest_dir / "attachments"
                            )
                            output_attachments_dir.mkdir(exist_ok=True)
                            attachment_content = self._process_attachment(
                                file_path,
                                output_attachments_dir,
                                self.attachment_processor,
                                config,
                                result,
                            )
                            if attachment_content:
                                result.documents_processed += 1
                                # Check file extension first
                                ext = file_path.suffix.lower()
                                if ext == ".zip":
                                    return f"[Archive: {file_path.name}]"
                                elif ext == ".pdf":
                                    return f"<!-- EMBEDDED DOCUMENT: {file_path.name} -->\n<details>\n<summary>📄 {file_path.name}</summary>\n\n{attachment_content}\n\n</details>"
                                elif language:
                                    return f"```{language}\n{attachment_content}\n```"
                                return attachment_content
                            else:
                                logger.warning(f"{context} - Failed to process file")
                                return "[Error processing file]"
                    except Exception as e:
                        logger.error(f"{context} - Error processing file: {str(e)}")
                        return f"[Error processing file: {str(e)}]"
                elif part_type == "tool_use":
                    # Handle tool usage
                    tool = content.get("tool", "")
                    input_text = content.get("input", "").strip()
                    if input_text:
                        return f"Tool: {tool}\nInput:\n```\n{input_text}\n```"
                elif part_type == "tool_result":
                    # Handle tool results
                    output = content.get("output", "").strip()
                    if output:
                        return f"Output: {output}"
                elif part_type == "table":
                    # Handle tables
                    headers = content.get("headers", [])
                    rows = content.get("rows", [])
                    if headers and rows:
                        table_parts = []
                        # Add headers
                        table_parts.append("| " + " | ".join(headers) + " |")
                        # Add separator
                        table_parts.append(
                            "| " + " | ".join(["---"] * len(headers)) + " |"
                        )
                        # Add rows
                        for row in rows:
                            table_parts.append(
                                "| " + " | ".join(str(cell) for cell in row) + " |"
                            )
                        return "\n".join(table_parts)
                elif part_type == "math":
                    # Handle math equations
                    latex = content.get("latex", "").strip()
                    if latex:
                        return f"$${latex}$$"
                elif part_type == "mermaid":
                    # Handle mermaid diagrams
                    diagram = content.get("diagram", "").strip()
                    if diagram:
                        return f"```mermaid\n{diagram}\n```"
            elif "text" in content:
                text = content.get("text", "")  # Don't strip text parts
                if text:
                    if content.get("type") == "code":
                        language = content.get("language", "")
                        return f"```{language}\n{text}\n```"
                    return text
            elif "parts" in content:
                parts = content.get("parts")
                if parts is None:
                    return None
                if not isinstance(parts, list):
                    return None
                content_parts = []
                for part in parts:
                    if part is None:
                        continue
                    if isinstance(part, str) and part.strip():
                        content_parts.append(part.strip())
                return "\n\n".join(content_parts) if content_parts else None
        return None

    def _get_output_path(self, title: str, create_time: Optional[str] = None) -> Path:
        """Get output path for a conversation.

        Args:
            title: Conversation title.
            create_time: Optional creation timestamp.

        Returns:
            Path to write markdown file.
        """
        # Get date prefix from create_time
        date_prefix = "00000000"  # Default if no date
        if create_time:
            try:
                # First try parsing as Unix timestamp
                try:
                    dt = datetime.fromtimestamp(float(create_time))
                    date_prefix = dt.strftime("%Y%m%d")
                except (ValueError, TypeError):
                    # If that fails, try ISO format
                    dt = datetime.fromisoformat(create_time.replace("Z", "+00:00"))
                    date_prefix = dt.strftime("%Y%m%d")
            except (ValueError, AttributeError, TypeError) as e:
                logger.debug(f"Could not parse create_time {create_time}: {str(e)}")

        # Sanitize title for use as filename
        safe_title = "".join(
            c for c in title if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        safe_title = safe_title.replace(" ", "_")

        # Create output directory if it doesn't exist
        self.source_config.dest_dir.mkdir(parents=True, exist_ok=True)

        # Format as "YYYYMMDD - Title.md"
        filename = f"{date_prefix} - {safe_title}.md"
        return self.source_config.dest_dir / filename

    def _format_timestamp(self, timestamp: Optional[str]) -> str:
        """Format a timestamp into a readable string.

        Args:
            timestamp: Timestamp string (either ISO format or Unix timestamp)

        Returns:
            Formatted date string.
        """
        if not timestamp:
            return "Unknown"

        try:
            # First try parsing as Unix timestamp (float)
            try:
                dt = datetime.fromtimestamp(float(timestamp))
                return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
            except (ValueError, TypeError):
                # If that fails, try ISO format
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        except (ValueError, AttributeError, TypeError) as e:
            logger.debug(f"Could not parse timestamp {timestamp}: {str(e)}")
            return timestamp  # Return original if parsing fails

    def _process_attachment(
        self,
        attachment_path: Path,
        output_dir: Path,
        attachment_processor: AttachmentProcessor,
        config: Config,
        result: ProcessingResult,
        alt_text: Optional[str] = None,
        is_image: bool = False,
    ) -> Optional[str]:
        """Process an attachment file and return its markdown representation."""
        try:
            # Process attachment
            temp_path, metadata = attachment_processor.process_file(
                attachment_path, config.global_config.force_generation, result
            )

            # Copy processed file to output directory
            output_path = output_dir / attachment_path.name
            shutil.copy2(temp_path, output_path)

            # Get relative path for markdown
            rel_path = Path("attachments") / attachment_path.name

            # Handle different attachment types
            if metadata.is_image:
                result.images_processed += 1
                # Get image description if enabled
                description = alt_text or ""
                if not config.global_config.no_image and not description:
                    try:
                        gpt = GPTProcessor(
                            config.global_config.openai_key or "dummy-key",
                            self.cache_manager,
                        )
                        description = gpt.describe_image(temp_path, result)
                    except Exception as e:
                        logger.error(f"GPT processing failed for {temp_path}: {str(e)}")
                        description = f"[Error analyzing image: {str(e)}]"

                # Format image markdown with metadata
                size_kb = metadata.size_bytes / 1024
                dimensions = metadata.dimensions or (0, 0)

                # Format timestamps
                created = (
                    datetime.fromtimestamp(metadata.created_time).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if metadata.created_time
                    else "Unknown"
                )
                modified = (
                    datetime.fromtimestamp(metadata.modified_time).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if metadata.modified_time
                    else "Unknown"
                )

                # Add error message if present
                error_note = f"\n\n**Note:** {metadata.error}" if metadata.error else ""

                return f"""
<!-- EMBEDDED IMAGE: {attachment_path.name} -->
<details>
<summary>🖼️ {attachment_path.name} ({dimensions[0]}x{dimensions[1]}, {size_kb:.1f}KB)</summary>

**Type:** {metadata.mime_type or "Unknown"}
**Size:** {size_kb:.1f}KB
**Dimensions:** {dimensions[0]}x{dimensions[1]}px
**Created:** {created}
**Modified:** {modified}
**Hash:** {metadata.file_hash or "Not available"}{error_note}

{description}

![{attachment_path.name}]({rel_path})

</details>
"""
            else:
                # Handle other file types
                result.documents_processed += 1
                size_kb = metadata.size_bytes / 1024
                ext = attachment_path.suffix.lower()

                # Format timestamps
                created = (
                    datetime.fromtimestamp(metadata.created_time).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if metadata.created_time
                    else "Unknown"
                )
                modified = (
                    datetime.fromtimestamp(metadata.modified_time).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if metadata.modified_time
                    else "Unknown"
                )

                # Add error message if present
                error_note = f"\n\n**Note:** {metadata.error}" if metadata.error else ""

                # Special handling for different file types
                if ext == ".zip":
                    return f"""
<!-- EMBEDDED ARCHIVE: {attachment_path.name} -->
<details>
<summary>📦 {attachment_path.name} ({size_kb:.1f}KB)</summary>

**Type:** {metadata.mime_type or "Unknown"}
**Size:** {size_kb:.1f}KB
**Created:** {created}
**Modified:** {modified}
**Hash:** {metadata.file_hash or "Not available"}{error_note}

[Download Archive]({rel_path})

</details>
"""
                elif ext == ".pdf":
                    return f"""
<!-- EMBEDDED PDF: {attachment_path.name} -->
<details>
<summary>📄 {attachment_path.name} ({size_kb:.1f}KB)</summary>

**Type:** {metadata.mime_type or "Unknown"}
**Size:** {size_kb:.1f}KB
**Created:** {created}
**Modified:** {modified}
**Hash:** {metadata.file_hash or "Not available"}{error_note}

[View PDF]({rel_path})

{metadata.markdown_content or ""}

</details>
"""
                elif metadata.markdown_content:
                    return f"""
<!-- EMBEDDED DOCUMENT: {attachment_path.name} -->
<details>
<summary>📄 {attachment_path.name} ({size_kb:.1f}KB)</summary>

**Type:** {metadata.mime_type or "Unknown"}
**Size:** {size_kb:.1f}KB
**Created:** {created}
**Modified:** {modified}
**Hash:** {metadata.file_hash or "Not available"}{error_note}

{metadata.markdown_content}

[Download Original]({rel_path})

</details>
"""
                else:
                    # Generic file handling
                    icon = "📄"  # Default icon
                    if ext in {".mp3", ".wav", ".m4a", ".ogg"}:
                        icon = "🎵"
                    elif ext in {".mp4", ".mov", ".avi", ".mkv"}:
                        icon = "🎬"
                    elif ext in {".doc", ".docx"}:
                        icon = "📝"
                    elif ext in {".xls", ".xlsx"}:
                        icon = "📊"
                    elif ext in {".ppt", ".pptx"}:
                        icon = "📽️"
                    elif ext in {".zip", ".rar", ".7z", ".tar", ".gz"}:
                        icon = "📦"

                    return f"""
<!-- EMBEDDED FILE: {attachment_path.name} -->
<details>
<summary>{icon} {attachment_path.name} ({size_kb:.1f}KB)</summary>

**Type:** {metadata.mime_type or "Unknown"}
**Size:** {size_kb:.1f}KB
**Created:** {created}
**Modified:** {modified}
**Hash:** {metadata.file_hash or "Not available"}{error_note}

[Download File]({rel_path})

</details>
"""

        except Exception as e:
            logger.error(f"Error processing attachment {attachment_path}: {str(e)}")
            return f"[Error processing attachment {attachment_path.name}: {str(e)}]"

    def cleanup(self) -> None:
        """Clean up temporary files."""
        try:
            if self._attachment_processor is not None:
                self._attachment_processor.cleanup()
                self._attachment_processor = None
            self._cleanup_temp_dir()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Ensure cleanup is called when object is destroyed."""
        self.cleanup()

    def _process_message(
        self,
        message: Dict[str, Any],
        context: str,
        result: ProcessingResult,
        config: Config,
    ) -> Optional[str]:
        """Process a single message and return its formatted content."""
        if not message:
            return None

        # Get role from message
        role = message.get("role", "unknown")
        if not role or role == "unknown":
            author = message.get("author", {})
            if isinstance(author, dict):
                role = author.get("role", "unknown")
                name = author.get("name", "")
                if name:
                    role = f"{role} ({name})"

        # Get content and attachments
        content = message.get("content", "")
        attachments = message.get("attachments", [])

        # Process content
        content_parts = []
        if isinstance(content, str):
            content_parts.append(content)
        else:
            content_text = self._extract_content_text(content, context, result, config)
            if content_text:
                content_parts.append(content_text)

        # Process attachments
        for attachment in attachments:
            name = attachment.get("name")
            if not name:
                continue

            # Get attachment path
            attachment_path = self.source_config.src_dir / "attachments" / name
            if not attachment_path.exists():
                logger.warning(f"{context} - Attachment not found: {name}")
                continue

            # Create output attachments directory
            output_attachments_dir = self.source_config.dest_dir / "attachments"
            output_attachments_dir.mkdir(exist_ok=True)

            # Process attachment
            is_image = attachment.get("mime_type", "").startswith("image/")
            attachment_content = self._process_attachment(
                attachment_path,
                output_attachments_dir,
                self.attachment_processor,
                config,
                result,
                is_image=is_image,
            )
            if attachment_content:
                content_parts.append(attachment_content)

        if not content_parts:
            return None

        # Format message with role and content
        role = role.lower()  # Normalize role for comparison
        if role == "system":
            return f"## System\n\n{'\n\n'.join(content_parts)}"
        elif role == "user":
            return f"## User\n\n{'\n\n'.join(content_parts)}"
        elif role == "assistant":
            return f"## Assistant\n\n{'\n\n'.join(content_parts)}"
        else:
            return f"## {role.title()}\n\n{'\n\n'.join(content_parts)}"

    def _get_conversations(self) -> List[Dict[str, Any]]:
        """Get conversations from the conversations.json file.

        Returns:
            List[Dict[str, Any]]: List of conversation dictionaries
        """
        conversations_file = self.source_config.src_dir / "conversations.json"
        if not conversations_file.exists():
            raise FileNotFoundError(
                f"Conversations file not found: {conversations_file}"
            )

        try:
            with open(conversations_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError(
                        "Invalid conversations.json format - expected a list of conversations"
                    )
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in conversations file: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error reading conversations file: {str(e)}")
