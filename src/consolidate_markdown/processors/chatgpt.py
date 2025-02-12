"""ChatGPT conversation export processor."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.progress import Progress, TaskID

from ..attachments.processor import AttachmentProcessor
from ..cache import CacheManager
from ..config import Config, SourceConfig
from .base import SourceProcessor
from .result import ProcessingResult

logger = logging.getLogger(__name__)


class ChatGPTProcessor(SourceProcessor):
    """Process ChatGPT conversation exports into Markdown."""

    def __init__(
        self, source_config: SourceConfig, cache_manager: Optional[CacheManager] = None
    ):
        """Initialize processor with source configuration."""
        super().__init__(source_config, cache_manager)
        self.validate()

    def validate(self) -> None:
        """Validate source configuration.

        Raises:
            ValueError: If source configuration is invalid.
        """
        super().validate()

        # Check for conversations.json
        conversations_file = self.source_config.src_dir / "conversations.json"
        if not conversations_file.exists():
            logger.info(
                f"No conversations.json found in source directory: {self.source_config.src_dir}"
            )
            return
        if not conversations_file.is_file():
            raise ValueError(f"conversations.json is not a file: {conversations_file}")

    def process(self, config: Config) -> ProcessingResult:
        """Process all conversations."""
        result = ProcessingResult()

        # Create output directory
        self.source_config.dest_dir.mkdir(parents=True, exist_ok=True)

        # Load conversations
        conversations_file = self.source_config.src_dir / "conversations.json"
        if not conversations_file.exists():
            error_msg = f"Conversations file not found: {conversations_file}"
            logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)
            return result

        try:
            conversations = json.loads(conversations_file.read_text(encoding="utf-8"))
            if not isinstance(conversations, list):
                error_msg = "Invalid conversations file format: not a list"
                logger.error(error_msg)
                result.add_error(error_msg, self._processor_type)
                return result

            # Process each conversation
            for conversation in conversations:
                if content := self._process_conversation(conversation, config, result):
                    # Get output path
                    title = conversation.get("title", "Untitled Conversation")
                    create_time = datetime.strptime(
                        conversation.get("create_time", ""), "%Y-%m-%dT%H:%M:%SZ"
                    )
                    output_file = self._get_output_path(title, create_time)

                    # Write content
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(content, encoding="utf-8")

        except json.JSONDecodeError as e:
            error_msg = f"Error decoding conversations file: {str(e)}"
            logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)
        except Exception as e:
            error_msg = f"Error processing conversations: {str(e)}"
            logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)

        return result

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
                result.add_skipped(self._processor_type)

        return result

    def _process_conversation(
        self, conversation: Dict[str, Any], config: Config, result: ProcessingResult
    ) -> Optional[str]:
        """Process a single conversation."""
        try:
            if not isinstance(conversation, dict):
                error_msg = f"Invalid conversation data: {type(conversation)}"
                logger.error(error_msg)
                result.add_error(error_msg, self._processor_type)
                result.skipped += 1
                return None

            # Get required fields
            title = conversation.get("title", "Untitled Conversation")
            create_time = conversation.get("create_time", "")

            # Require title and create_time (do not require messages here so that a bad timestamp gets caught)
            if not title or not create_time:
                error_msg = "Missing required fields in conversation"
                logger.warning(error_msg)
                result.add_error(error_msg, self._processor_type)
                result.skipped += 1
                return None

            # Parse create_time using the correct call (remove extra 'datetime.')
            try:
                datetime.strptime(create_time, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                error_msg = f"Invalid create_time format: {create_time}"
                logger.warning(error_msg)
                result.add_error(error_msg, self._processor_type)
                result.skipped += 1
                return None

            # Now retrieve messages (if none, mark as an error)
            messages = conversation.get("messages", [])
            if not messages:
                error_msg = "No messages found in conversation"
                logger.warning(error_msg)
                result.add_error(error_msg, self._processor_type)
                result.skipped += 1
                return None

            # Process each message in the conversation
            content_parts = []
            for message in messages:
                processed_message = self._process_message(
                    message, conversation.get("context", ""), result, config
                )
                if processed_message:
                    content_parts.append(processed_message)

            if not content_parts:
                result.skipped += 1
                return None

            # Format the output
            output = [
                f"# {title}",
                "",
                f"Created: {create_time.replace('T', ' ').replace('Z', '')}",
            ]
            if model := conversation.get("model"):
                output.append(f"Model: {model}")
            output.extend(["", *content_parts])
            result.processed += 1
            return "\n\n".join(output)

        except Exception as e:
            error_msg = f"Error processing conversation: {str(e)}"
            logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)
            result.skipped += 1
            return None

    def _get_output_path(self, title: str, create_time: datetime) -> Path:
        """Get the output path for a conversation."""
        # Format the filename
        date_str = create_time.strftime("%Y%m%d")
        safe_title = title.replace(" ", "_").replace("/", "_")
        filename = f"{date_str} - {safe_title}.md"

        return self.source_config.dest_dir / filename

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
        try:
            # Extract metadata
            title = conversation.get("title", "Untitled Conversation")
            create_time = conversation.get("create_time")
            update_time = conversation.get("update_time")
            model = conversation.get("model", "Unknown Model")

            # Build header
            markdown_lines = [
                f"# {title}",
                "",
                f"Created: {self._format_timestamp(create_time)}",
            ]
            if update_time:
                markdown_lines.append(f"Updated: {self._format_timestamp(update_time)}")
            if model:
                markdown_lines.append(f"Model: {model}")
            markdown_lines.append("")

            # Extract messages
            messages = conversation.get("messages", [])
            if not messages:
                error_msg = "No messages found in conversation"
                logger.warning(error_msg)
                result.add_error(error_msg, self._processor_type)
                result.add_skipped(self._processor_type)
                return "\n\n".join(markdown_lines)  # Return header only

            # Process each message
            for message in messages:
                if not isinstance(message, dict):
                    error_msg = f"Invalid message format: {type(message)}"
                    logger.warning(error_msg)
                    result.add_error(error_msg, self._processor_type)
                    continue

                if "role" not in message:
                    error_msg = "Message missing required 'role' field"
                    logger.warning(error_msg)
                    result.add_error(error_msg, self._processor_type)
                    continue

                # Process message content
                content = self._process_message(message, "Message", result, config)
                if content:
                    markdown_lines.append(content)

                # Process attachments
                attachments = message.get("attachments", [])
                for attachment in attachments:
                    name = str(attachment.get("name", ""))
                    if not name:
                        continue

                    # Get attachment path
                    file_path_str = attachment.get("file_path", "")
                    if not file_path_str:
                        file_path = self.source_config.src_dir / "attachments" / name
                    else:
                        file_path = Path(file_path_str)

                    if not file_path.exists():
                        error_msg = f"Attachment not found: {name}"
                        logger.warning(error_msg)
                        result.add_error(error_msg, self._processor_type)
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

                        # Format based on type and increment counters
                        if is_image:
                            if config.global_config.no_image:
                                result.documents_processed += 1
                                markdown_lines.append(
                                    f"<!-- EMBEDDED PDF: {name} -->\n"
                                    f"<details>\n<summary>📄 {name}</summary>\n\n"
                                    f"[View PDF](attachments/{name})\n\n</details>"
                                )
                            else:
                                result.images_processed += 1
                                markdown_lines.append(
                                    f"<!-- EMBEDDED IMAGE: {name} -->\n"
                                    f"![{name}](attachments/{name})"
                                )
                        else:
                            result.documents_processed += 1
                            markdown_lines.append(
                                f"<!-- EMBEDDED PDF: {name} -->\n"
                                f"<details>\n<summary>📄 {name}</summary>\n\n"
                                f"[View PDF](attachments/{name})\n\n</details>"
                            )

                    except Exception as e:
                        error_msg = f"Error processing attachment {name}: {str(e)}"
                        logger.error(error_msg)
                        result.add_error(error_msg, self._processor_type)
                        if is_image:
                            result.add_image_skipped(self._processor_type)
                        else:
                            result.add_document_skipped(self._processor_type)

            # Combine all messages
            return "\n\n".join(markdown_lines)

        except Exception as e:
            error_msg = f"Error converting conversation to markdown: {str(e)}"
            logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)
            return "\n\n".join(markdown_lines)  # Return what we have so far

    def _extract_content_text(
        self,
        content: Dict[str, Any],
        context: str,
        result: ProcessingResult,
        config: Config,
    ) -> Optional[str]:
        """Extract text content from a content part."""
        try:
            content_type = content.get("type", "")
            if content_type == "text":
                text = str(content.get("text", ""))
                if text:
                    return text
            elif content_type == "code":
                text = str(content.get("text", ""))
                if text:
                    language = content.get("language", "")
                    return f"```{language}\n{text}\n```"
                return text
            return None
        except Exception as e:
            logger.error(f"{context} - Error processing content: {str(e)}")
            return f"[Error processing content: {str(e)}]"

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

    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from a PDF file."""
        try:
            import pdfminer.high_level

            text = pdfminer.high_level.extract_text(str(file_path))
            return text.strip() or "[PDF: No text content found]"
        except ImportError:
            return "[PDF: pdfminer-six not installed]"
        except Exception as e:
            return f"[PDF: Error extracting text - {str(e)}]"

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
        """Process a single message."""
        try:
            # Get role and content
            role = message.get("role", "")
            if not role:
                error_msg = "Message missing required 'role' field"
                logger.warning(error_msg)
                result.add_error(error_msg, self._processor_type)
                return None

            # Process message content
            content_parts = []

            # Handle string content
            if isinstance(message.get("content"), str):
                content_parts.append(message["content"])
            # Handle list of content parts
            elif isinstance(message.get("content"), list):
                for part in message["content"]:
                    if not isinstance(part, dict):
                        continue

                    part_type = part.get("type", "")

                    if part_type == "text":
                        content_parts.append(part.get("text", ""))
                    elif part_type == "code":
                        lang = part.get("language", "")
                        text = part.get("text", "")
                        if text:
                            if lang:
                                content_parts.append(f"```{lang}\n{text}\n```")
                            else:
                                content_parts.append(f"```\n{text}\n```")
                    elif part_type == "mermaid":
                        diagram = part.get("diagram", "")
                        if diagram:
                            content_parts.append(f"```mermaid\n{diagram}\n```")
                    elif part_type == "math":
                        math = part.get("math", "") or part.get("latex", "")
                        if math:
                            content_parts.append(f"$${math}$$")
                    elif part_type == "table":
                        headers = part.get("headers", [])
                        rows = part.get("rows", [])
                        if headers and rows:
                            # Create header row
                            table_lines = [
                                f"| {' | '.join(str(h) for h in headers)} |",
                                f"| {' | '.join('-' * len(str(h)) for h in headers)} |",
                            ]
                            # Add data rows
                            for row in rows:
                                table_lines.append(
                                    f"| {' | '.join(str(cell) for cell in row)} |"
                                )
                            content_parts.append("\n".join(table_lines))
                    elif part_type == "file":
                        # If message has attachments, skip inline file processing
                        if "attachments" in message and message["attachments"]:
                            continue
                        file_path = part.get("file_path", "")
                        if file_path:
                            file_path = Path(file_path)
                            if file_path.exists():
                                # Process file based on metadata
                                metadata = part.get("metadata", {})
                                if metadata.get("language"):
                                    content = file_path.read_text()
                                    content_parts.append(
                                        f"```{metadata['language']}\n{content}\n```"
                                    )
                                    result.documents_processed += 1
                                elif metadata.get("mime_type") == "application/zip":
                                    content_parts.append(f"[Archive: {file_path.name}]")
                                    result.documents_processed += 1
                                else:
                                    content_parts.append(f"[File: {file_path.name}]")
                                    result.documents_processed += 1
                            else:
                                error_msg = f"File not found: {file_path}"
                                logger.warning(error_msg)
                                result.add_error(error_msg, self._processor_type)
                    elif part_type == "image":
                        # If message has attachments, skip inline image processing
                        if "attachments" in message and message["attachments"]:
                            continue
                        image_path = part.get("image", "")
                        if not image_path:
                            error_msg = "Image content missing required 'image' field"
                            logger.warning(error_msg)
                            result.add_error(error_msg, self._processor_type)
                            continue

                        image_path = Path(image_path)
                        if not image_path.exists():
                            error_msg = f"Image file not found: {image_path}"
                            logger.warning(error_msg)
                            result.add_error(error_msg, self._processor_type)
                            continue

                        if config.global_config.no_image:
                            content_parts.append(
                                f"<!-- EMBEDDED PDF: {image_path.name} -->"
                            )
                        else:
                            content_parts.append(
                                f"<!-- EMBEDDED IMAGE: {image_path.name} -->"
                            )
                        result.documents_processed += 1
                    elif part_type not in [
                        "text",
                        "code",
                        "mermaid",
                        "math",
                        "table",
                        "file",
                        "image",
                    ]:
                        error_msg = f"Unsupported content type: {part_type}"
                        logger.warning(error_msg)
                        result.add_error(error_msg, self._processor_type)

            # Process attachments
            attachments = message.get("attachments", [])
            for attachment in attachments:
                file_path = attachment.get("file_path", "")
                name = attachment.get("name", "")

                if not file_path:
                    error_msg = "Attachment missing required 'file_path' field"
                    logger.warning(error_msg)
                    result.add_error(error_msg, self._processor_type)
                    continue

                file_path = Path(file_path)
                if not file_path.exists():
                    error_msg = f"Attachment file not found: {name or file_path}"
                    logger.warning(error_msg)
                    result.add_error(error_msg, self._processor_type)
                    continue

                mime_type = attachment.get("mime_type", "")
                attachment_name = name or file_path.name

                if mime_type == "application/pdf":
                    content_parts.append(f"<!-- EMBEDDED PDF: {attachment_name} -->")
                    result.documents_processed += 1
                elif mime_type.startswith("image/"):
                    if config.global_config.no_image:
                        content_parts.append(
                            f"<!-- EMBEDDED PDF: {attachment_name} -->"
                        )
                    else:
                        content_parts.append(
                            f"<!-- EMBEDDED IMAGE: {attachment_name} -->"
                        )
                    result.documents_processed += 1
                else:
                    content_parts.append(f"[File: {attachment_name}]")
                    result.documents_processed += 1

            # Combine all content parts
            if content_parts:
                return f"## {role.title()}\n\n{chr(10).join(content_parts)}"

            return None

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)
            return None

    def _get_conversations(self) -> List[Dict[str, Any]]:
        """Get conversations from the conversations.json file.

        Returns:
            List[Dict[str, Any]]: List of conversation dictionaries, optionally limited
                                by self.item_limit if set.
        """
        conversations_file = self.source_config.src_dir / "conversations.json"
        if not conversations_file.exists():
            conversations_file.write_text("[]")

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
