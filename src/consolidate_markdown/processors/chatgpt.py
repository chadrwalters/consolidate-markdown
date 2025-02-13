import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dateutil import tz
from rich.progress import Progress, TaskID

from consolidate_markdown.attachments.processor import AttachmentProcessor
from consolidate_markdown.cache import CacheManager
from consolidate_markdown.config import Config, SourceConfig
from consolidate_markdown.processors.base import SourceProcessor
from consolidate_markdown.processors.result import ProcessingResult


class ChatGPTProcessor(SourceProcessor):
    """Process ChatGPT conversation exports."""

    def __init__(
        self,
        source_config: SourceConfig,
        cache_manager: Optional[CacheManager] = None,
        attachment_processor: Optional[AttachmentProcessor] = None,
    ) -> None:
        """Initialize processor."""
        super().__init__(source_config, cache_manager)
        self.source_config.type = "chatgpt"
        self.logger = logging.getLogger(__name__)

    @property
    def _processor_type(self) -> str:
        """Get the processor type."""
        return "chatgpt"

    @property
    def attachment_processor(self) -> Optional[AttachmentProcessor]:
        """Get the attachment processor."""
        return self._attachment_processor

    @attachment_processor.setter
    def attachment_processor(self, value: Optional[AttachmentProcessor]) -> None:
        """Set the attachment processor."""
        self._attachment_processor = value

    def validate(self) -> None:
        """Validate configuration."""
        super().validate()

    def process(self, config: Config) -> ProcessingResult:
        """Process ChatGPT conversations."""
        result = ProcessingResult()
        result.get_processor_stats(self._processor_type)

        try:
            # Create output directory if it doesn't exist
            self.source_config.dest_dir.mkdir(parents=True, exist_ok=True)

            # Process conversations from conversations.json
            conversations = self._get_conversations()
            for conversation in conversations:
                self._process_conversation(conversation, config, result)

            # Copy existing markdown files
            markdown_dir = self.source_config.src_dir / "markdown_chats"
            if markdown_dir.exists():
                for file in markdown_dir.glob("*.md"):
                    # Copy file to output directory
                    shutil.copy2(file, self.source_config.dest_dir / file.name)
                    result.add_generated(self._processor_type)

        except Exception as e:
            error_msg = f"Error processing ChatGPT conversations: {str(e)}"
            self.logger.error(error_msg)
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
                self.logger.error(error_msg)
                result.add_error(error_msg, self._processor_type)
                result.add_skipped(self._processor_type)

        return result

    def _process_conversation(
        self,
        conversation: Dict[str, Any],
        config: Config,
        result: ProcessingResult,
    ) -> None:
        """Process a single conversation."""
        try:
            # Get conversation metadata
            title = conversation.get("title", "Untitled")
            create_time = conversation.get("create_time", 0)
            model = conversation.get("model", "unknown")

            # Format create time
            if isinstance(create_time, (int, float)):
                create_time = datetime.fromtimestamp(create_time, tz=tz.tzutc())
            elif isinstance(create_time, str):
                try:
                    create_time = datetime.strptime(create_time, "%Y-%m-%dT%H:%M:%SZ")
                    create_time = create_time.replace(tzinfo=tz.tzutc())
                except ValueError:
                    create_time = datetime.now(tz=tz.tzutc())
            else:
                create_time = datetime.now(tz=tz.tzutc())

            # Format filename
            formatted_title = re.sub(r'[<>:"/\\|?*]', "", title.replace(" ", "_"))
            filename = f"{create_time.strftime('%Y%m%d')} - {formatted_title}.md"
            output_file = self.source_config.dest_dir / filename

            # Write conversation to file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                f.write(f"Created: {create_time.strftime('%Y-%m-%d')}\n")
                if model:
                    f.write(f"Model: {model}\n")
                f.write("\n")

                # Process messages
                messages = conversation.get("messages", [])
                for message in messages:
                    self._process_message(message, f, config, result)

            result.add_generated(self._processor_type)
            result.processed += 1

        except Exception as e:
            error_msg = f"Error processing conversation: {str(e)}"
            self.logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)

    def _write_message(
        self, f: Any, conversation: Dict[str, Any], config: Config
    ) -> None:
        """Write a message to the output file."""
        role = conversation.get("role", "unknown")
        content = conversation.get("content", "")

        # Write role header
        f.write(f"## {role.capitalize()}\n\n")

        # Handle different content types
        if isinstance(content, str):
            f.write(content + "\n\n")
        elif isinstance(content, list):
            for item in content:
                self._write_content_item(item, f, config)
        else:
            f.write(str(content) + "\n\n")

    def _write_content_item(self, item: Dict[str, Any], f: Any, config: Config) -> None:
        """Write a content item to the output file."""
        item_type = item.get("type", "")

        if item_type == "text":
            f.write(item.get("text", "") + "\n\n")
        elif item_type == "code":
            language = item.get("language", "")
            code = item.get("code", "")
            if code:
                if language:
                    f.write(f"```{language}\n{code}\n```")
                else:
                    f.write(f"```\n{code}\n```")
                f.write("\n\n")
        elif item_type == "image":
            image_path = item.get("image", "")
            if image_path:
                f.write(f"![image]({image_path})\n\n")
        elif item_type == "file":
            file_path = item.get("file_path", "")
            if file_path:
                f.write(f"[file]({file_path})\n\n")

    def _get_output_path(self, title: str, create_time: datetime) -> Path:
        """Get the output path for a conversation.

        Args:
            title: The conversation title
            create_time: The conversation creation time

        Returns:
            The output path for the conversation
        """
        # Format the date prefix
        date_prefix = create_time.strftime("%Y%m%d")

        # Clean the title for use in filename
        # First replace special characters with underscores
        clean_title = re.sub(r'[\'"`&+]', "", title)  # Remove quotes and special chars
        clean_title = re.sub(
            r"[-\s_]+", "_", clean_title
        )  # Replace spaces/hyphens/underscores with single underscore
        # Then remove any other invalid characters
        clean_title = "".join(c for c in clean_title if c.isalnum() or c in "_-.")
        # Remove leading/trailing underscores
        clean_title = clean_title.strip("_")

        # Combine date and title
        filename = f"{date_prefix}_{clean_title}.md"

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
                self.logger.warning(error_msg)
                result.add_error(error_msg, self._processor_type)
                result.add_skipped(self._processor_type)
                return "\n\n".join(markdown_lines)  # Return header only

            # Process each message
            for message in messages:
                if not isinstance(message, dict):
                    error_msg = f"Invalid message format: {type(message)}"
                    self.logger.warning(error_msg)
                    result.add_error(error_msg, self._processor_type)
                    continue

                if "role" not in message:
                    error_msg = "Message missing required 'role' field"
                    self.logger.warning(error_msg)
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
                        self.logger.warning(error_msg)
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
                        self.logger.error(error_msg)
                        result.add_error(error_msg, self._processor_type)
                        if is_image:
                            result.add_image_skipped(self._processor_type)
                        else:
                            result.add_document_skipped(self._processor_type)

            # Combine all messages
            return "\n\n".join(markdown_lines)

        except Exception as e:
            error_msg = f"Error converting conversation to markdown: {str(e)}"
            self.logger.error(error_msg)
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
            self.logger.error(f"{context} - Error processing content: {str(e)}")
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
            self.logger.debug(f"Could not parse timestamp {timestamp}: {str(e)}")
            return timestamp  # Return original if parsing fails

    def _process_message(
        self,
        message: Dict[str, Any],
        f: Any,
        config: Config,
        result: ProcessingResult,
    ) -> None:
        """Process a single message."""
        try:
            # Get role and content
            role = message.get("role", "")
            if not role:
                error_msg = "Message missing required 'role' field"
                self.logger.warning(error_msg)
                result.add_error(error_msg, self._processor_type)
                return

            # Debug log the message structure
            self.logger.debug(f"Processing message with role: {role}")
            self.logger.debug(f"Message content type: {type(message.get('content'))}")
            self.logger.debug(f"Message structure: {json.dumps(message, indent=2)}")

            # Process message content
            content_parts = []
            message_content = message.get("content")

            # Handle empty or missing content
            if message_content is None:
                error_msg = "Message missing required 'content' field"
                self.logger.warning(error_msg)
                result.add_error(error_msg, self._processor_type)
                return

            # Handle string content
            if isinstance(message_content, str):
                if message_content.strip():  # Only add non-empty content
                    content_parts.append(message_content)
                else:
                    self.logger.debug("Skipping empty string content")
            # Handle list of content parts
            elif isinstance(message_content, list):
                for part in message_content:
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
                    elif part_type == "quote":
                        text = part.get("text", "")
                        if text:
                            content_parts.append(f"> {text}")
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
                            self.logger.warning(error_msg)
                            result.add_error(error_msg, self._processor_type)
                    elif part_type == "image":
                        # If message has attachments, skip inline image processing
                        if "attachments" in message and message["attachments"]:
                            continue
                        file_path = part.get("file_path", "")
                        if file_path:
                            file_path = Path(file_path)
                            if file_path.exists():
                                # Process image based on metadata
                                metadata = part.get("metadata", {})
                                if metadata.get("mime_type", "").startswith("image/"):
                                    # Create output attachments directory
                                    output_attachments_dir = (
                                        self.source_config.dest_dir / "attachments"
                                    )
                                    output_attachments_dir.mkdir(
                                        parents=True, exist_ok=True
                                    )

                                    # Copy image to output directory
                                    output_path = (
                                        output_attachments_dir / file_path.name
                                    )
                                    shutil.copy2(file_path, output_path)

                                    # Add image reference to markdown
                                    if config.global_config.no_image:
                                        result.documents_processed += 1
                                        content_parts.append(
                                            f"<!-- EMBEDDED IMAGE: {file_path.name} -->\n"
                                            f"[Image: {file_path.name}](attachments/{file_path.name})"
                                        )
                                    else:
                                        result.images_processed += 1
                                        content_parts.append(
                                            f"<!-- EMBEDDED IMAGE: {file_path.name} -->\n"
                                            f"![{file_path.name}](attachments/{file_path.name})"
                                        )
                                else:
                                    error_msg = f"Invalid image MIME type: {metadata.get('mime_type')}"
                                    self.logger.warning(error_msg)
                                    result.add_error(error_msg, self._processor_type)
                        else:
                            error_msg = f"Image not found: {file_path}"
                            self.logger.warning(error_msg)
                            result.add_error(error_msg, self._processor_type)

            # Format message with role prefix
            if content_parts:
                formatted_content = "\n\n".join(content_parts)
                if role == "user":
                    f.write(f"## User\n\n{formatted_content}\n\n")
                elif role == "assistant":
                    f.write(f"## Assistant\n\n{formatted_content}\n\n")
                elif role == "system":
                    f.write(f"## System\n\n{formatted_content}\n\n")
                else:
                    f.write(f"## {role.title()}\n\n{formatted_content}\n\n")
            else:
                self.logger.debug("No content parts to format")

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            self.logger.error(error_msg)
            result.add_error(error_msg, self._processor_type)

    def _get_conversations(self) -> List[Dict[str, Any]]:
        """Get conversations from conversations.json.

        Returns:
            List[Dict[str, Any]]: List of conversation dictionaries.
        """
        conversations_file = self.source_config.src_dir / "conversations.json"
        if not conversations_file.exists():
            self.logger.warning(
                f"No conversations.json found in source directory: {self.source_config.src_dir}"
            )
            return []

        try:
            with open(conversations_file, "r", encoding="utf-8") as f:
                conversations = json.loads(f.read())
                if not isinstance(conversations, list):
                    self.logger.warning(
                        "conversations.json does not contain a list of conversations"
                    )
                    return []
                return conversations
        except Exception as e:
            self.logger.error(f"Error reading conversations.json: {str(e)}")
            return []

    def _generate_filename(self, title: str, create_time: datetime) -> str:
        """Generate a filename from create time and title."""
        # Format date as YYYYMMDD
        date_str = create_time.strftime("%Y%m%d")

        # Clean title by replacing spaces with underscores and removing special characters
        clean_title = re.sub(r"[^\w\s-]", "", title)
        clean_title = re.sub(r"[-\s]+", "_", clean_title)

        # Return the formatted filename
        return f"{date_str} - {clean_title}.md"

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
                self.logger.warning(f"Attachment not found: {attachment_path}")
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
            self.logger.error(
                f"Error processing attachment {attachment_path}: {str(e)}"
            )
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
            self.logger.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Ensure cleanup is called when object is destroyed."""
        self.cleanup()
