"""GPT-4 Vision processor for image analysis."""

import base64  # Standard library
import logging  # Standard library
import subprocess  # Standard library
from pathlib import Path  # Standard library
from typing import Any, Dict, List, Optional, Tuple, cast

from openai import OpenAI  # External dependency: openai
from openai.types.chat import ChatCompletionMessageParam  # External dependency: openai

from ..cache import CacheManager, quick_hash
from ..config import VALID_MODELS, GlobalConfig
from ..processors.result import ProcessingResult

logger = logging.getLogger(__name__)


class GPTError(Exception):
    """Error during GPT processing."""

    pass


class GPTProcessor:
    """Process images using GPT-4 Vision (OpenAI/OpenRouter)."""

    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

    def __init__(
        self, config: GlobalConfig, cache_manager: Optional[CacheManager] = None
    ):
        """Initialize with configuration object.

        Args:
            config: Global configuration containing API settings
            cache_manager: Optional cache manager for GPT results
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.cache_manager = cache_manager
        self.provider = config.api_provider
        self.current_model = config.models.default_model
        self.client: Optional[OpenAI] = None

        # Set OpenAI logging to INFO level before creating client
        logging.getLogger("openai").setLevel(logging.INFO)
        logging.getLogger("openai._base_client").setLevel(logging.INFO)
        logging.getLogger("httpx").setLevel(logging.INFO)

        # Initialize client based on provider
        try:
            if self.provider == "openai":
                if not config.openai_key:
                    raise GPTError(
                        "OpenAI API key is required when using OpenAI provider"
                    )
                # Note: Proxies should be configured via environment variables (HTTP_PROXY, HTTPS_PROXY)
                # instead of passing a 'proxies' parameter to the OpenAI client
                client_params: Dict[str, Any] = {
                    "api_key": config.openai_key,
                    "base_url": config.openai_base_url,
                }
                # Remove proxies if present (not supported in OpenAI v1.0+)
                client_params.pop("proxies", None)
                self.client = OpenAI(**client_params)
            elif self.provider == "openrouter":
                if not config.openrouter_key:
                    raise GPTError(
                        "OpenRouter API key is required when using OpenRouter provider"
                    )
                # Note: Proxies should be configured via environment variables (HTTP_PROXY, HTTPS_PROXY)
                # instead of passing a 'proxies' parameter to the OpenAI client
                router_client_params: Dict[str, Any] = {
                    "api_key": config.openrouter_key,
                    "base_url": config.openrouter_base_url,
                }
                # Remove proxies if present (not supported in OpenAI v1.0+)
                router_client_params.pop("proxies", None)
                self.client = OpenAI(**router_client_params)
            else:
                raise GPTError(f"Unsupported API provider: {self.provider}")
        except TypeError as e:
            # Handle initialization errors gracefully for testing
            logger.warning(f"OpenAI client initialization error: {str(e)}")
            self.client = None

    def set_model(self, model_alias: Optional[str] = None) -> None:
        """Set the current model to use.

        Args:
            model_alias: Optional alias of the model to use. If None, uses default model.

        Raises:
            GPTError: If the model alias is invalid or model is not supported by provider.
        """
        if model_alias is None:
            self.current_model = self.config.models.default_model
            return

        # Check if this is a direct model name
        if model_alias in VALID_MODELS.get(self.provider, []):
            self.current_model = model_alias
            return

        # Look up model by alias
        if model_alias in self.config.models.alternate_models:
            model = self.config.models.alternate_models[model_alias]
            if model in VALID_MODELS.get(self.provider, []):
                self.current_model = model
            else:
                raise GPTError(
                    f"Model '{model}' from alias '{model_alias}' is not supported by provider '{self.provider}'"
                )
        else:
            raise GPTError(f"Invalid model alias: {model_alias}")

    def analyze_image(
        self,
        image_path: Path,
        model_alias: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> str:
        """Analyze an image using the specified model.

        Args:
            image_path: Path to the image file
            model_alias: Optional alias of the model to use. If None, uses current model.
            prompt: Optional custom prompt for the analysis

        Returns:
            Analysis result as string

        Raises:
            GPTError: If there's an error processing the image
        """
        # Set model if specified
        if model_alias is not None:
            self.set_model(model_alias)

        # Check if we have a cached result
        if self.cache_manager:
            cache_key = f"{image_path}:{self.current_model}"
            cached = self.cache_manager.get_gpt_cache(cache_key)
            if cached:
                return cached

        try:
            # Prepare image data
            with open(image_path, "rb") as f:
                image_data = f.read()
                image_b64 = base64.b64encode(image_data).decode("utf-8")

            # Default prompt if none provided
            if not prompt:
                prompt = "Please describe this image in detail, including any text, objects, colors, and layout."

            # Prepare API call based on provider
            if self.provider == "openai":
                response = self._call_openai_api(image_b64, prompt)
            else:  # openrouter
                response = self._call_openrouter_api(image_b64, prompt)

            if response is None:
                raise GPTError("API returned no response")

            # Cache the result if we have a cache manager
            if self.cache_manager:
                self.cache_manager.update_gpt_cache(cache_key, response)

            return response

        except Exception as e:
            raise GPTError(f"Error analyzing image with {self.current_model}: {str(e)}")

    def _call_openai_api(self, image_b64: str, prompt: str) -> str:
        """Call OpenAI API for image analysis.

        Args:
            image_b64: Base64 encoded image data
            prompt: Analysis prompt

        Returns:
            Analysis result

        Raises:
            GPTError: If the API call fails
        """
        if not self.client:
            return "GPT image analysis is disabled."

        try:
            # Format message according to test expectations - single message with content array
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ],
                }
            ]

            # Cast the messages to the expected type
            typed_messages = cast(List[ChatCompletionMessageParam], messages)

            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=typed_messages,
                max_tokens=500,
            )
            # Log API request at debug level
            logger.debug(f"GPT API request to {self.provider} completed")

            result = response.choices[0].message.content
            if result is None:
                raise GPTError("OpenAI API returned no content")
            return str(result)

        except Exception as e:
            raise GPTError(f"OpenAI API error: {str(e)}")

    def _call_openrouter_api(self, image_b64: str, prompt: str) -> str:
        """Call OpenRouter API for image analysis.

        Args:
            image_b64: Base64 encoded image data
            prompt: Analysis prompt

        Returns:
            Analysis result

        Raises:
            GPTError: If the API call fails
        """
        if not self.client:
            return "GPT image analysis is disabled."

        try:
            # Format message according to test expectations - single message with content array
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ],
                }
            ]

            # Cast the messages to the expected type
            typed_messages = cast(List[ChatCompletionMessageParam], messages)

            response = self.client.chat.completions.create(
                model=self.current_model,
                messages=typed_messages,
                max_tokens=500,
            )
            # Log API request at debug level
            logger.debug(f"GPT API request to {self.provider} completed")

            result = response.choices[0].message.content
            if result is None:
                raise GPTError(
                    f"OpenRouter API returned no content for model {self.current_model}"
                )
            return str(result)

        except Exception as e:
            raise GPTError(
                f"OpenRouter API error with model {self.current_model}: {str(e)}"
            )

    def describe_image(
        self,
        image_path: Path,
        result: ProcessingResult,
        processor_type: str,
    ) -> str:
        """Get GPT description of image.

        Args:
            image_path: Path to the image file
            result: The processing result to update
            processor_type: The type of processor requesting the analysis
        """
        # Convert image to supported format if needed
        converted_path, needs_cleanup = self._convert_to_supported_format(image_path)
        if converted_path is None:
            logger.error(f"Could not convert {image_path} to a supported format")
            result.add_gpt_skipped(processor_type)
            return "[Error: Unsupported image format]"

        try:
            # Generate cache key from image content
            image_hash = quick_hash(str(converted_path.read_bytes()))

            # Check cache first
            if self.cache_manager:
                cached = self.cache_manager.get_gpt_cache(image_hash)
                if cached:
                    logger.debug(f"Cache hit for GPT analysis: {image_hash}")
                    result.add_gpt_from_cache(processor_type)
                    return str(cached)

            logger.debug(f"Cache miss for GPT analysis: {image_hash}")

            # Convert image to base64
            with open(converted_path, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode()

            # Create API request with proper type annotation
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What's in this image? Describe it in detail.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            },
                        },
                    ],
                }
            ]

            # Cast the messages to the expected type
            typed_messages = cast(List[ChatCompletionMessageParam], messages)

            # Log request without base64 data for debugging
            logger.debug(
                f"Sending GPT request to {self.provider} for image analysis (base64 data omitted)"
            )

            # Check if client is available
            if not self.client:
                logger.error("GPT client is not initialized")
                result.add_gpt_skipped(processor_type)
                return "[Error: GPT client not available]"

            response = self.client.chat.completions.create(
                model=self.current_model,
                messages=typed_messages,
                max_tokens=300,
            )
            # Log API request at debug level
            logger.debug(f"GPT API request to {self.provider} completed")

            content = response.choices[0].message.content
            if content is None:
                logger.error(f"GPT API returned no content ({self.provider})")
                result.add_gpt_skipped(processor_type)
                return "[Error: No content returned]"

            description = str(content)
            result.add_gpt_generated(processor_type)

            # Cache the result
            if self.cache_manager:
                self.cache_manager.update_gpt_cache(image_hash, description)

            # Log the description at debug level instead of info
            logger.debug(
                f"Generated description for {image_path.name}: {description[:100]}..."
            )

            return description

        except Exception as e:
            logger.error(f"GPT API error ({self.provider}): {str(e)}")
            result.add_gpt_skipped(processor_type)
            return "[Error analyzing image]"
        finally:
            # Clean up temporary file if needed
            if needs_cleanup and converted_path and converted_path.exists():
                try:
                    converted_path.unlink()
                except Exception as e:
                    logger.warning(
                        f"Failed to clean up temporary file {converted_path}: {e}"
                    )

    def get_placeholder(
        self,
        image_path: Path,
        result: ProcessingResult,
        processor_type: str,
    ) -> str:
        """Get a placeholder description for an image.

        Args:
            image_path: Path to the image file
            result: The processing result to update
            processor_type: The type of processor requesting the analysis
        """
        result.add_gpt_skipped(processor_type)
        return f"[GPT image analysis skipped for {image_path.name}]"

    def _convert_to_supported_format(
        self, image_path: Path
    ) -> Tuple[Optional[Path], bool]:
        """Convert image to a supported format if needed."""
        suffix = image_path.suffix.lower()
        if suffix in self.SUPPORTED_FORMATS:
            return image_path, False

        # For SVG files, look for PNG version in metadata
        if suffix == ".svg":
            # Look for PNG version in same directory as SVG
            png_path = image_path.with_suffix(".png")
            if png_path.exists():
                return png_path, False

            # Try to convert SVG to PNG using rsvg-convert
            try:
                output_path = image_path.with_suffix(".png")
                subprocess.run(
                    ["rsvg-convert", "-o", str(output_path), str(image_path)],
                    check=True,
                    capture_output=True,
                )
                logger.debug(f"Converted {image_path.name} to PNG for GPT analysis")
                return output_path, True
            except Exception as e:
                logger.error(f"Failed to convert SVG to PNG: {e}")
                return None, False

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
