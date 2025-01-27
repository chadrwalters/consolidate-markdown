"""GPT-4 Vision integration for image analysis."""
import base64
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import openai
from ..cache import CacheManager, quick_hash
from ..processors.base import ProcessingResult

logger = logging.getLogger(__name__)

class GPTError(Exception):
    """Error during GPT processing."""
    pass

class GPTProcessor:
    """Process images using GPT-4 Vision."""

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

    def __init__(self, api_key: str, cache_manager: Optional[CacheManager] = None):
        """Initialize with OpenAI API key."""
        self.api_key = api_key
        self.cache_manager = cache_manager
        openai.api_key = api_key

    def _convert_to_supported_format(self, image_path: Path) -> Tuple[Optional[Path], bool]:
        """Convert image to a supported format if needed."""
        suffix = image_path.suffix.lower()
        if suffix in self.SUPPORTED_FORMATS:
            return image_path, False

        # Convert HEIC to JPEG using sips on macOS
        if suffix == '.heic':
            try:
                output_path = image_path.with_suffix('.jpg')
                subprocess.run(
                    ['sips', '-s', 'format', 'jpeg', str(image_path), '--out', str(output_path)],
                    check=True,
                    capture_output=True
                )
                logger.debug(f"Converted {image_path.name} to JPEG for GPT analysis")
                return output_path, True
            except Exception as e:
                logger.error(f"Failed to convert HEIC to JPEG: {e}")
                return None, False

        return None, False

    def describe_image(self, image_path: Path, result: ProcessingResult) -> str:
        """Get a description of an image using GPT-4 Vision."""
        try:
            # Convert image if needed
            supported_path, was_converted = self._convert_to_supported_format(image_path)
            if not supported_path:
                raise GPTError(f"Unsupported image format: {image_path.suffix}")

            # Read image and get hash
            with open(supported_path, "rb") as image_file:
                image_data = image_file.read()
                image_hash = quick_hash(str(image_data))

            # Check cache if available
            if self.cache_manager:
                cached = self.cache_manager.get_gpt_cache(image_hash)
                if cached is not None:  # Explicit None check
                    result.gpt_cache_hits += 1
                    logger.debug(f"Using cached GPT analysis for {image_path.name}")
                    return cached

            # Convert image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')

            # Call GPT-4 Vision
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image in detail."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )

            description = response.choices[0].message.content
            if description is None:  # Explicit None check
                raise GPTError("GPT returned empty response")

            # Cache the result if cache manager available
            if self.cache_manager:
                self.cache_manager.update_gpt_cache(image_hash, description)
                result.gpt_new_analyses += 1
                logger.debug(f"Cached new GPT analysis for {image_path.name}")

            # Clean up converted file
            if was_converted and supported_path != image_path:
                supported_path.unlink(missing_ok=True)

            return description

        except Exception as e:
            raise GPTError(f"Failed to process image with GPT: {str(e)}")

    def get_placeholder(self, image_path: Path, result: ProcessingResult) -> str:
        """Return a placeholder when GPT analysis is skipped."""
        result.images_skipped += 1
        return f"[GPT image analysis skipped for {image_path.name}]"
