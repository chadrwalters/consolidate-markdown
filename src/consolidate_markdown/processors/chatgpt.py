"""ChatGPT conversation export processor."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.progress import Progress, TaskID

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
                result.add_error(error_msg, self._processor_type)

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
                result.add_skipped(self._processor_type)
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
                result.add_from_cache(self._processor_type)
                return

            # Convert to markdown
            try:
                markdown = self._convert_to_markdown(conversation, config, result)
                if not markdown:
                    logger.warning(f"{context} - Skipping conversation with no content")
                    result.add_skipped(self._processor_type)
                    return

                # Write output file
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(markdown, encoding="utf-8")
                logger.debug(f"Wrote conversation to: {output_file}")
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
            logger.error(f"Error processing conversation: {str(e)}")
            result.add_error(
                f"Error processing conversation: {str(e)}", self._processor_type
            )
            result.add_skipped(self._processor_type)
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
                            file_path_str = str(part.get("file_path", ""))
                            if file_path_str:
                                try:
                                    file_path = Path(file_path_str)
                                    if file_path.exists() and file_path.is_file():
                                        file_content = file_path.read_text(
                                            encoding="utf-8"
                                        )
                                        language = str(
                                            part.get("metadata", {}).get("language", "")
                                        )
                                        mime_type = str(
                                            part.get("metadata", {}).get(
                                                "mime_type", ""
                                            )
                                        )
                                        if mime_type == "application/zip":
                                            content_parts.append(
                                                f"[Archive: {file_path.name}]"
                                            )
                                        elif mime_type == "application/pdf":
                                            content_parts.append(
                                                f"<!-- EMBEDDED PDF: {file_path.name} -->\n"
                                                f"<details>\n<summary>📄 {file_path.name}</summary>\n\n"
                                                f"[View PDF](attachments/{file_path.name})\n\n</details>"
                                            )
                                        elif language:
                                            content_parts.append(
                                                f"```{language}\n{file_content}\n```"
                                            )
                                        else:
                                            content_parts.append(file_content)
                                        result.documents_processed += 1
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
                    file_path_str = str(content.get("file_path", ""))
                    if file_path_str:
                        try:
                            file_path = Path(file_path_str)
                            if file_path.exists() and file_path.is_file():
                                file_content = file_path.read_text(encoding="utf-8")
                                language = str(
                                    content.get("metadata", {}).get("language", "")
                                )
                                mime_type = str(
                                    content.get("metadata", {}).get("mime_type", "")
                                )
                                if mime_type == "application/zip":
                                    return f"[Archive: {file_path.name}]"
                                elif mime_type == "application/pdf":
                                    return f"<!-- EMBEDDED PDF: {file_path.name} -->\n<details>\n<summary>📄 {file_path.name}</summary>\n\n"
                                    f"[View PDF](attachments/{file_path.name})\n\n</details>"
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
                                        return f"<!-- EMBEDDED PDF: {file_path.name} -->\n<details>\n<summary>📄 {file_path.name}</summary>\n\n"
                                        f"[View PDF](attachments/{file_path.name})\n\n</details>"
                                    elif language:
                                        return (
                                            f"```{language}\n{attachment_content}\n```"
                                        )
                                    return attachment_content
                                else:
                                    logger.warning(
                                        f"{context} - Failed to process file"
                                    )
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
        role = str(message.get("role", "unknown"))
        if not role or role == "unknown":
            author = message.get("author", {})
            if isinstance(author, dict):
                role = str(author.get("role", "unknown"))
                name = str(author.get("name", ""))
                if name:
                    role = f"{role} ({name})"

        # Get content and attachments
        content = message.get("content", "")
        attachments = message.get("attachments", [])

        # Process content
        content_parts = []
        if isinstance(content, str):
            content_parts.append(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    part_type = str(part.get("type", ""))
                    if part_type == "text":
                        text = str(part.get("text", ""))
                        if text:
                            content_parts.append(text)
                    elif part_type == "code":
                        language = str(part.get("language", ""))
                        code = str(part.get("text", "")).strip()
                        if code:
                            content_parts.append(f"```{language}\n{code}\n```")
                    elif part_type == "math":
                        latex = str(part.get("latex", "")).strip()
                        if latex:
                            content_parts.append(f"$${latex}$$")
                    elif part_type == "table":
                        headers = [str(h) for h in part.get("headers", [])]
                        rows = [
                            [str(cell) for cell in row] for row in part.get("rows", [])
                        ]
                        if headers and rows:
                            table_parts = []
                            table_parts.append("| " + " | ".join(headers) + " |")
                            table_parts.append(
                                "| " + " | ".join(["---"] * len(headers)) + " |"
                            )
                            for row in rows:
                                table_parts.append("| " + " | ".join(row) + " |")
                            content_parts.append("\n".join(table_parts))
                    elif part_type == "mermaid":
                        diagram = str(part.get("diagram", "")).strip()
                        if diagram:
                            content_parts.append(f"```mermaid\n{diagram}\n```")
                    elif part_type == "file":
                        file_path_str = str(part.get("file_path", ""))
                        if file_path_str:
                            try:
                                file_path = Path(file_path_str)
                                if file_path.exists() and file_path.is_file():
                                    file_content = file_path.read_text(encoding="utf-8")
                                    language = str(
                                        part.get("metadata", {}).get("language", "")
                                    )
                                    mime_type = str(
                                        part.get("metadata", {}).get("mime_type", "")
                                    )
                                    if mime_type == "application/zip":
                                        content_parts.append(
                                            f"[Archive: {file_path.name}]"
                                        )
                                    elif mime_type == "application/pdf":
                                        content_parts.append(
                                            f"<!-- EMBEDDED PDF: {file_path.name} -->\n"
                                            f"<details>\n<summary>📄 {file_path.name}</summary>\n\n"
                                            f"[View PDF](attachments/{file_path.name})\n\n</details>"
                                        )
                                    elif language:
                                        content_parts.append(
                                            f"```{language}\n{file_content}\n```"
                                        )
                                    else:
                                        content_parts.append(file_content)
                                    result.documents_processed += 1
                            except Exception as e:
                                logger.error(
                                    f"{context} - Error processing file: {str(e)}"
                                )
                                content_parts.append(
                                    f"[Error processing file: {str(e)}]"
                                )

        # Process attachments
        for attachment in attachments:
            name = str(attachment.get("name", ""))
            if not name:
                continue

            # Get attachment path
            file_path_str = str(attachment.get("file_path", ""))
            if not file_path_str:
                file_path = self.source_config.src_dir / "attachments" / name
            else:
                file_path = Path(file_path_str)

            if not file_path.exists():
                logger.warning(f"{context} - Attachment not found: {name}")
                continue

            # Create output attachments directory
            output_attachments_dir = self.source_config.dest_dir / "attachments"
            output_attachments_dir.mkdir(parents=True, exist_ok=True)

            # Process attachment
            is_image = str(attachment.get("mime_type", "")).startswith("image/")
            try:
                # Copy file to output directory
                output_path = output_attachments_dir / name
                shutil.copy2(file_path, output_path)

                # Format based on type
                if is_image:
                    if config.global_config.no_image:
                        result.documents_processed += 1
                        content_parts.append(
                            f"<!-- EMBEDDED PDF: {name} -->\n"
                            f"<details>\n<summary>📄 {name}</summary>\n\n"
                            f"[View PDF](attachments/{name})\n\n</details>"
                        )
                    else:
                        result.images_processed += 1
                        content_parts.append(
                            f"<!-- EMBEDDED IMAGE: {name} -->\n"
                            f"![{name}](attachments/{name})"
                        )
                else:
                    result.documents_processed += 1
                    content_parts.append(
                        f"<!-- EMBEDDED PDF: {name} -->\n"
                        f"<details>\n<summary>📄 {name}</summary>\n\n"
                        f"[View PDF](attachments/{name})\n\n</details>"
                    )
            except Exception as e:
                logger.error(
                    f"{context} - Error processing attachment {name}: {str(e)}"
                )
                if is_image:
                    result.add_image_skipped(self._processor_type)
                else:
                    result.add_document_skipped(self._processor_type)

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
            List[Dict[str, Any]]: List of conversation dictionaries, optionally limited
                                by self.item_limit if set.
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

                # Sort conversations by create_time in descending order (newest first)
                data.sort(key=lambda x: x.get("create_time", ""), reverse=True)

                # Apply limit if set
                if hasattr(self, "item_limit") and self.item_limit is not None:
                    logger.debug(
                        f"Limiting to {self.item_limit} most recent conversations"
                    )
                    data = data[: self.item_limit]

                return data

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in conversations file: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error reading conversations file: {str(e)}")
