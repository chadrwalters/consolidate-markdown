"""GPT image analysis processor."""

import base64
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam

from ..cache import CacheManager, quick_hash
from ..processors.result import ProcessingResult

logger = logging.getLogger(__name__)


class GPTError(Exception):
    """Error during GPT processing."""

    pass


class GPTProcessor:
    """Process images using GPT-4 Vision."""

    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

    def __init__(self, api_key: str, cache_manager: Optional[CacheManager] = None):
        """Initialize with OpenAI API key."""
        self.api_key = api_key
        self.cache_manager = cache_manager

        # Set OpenAI logging to INFO level before creating client
        logging.getLogger("openai").setLevel(logging.INFO)
        logging.getLogger("openai._base_client").setLevel(logging.INFO)
        logging.getLogger("httpx").setLevel(logging.INFO)

        self.client = OpenAI(api_key=api_key)

    def _convert_to_supported_format(
        self, image_path: Path
    ) -> Tuple[Optional[Path], bool]:
        """Convert image to a supported format if needed."""
        suffix = image_path.suffix.lower()
        if suffix in self.SUPPORTED_FORMATS:
            return image_path, False

        # Convert HEIC to JPEG using sips on macOS
        if suffix == ".heic":
            try:
                output_path = image_path.with_suffix(".jpg")
                subprocess.run(
                    [
                        "sips",
                        "-s",
                        "format",
                        "jpeg",
                        str(image_path),
                        "--out",
                        str(output_path),
                    ],
                    check=True,
                    capture_output=True,
                )
                logger.debug(f"Converted {image_path.name} to JPEG for GPT analysis")
                return output_path, True
            except Exception as e:
                logger.error(f"Failed to convert HEIC to JPEG: {e}")
                return None, False

        return None, False

    def describe_image(
        self, image_path: Path, result: ProcessingResult, processor_type: str
    ) -> str:
        """Get GPT description of image.

        Args:
            image_path: Path to the image file
            result: The processing result to update
            processor_type: The type of processor requesting the analysis
        """
        # Generate cache key from image content
        image_hash = quick_hash(str(image_path.read_bytes()))

        # Check cache first
        if self.cache_manager:
            cached = self.cache_manager.get_gpt_cache(image_hash)
            if cached:
                logger.debug(f"Cache hit for GPT analysis: {image_hash}")
                result.add_gpt_from_cache(processor_type)
                return str(cached)

        logger.debug(f"Cache miss for GPT analysis: {image_hash}")

        # Convert image to base64
        with open(image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()

        # Create API request with proper type annotation
        messages: list[ChatCompletionUserMessageParam] = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in detail."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
                    },
                ],
            }
        ]

        # Log request without base64 data for debugging
        logger.debug("Sending GPT request for image analysis (base64 data omitted)")

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=300,
            )
            description = str(response.choices[0].message.content)
            result.add_gpt_generated(processor_type)

            # Cache the result
            if self.cache_manager:
                self.cache_manager.update_gpt_cache(image_hash, description)

            return description

        except Exception as e:
            logger.error(f"GPT API error: {str(e)}")
            result.add_gpt_skipped(processor_type)
            return "[Error analyzing image]"

    def get_placeholder(
        self, image_path: Path, result: ProcessingResult, processor_type: str
    ) -> str:
        """Return a placeholder when GPT analysis is skipped.

        Args:
            image_path: Path to the image file
            result: The processing result to update
            processor_type: The type of processor requesting the analysis
        """
        result.add_gpt_skipped(processor_type)
        return f"[GPT image analysis skipped for {image_path.name}]"
