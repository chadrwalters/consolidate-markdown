import logging
import base64
import mimetypes
from pathlib import Path
from typing import Optional

from openai import OpenAI

from .image import ImageProcessor
from ..processors.base import ProcessingResult

logger = logging.getLogger(__name__)

class GPTError(Exception):
    """Error during GPT processing."""
    pass

class GPTProcessor:
    """Process images using GPT-4 Vision."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)

    def describe_image(self, image_path: Path, result: ProcessingResult) -> str:
        """Get a description of an image using GPT-4 Vision."""
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        logger.debug(f"Sending image {image_path.name} to GPT-4 Vision API")

        try:
            # Read and encode image
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Prepare API request
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please describe this image in markdown format. Include relevant details about what's shown, but keep it concise. Format it as a proper markdown paragraph."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]

            # Make API request
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=300,
            )

            # Extract and return description
            description = response.choices[0].message.content
            return description.strip()

        except Exception as e:
            logger.error(f"Failed to process image with GPT-4 Vision: {str(e)}")
            return self.get_placeholder(image_path, result)

    def get_placeholder(self, image_path: Path, result: ProcessingResult) -> str:
        """Get a placeholder for when GPT processing is disabled or fails."""
        return f"[Image: {image_path.name} - GPT analysis skipped]"
