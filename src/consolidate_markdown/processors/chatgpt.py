"""ChatGPT conversation export processor."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        """Process conversations from JSON file.

        Args:
            config: Global configuration.

        Returns:
            Processing result.
        """
        result = ProcessingResult()

        try:
            # Read conversations file
            conversations_file = self.source_config.src_dir / "conversations.json"
            logger.info(f"Processing ChatGPT conversations from: {conversations_file}")

            if not conversations_file.exists():
                error_msg = f"Conversations file not found: {conversations_file}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                return result

            if not conversations_file.is_file():
                error_msg = f"Conversations file is not a file: {conversations_file}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                return result

            try:
                with conversations_file.open(encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(
                    f"Successfully loaded conversations.json with {len(data) if isinstance(data, list) else 0} conversations"
                )
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON in conversations file: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                return result
            except Exception as e:
                error_msg = f"Error reading conversations file: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                return result

            # Process conversations
            if isinstance(data, list):
                for conversation in data:
                    self._process_conversation(conversation, config, result)
            else:
                error_msg = "Invalid conversations.json format - expected list"
                logger.error(error_msg)
                result.errors.append(error_msg)

            logger.info(
                f"Completed ChatGPT processing: {result.processed} conversations processed, {result.images_processed} images, {result.documents_processed} documents"
            )
            return result

        except Exception as e:
            error_msg = f"Error processing conversations: {str(e)}"
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
            logger.debug(f"{context} - No mapping found")
            return "\n".join(lines)

        try:
            # Get the mapping items in order by traversing the tree
            current_id = conversation.get("current_node")
            visited = set()  # Track visited nodes to avoid cycles

            while current_id and current_id not in visited:
                visited.add(current_id)

                msg_data = mapping.get(current_id)
                if not msg_data:
                    logger.debug(f"{context} - No message data for node: {current_id}")
                    break

                message = msg_data.get("message")
                if message and isinstance(message, dict):
                    # Check for any content (text, images, or files)
                    content = message.get("content")
                    if content:
                        if isinstance(content, str) and content.strip():
                            messages.insert(0, message)
                        elif isinstance(content, dict):
                            if (
                                content.get("parts")
                                or content.get("text")
                                or content.get("image_url")
                                or content.get("file_url")
                            ):
                                messages.insert(0, message)
                        elif isinstance(content, list):
                            for part in content:
                                if isinstance(part, str) and part.strip():
                                    messages.insert(0, message)
                                    break
                                elif isinstance(part, dict) and (
                                    part.get("text")
                                    or part.get("image_url")
                                    or part.get("file_url")
                                ):
                                    messages.insert(0, message)
                                    break

                current_id = msg_data.get("parent")

            logger.debug(
                f"{context} - Found {len(messages)} messages in tree traversal"
            )

        except Exception as e:
            logger.debug(f"{context} - Error processing mapping: {str(e)}")
            messages = []

        # Process messages
        for message in messages:
            try:
                if not isinstance(message, dict):
                    continue

                author = message.get("author", {})
                if not isinstance(author, dict):
                    continue

                role = author.get("role", "unknown")
                content = message.get("content")
                if content is None:
                    continue

                content_text = self._extract_content_text(
                    content, context, result, config
                )
                if content_text:
                    lines.extend([f"## {role.title()}", "", content_text, ""])
                    logger.debug(f"{context} - Added message with role: {role}")

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
                    if "text" in part:
                        text = part.get("text", "").strip()
                        if text:
                            content_parts.append(text)
                    elif "type" in part:
                        part_type = part.get("type")
                        if part_type == "image_url":
                            # Handle inline base64 images
                            image_url = part.get("image_url", {}).get("url", "")
                            logger.debug(
                                f"{context} - Processing image URL: {image_url[:100]}..."
                            )
                            if image_url.startswith("data:image/"):
                                # Extract image data and save to temp file
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
                            logger.debug(f"{context} - Processing file URL: {file_url}")
                            # Create output attachments directory
                            output_attachments_dir = (
                                self.source_config.dest_dir / "attachments"
                            )
                            output_attachments_dir.mkdir(exist_ok=True)
                            attachment_content = self._process_attachment(
                                Path(file_url),
                                output_attachments_dir,
                                self.attachment_processor,
                                config,
                                result,
                            )
                            if attachment_content:
                                content_parts.append(attachment_content)
                                logger.debug(f"{context} - Successfully processed file")
                            else:
                                logger.warning(f"{context} - Failed to process file")
            return "\n\n".join(content_parts) if content_parts else None
        elif isinstance(content, dict):
            if "text" in content:
                text = content.get("text", "").strip()
                if text:
                    return text
            elif "type" in content:
                part_type = content.get("type")
                if part_type == "image_url":
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
                    logger.debug(f"{context} - Processing file URL: {file_url}")
                    # Create output attachments directory
                    output_attachments_dir = self.source_config.dest_dir / "attachments"
                    output_attachments_dir.mkdir(exist_ok=True)
                    attachment_content = self._process_attachment(
                        Path(file_url),
                        output_attachments_dir,
                        self.attachment_processor,
                        config,
                        result,
                    )
                    if attachment_content:
                        logger.debug(f"{context} - Successfully processed file")
                        return attachment_content
                    else:
                        logger.warning(f"{context} - Failed to process file")
                        return "[Error processing file]"
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
        """Process an attachment and return markdown representation.

        Args:
            attachment_path: Path to the attachment
            output_dir: Directory to store processed attachments
            attachment_processor: Processor for handling attachments
            config: Global configuration
            result: Processing result tracker
            alt_text: Optional alternative text for images
            is_image: Whether the attachment is an image

        Returns:
            Markdown representation of the attachment, or None if processing failed
        """
        try:
            if not attachment_path.exists():
                logger.warning(f"Attachment not found: {attachment_path}")
                return None

            # Create output attachments directory if needed
            output_dir.mkdir(exist_ok=True)

            # Process the attachment
            temp_path, metadata = attachment_processor.process_file(
                attachment_path,
                force=config.global_config.force_generation,
                result=result,
            )

            # Copy processed file to output directory
            output_path = output_dir / attachment_path.name
            shutil.copy2(temp_path, output_path)

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

                # Format image markdown
                size_kb = metadata.size_bytes / 1024
                dimensions = metadata.dimensions or (0, 0)
                return f"""
<!-- EMBEDDED IMAGE: {attachment_path.name} -->
<details>
<summary>🖼️ {attachment_path.name} ({dimensions[0]}x{dimensions[1]}, {size_kb:.0f}KB)</summary>

{description}

</details>
"""
            else:
                # Handle other file types
                result.documents_processed += 1
                if metadata.markdown_content:
                    return f"""
<!-- EMBEDDED DOCUMENT: {attachment_path.name} -->
<details>
<summary>📄 {attachment_path.name} ({metadata.size_bytes / 1024:.0f}KB)</summary>

{metadata.markdown_content}

</details>
"""
                else:
                    return f"[Document: {attachment_path.name}]"

        except Exception as e:
            logger.error(f"Error processing attachment {attachment_path}: {str(e)}")
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
