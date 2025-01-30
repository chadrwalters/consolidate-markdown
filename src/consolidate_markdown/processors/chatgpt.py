"""ChatGPT conversation export processor."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..attachments.gpt import GPTProcessor
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
            if not conversations_file.is_file():
                raise ValueError(f"Conversations file not found: {conversations_file}")

            with conversations_file.open(encoding="utf-8") as f:
                data = json.load(f)

            # Process conversations
            if isinstance(data, list):
                for conversation in data:
                    self._process_conversation(conversation, config, result)
            else:
                logger.warning("Invalid conversations.json format - expected list")
                result.errors.append(
                    "Invalid conversations.json format - expected list"
                )

            return result

        except Exception as e:
            logger.error(f"Error processing conversations: {str(e)}")
            result.errors.append(f"Error processing conversations: {str(e)}")
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
            output_file = self._get_output_path(title, create_time)

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
        title = conversation.get("title", "Untitled Conversation")
        create_time = conversation.get("create_time")
        update_time = conversation.get("update_time")
        model = conversation.get("model", "Unknown Model")
        conversation_id = conversation.get("id", "unknown")

        # For warning context
        context = f"[{title}] ({conversation_id})"

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
        messages = conversation.get("messages", [])
        if messages is None:
            logger.warning(
                f"{context} - Messages list is None, defaulting to empty list"
            )
            messages = []

        if not messages:
            # Try alternate message locations
            mapping = conversation.get("mapping")
            if mapping is None:
                logger.warning(f"{context} - No mapping found in conversation")
                messages = []
            elif not isinstance(mapping, dict):
                logger.warning(
                    f"{context} - Mapping is not a dictionary: {type(mapping)}"
                )
                messages = []
            elif not mapping:
                logger.warning(f"{context} - Mapping is empty")
                messages = []
            else:
                messages = mapping.get("messages", [])
                if messages is None:
                    logger.warning(
                        f"{context} - Mapping messages is None, defaulting to empty list"
                    )
                    messages = []
                elif not messages:
                    # Handle nested message structure
                    messages = []
                    try:
                        # Convert mapping items to list and filter out None values
                        mapping_items = []
                        for msg_id, msg_data in mapping.items():
                            if msg_id is None or msg_data is None:
                                continue
                            if not isinstance(msg_data, dict):
                                continue
                            mapping_items.append((msg_id, msg_data))

                        logger.debug(
                            f"{context} - Processing {len(mapping_items)} messages from mapping"
                        )

                        for msg_id, msg_data in mapping_items:
                            message = msg_data.get("message")
                            if message is None:
                                continue

                            if isinstance(message, dict):
                                # Extract author/role info first
                                author = message.get("author", {})
                                role = (
                                    author.get("role", "unknown")
                                    if isinstance(author, dict)
                                    else "unknown"
                                )

                                # Extract content with proper fallbacks
                                content = message.get("content", {})
                                content_text = None

                                if content is None:
                                    continue

                                if isinstance(content, str):
                                    content_text = content.strip()
                                elif isinstance(content, dict):
                                    # Try multiple content extraction strategies
                                    if "text" in content and content["text"].strip():
                                        content_text = content["text"].strip()
                                    elif "parts" in content:
                                        parts = content.get("parts", [])
                                        if isinstance(parts, list):
                                            logger.debug(
                                                f"{context} - Processing message parts ({len(parts)} parts)"
                                            )
                                            content_parts = []
                                            for part in parts:
                                                if (
                                                    isinstance(part, str)
                                                    and part.strip()
                                                ):
                                                    content_parts.append(part.strip())
                                                elif isinstance(part, dict):
                                                    if (
                                                        "text" in part
                                                        and part["text"].strip()
                                                    ):
                                                        content_parts.append(
                                                            part["text"].strip()
                                                        )
                                                    elif "image_url" in part:
                                                        # Process image through attachment processor
                                                        image_url = part["image_url"][
                                                            "url"
                                                        ]
                                                        attachment_md = (
                                                            self._process_attachment(
                                                                image_url,
                                                                "image",
                                                                config,
                                                                result,
                                                            )
                                                        )
                                                        if attachment_md:
                                                            content_parts.append(
                                                                attachment_md
                                                            )
                                                        else:
                                                            content_parts.append(
                                                                f"[Image: {image_url}]"
                                                            )
                                                    elif (
                                                        "type" in part
                                                        and part["type"] == "text"
                                                        and part.get("text", "").strip()
                                                    ):
                                                        content_parts.append(
                                                            part["text"].strip()
                                                        )
                                            content_text = (
                                                "\n\n".join(content_parts)
                                                if content_parts
                                                else None
                                            )
                                    elif all(
                                        k in content
                                        for k in ["content_type", "language"]
                                    ):
                                        # Handle messages with response_format_name
                                        if "response_format_name" in content:
                                            content_text = content.get(
                                                "text", ""
                                            ).strip()
                                        elif content.get("text", "").strip():
                                            content_text = content["text"].strip()
                                    elif (
                                        "user_profile" in content
                                        or "user_instructions" in content
                                    ):
                                        profile_parts = []
                                        if content.get("user_profile", "").strip():
                                            profile_parts.append(
                                                f"**User Profile:**\n{content['user_profile'].strip()}"
                                            )
                                        if content.get("user_instructions", "").strip():
                                            profile_parts.append(
                                                f"**User Instructions:**\n{content['user_instructions'].strip()}"
                                            )
                                        content_text = (
                                            "\n\n".join(profile_parts)
                                            if profile_parts
                                            else None
                                        )
                                    elif (
                                        "custom_instructions" in content
                                        and content["custom_instructions"].strip()
                                    ):
                                        content_text = f"**Custom Instructions:**\n{content['custom_instructions'].strip()}"

                                    if not content_text:
                                        logger.debug(
                                            f"{context} - No extractable text content found"
                                        )
                                        continue
                                else:
                                    logger.debug(
                                        f"{context} - Unsupported content type: {type(content)}"
                                    )
                                    continue

                                if not content_text:
                                    continue

                                lines.extend(
                                    [f"## {role.title()}", "", content_text, ""]
                                )
                            else:
                                logger.debug(f"{context} - Skipping non-dict message")
                    except Exception as e:
                        logger.warning(
                            f"{context} - Error processing mapping: {str(e)}"
                        )
                        messages = []

        # Ensure messages is always iterable
        if messages is None:
            logger.debug(f"{context} - Messages became None after processing")
            messages = []
        elif not isinstance(messages, (list, tuple)):
            logger.debug(f"{context} - Messages is not iterable ({type(messages)})")
            messages = []

        for message in messages:
            if message is None:
                continue

            if not isinstance(message, dict):
                logger.debug(f"{context} - Invalid message format: {type(message)}")
                continue

            role = message.get("role", "unknown")
            content = message.get("content")

            if content is None:
                continue

            # Try to extract meaningful content
            content_text = None

            if isinstance(content, list):
                # Handle structured content
                content_parts = []
                for part in content:
                    if part is None:
                        continue
                    if isinstance(part, dict):
                        if "text" in part and part["text"].strip():
                            content_parts.append(part["text"].strip())
                        elif "image_url" in part:
                            # Process image through attachment processor
                            image_url = part["image_url"]["url"]
                            attachment_md = self._process_attachment(
                                image_url, "image", config, result
                            )
                            if attachment_md:
                                content_parts.append(attachment_md)
                            else:
                                content_parts.append(f"[Image: {image_url}]")
                        elif "file_url" in part:
                            # Process file through attachment processor
                            file_url = part["file_url"]["url"]
                            attachment_md = self._process_attachment(
                                file_url, "file", config, result
                            )
                            if attachment_md:
                                content_parts.append(attachment_md)
                            else:
                                content_parts.append(f"[File: {file_url}]")
                    elif isinstance(part, str) and part.strip():
                        content_parts.append(part.strip())
                content_text = "\n\n".join(content_parts) if content_parts else None
            elif isinstance(content, dict):
                # Handle dictionary content
                if "text" in content and content["text"].strip():
                    content_text = content["text"].strip()
                elif "image_url" in content:
                    # Process image through attachment processor
                    image_url = content["image_url"]["url"]
                    attachment_md = self._process_attachment(
                        image_url, "image", config, result
                    )
                    content_text = (
                        attachment_md if attachment_md else f"[Image: {image_url}]"
                    )
                elif "file_url" in content:
                    # Process file through attachment processor
                    file_url = content["file_url"]["url"]
                    attachment_md = self._process_attachment(
                        file_url, "file", config, result
                    )
                    content_text = (
                        attachment_md if attachment_md else f"[File: {file_url}]"
                    )
                elif "content_type" in content and "parts" in content:
                    # Handle structured content with content_type and parts
                    if content["content_type"] in ["text", "multimodal_text"]:
                        content_parts = []
                        parts = content.get("parts")
                        if parts is not None:
                            logger.debug(
                                f"{context} - Processing {len(parts)} content parts"
                            )
                            for part in parts:
                                if part is None:
                                    continue
                                if isinstance(part, str) and part.strip():
                                    content_parts.append(part.strip())
                                elif isinstance(part, dict):
                                    if "text" in part and part["text"].strip():
                                        content_parts.append(part["text"].strip())
                                    elif "image_url" in part:
                                        # Process image through attachment processor
                                        image_url = part["image_url"]["url"]
                                        attachment_md = self._process_attachment(
                                            image_url, "image", config, result
                                        )
                                        if attachment_md:
                                            content_parts.append(attachment_md)
                                        else:
                                            content_parts.append(
                                                f"[Image: {image_url}]"
                                            )
                                    elif "file_url" in part:
                                        # Process file through attachment processor
                                        file_url = part["file_url"]["url"]
                                        attachment_md = self._process_attachment(
                                            file_url, "file", config, result
                                        )
                                        if attachment_md:
                                            content_parts.append(attachment_md)
                                        else:
                                            content_parts.append(f"[File: {file_url}]")
                                    elif (
                                        "type" in part
                                        and part["type"] == "text"
                                        and part.get("text", "").strip()
                                    ):
                                        content_parts.append(part["text"].strip())
                        content_text = (
                            "\n\n".join(content_parts) if content_parts else None
                        )
                    else:
                        logger.debug(
                            f"{context} - Unsupported content_type: {content['content_type']}"
                        )
                # Handle language-specific content format
                elif any(
                    all(k in content for k in keys)
                    for keys in [
                        ["content_type", "language", "text"],
                        ["content_type", "language", "response_format_name", "text"],
                    ]
                ):
                    if content.get("text", "").strip():
                        content_text = content["text"].strip()
                # Handle user profile/instructions content
                elif all(
                    k in content
                    for k in ["content_type", "user_profile", "user_instructions"]
                ):
                    profile_parts = []
                    if content.get("user_profile", "").strip():
                        profile_parts.append("**User Profile:**")
                        profile_parts.append(content["user_profile"].strip())
                    if content.get("user_instructions", "").strip():
                        profile_parts.append("**User Instructions:**")
                        profile_parts.append(content["user_instructions"].strip())
                    content_text = "\n\n".join(profile_parts) if profile_parts else None
                # Handle custom instructions content
                elif "content_type" in content and "custom_instructions" in content:
                    if content.get("custom_instructions", "").strip():
                        content_text = f"**Custom Instructions:**\n\n{content['custom_instructions'].strip()}"
                # Handle result/summary content
                elif all(k in content for k in ["content_type", "result", "summary"]):
                    summary_parts = []
                    if content.get("summary", "").strip():
                        summary_parts.append("**Summary:**")
                        summary_parts.append(content["summary"].strip())
                    if content.get("result", "").strip():
                        summary_parts.append("**Result:**")
                        summary_parts.append(content["result"].strip())
                    if content.get("assets"):
                        summary_parts.append("**Assets:**")
                        summary_parts.append(str(content["assets"]))
                    content_text = "\n\n".join(summary_parts) if summary_parts else None
                else:
                    logger.debug(f"{context} - Unknown content format")
            elif isinstance(content, str) and content.strip():
                content_text = content.strip()
            else:
                logger.debug(f"{context} - Invalid content type: {type(content)}")

            if not content_text:
                continue

            lines.extend([f"## {role.title()}", "", content_text, ""])

        return "\n".join(lines)

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
                dt = datetime.fromisoformat(create_time.replace("Z", "+00:00"))
                date_prefix = dt.strftime("%Y%m%d")
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse create_time: {create_time}")

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
        """Format an ISO timestamp into a readable string.

        Args:
            timestamp: ISO format timestamp string.

        Returns:
            Formatted date string.
        """
        if not timestamp:
            return "Unknown"

        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        except (ValueError, AttributeError):
            return timestamp  # Return original if parsing fails

    def _process_attachment(
        self,
        attachment_url: str,
        content_type: str,
        config: Config,
        result: ProcessingResult,
    ) -> Optional[str]:
        """Process an attachment and return markdown representation.

        Args:
            attachment_url: URL or path to the attachment
            content_type: Type of attachment (image, file, etc)
            config: Global configuration
            result: Processing result tracker

        Returns:
            Markdown representation of the attachment, or None if processing failed
        """
        try:
            # Parse the attachment path
            attachment_path = Path(attachment_url)
            if not attachment_path.exists():
                logger.warning(f"Attachment not found: {attachment_url}")
                return None

            # Create output attachments directory
            output_attachments_dir = self.source_config.dest_dir / "attachments"
            output_attachments_dir.mkdir(exist_ok=True)

            # Process the attachment
            temp_path, metadata = self.attachment_processor.process_file(
                attachment_path,
                force=config.global_config.force_generation,
                result=result,
            )

            # Copy processed file to output directory
            output_path = output_attachments_dir / attachment_path.name
            shutil.copy2(temp_path, output_path)

            # Handle different attachment types
            if metadata.is_image:
                result.images_processed += 1
                # Get image description if enabled
                description = ""
                if not config.global_config.no_image:
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
            logger.error(f"Error processing attachment {attachment_url}: {str(e)}")
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
