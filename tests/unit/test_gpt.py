from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from consolidate_markdown.attachments.gpt import GPTError, GPTProcessor
from consolidate_markdown.cache import CacheManager
from consolidate_markdown.config import GlobalConfig, ModelsConfig
from consolidate_markdown.processors.result import ProcessingResult


@pytest.fixture
def global_config():
    """Create a basic global config for testing."""
    return GlobalConfig(
        cm_dir=Path("/tmp"),
        log_level="INFO",
        force_generation=False,
        no_image=False,
        api_provider="openai",
        openai_key="test-key",
        openai_base_url="https://api.openai.com/v1",
        models=ModelsConfig(
            default_model="gpt-4-vision-preview",
            alternate_models={
                "gpt4": "gpt-4-vision-preview",
                "gpt3": "gpt-3.5-turbo",
            },
        ),
    )


@pytest.fixture
def openai_config(global_config):
    """Create an OpenAI config for testing."""
    config = global_config
    config.api_provider = "openai"
    config.openai_key = "test-openai-key"
    return config


@pytest.fixture
def openrouter_config(global_config):
    """Create an OpenRouter config for testing."""
    config = global_config
    config.api_provider = "openrouter"
    config.openrouter_key = "test-openrouter-key"
    config.openrouter_base_url = "https://openrouter.ai/api/v1"
    return config


@pytest.fixture
def mock_image_path(tmp_path):
    """Create a mock image file."""
    image_path = tmp_path / "test.jpg"
    image_path.write_bytes(b"fake image data")
    return image_path


@pytest.fixture
def mock_svg_path(tmp_path):
    """Create a mock SVG file."""
    svg_path = tmp_path / "test.svg"
    svg_content = """<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
        <rect width="100" height="100" fill="blue" />
    </svg>"""
    svg_path.write_text(svg_content)
    return svg_path


@pytest.fixture
def mock_heic_path(tmp_path):
    """Create a mock HEIC file."""
    heic_path = tmp_path / "test.heic"
    heic_path.write_bytes(b"fake heic data")
    return heic_path


@pytest.fixture
def cache_manager(tmp_path):
    """Create a cache manager for testing."""
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()
    return CacheManager(cm_dir)


class TestGPTProcessor:
    """Tests for the GPTProcessor class."""

    def test_initialization_openai(self, openai_config):
        """Test initialization with OpenAI provider."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI") as mock_openai:
            processor = GPTProcessor(openai_config)

            # Check that the client was initialized with the correct parameters
            mock_openai.assert_called_once_with(
                api_key="test-openai-key",
                base_url="https://api.openai.com/v1",
            )

            # Check that the provider and model were set correctly
            assert processor.provider == "openai"
            assert processor.current_model == "gpt-4-vision-preview"

    def test_initialization_openrouter(self, openrouter_config):
        """Test initialization with OpenRouter provider."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI") as mock_openai:
            processor = GPTProcessor(openrouter_config)

            # Check that the client was initialized with the correct parameters
            mock_openai.assert_called_once_with(
                api_key="test-openrouter-key",
                base_url="https://openrouter.ai/api/v1",
            )

            # Check that the provider and model were set correctly
            assert processor.provider == "openrouter"
            assert processor.current_model == "gpt-4-vision-preview"

    def test_initialization_invalid_provider(self, global_config):
        """Test initialization with an invalid provider."""
        global_config.api_provider = "invalid"

        with pytest.raises(GPTError, match="Unsupported API provider: invalid"):
            GPTProcessor(global_config)

    def test_initialization_missing_openai_key(self, openai_config):
        """Test initialization with missing OpenAI API key."""
        openai_config.openai_key = None

        with pytest.raises(GPTError, match="OpenAI API key is required"):
            GPTProcessor(openai_config)

    def test_initialization_missing_openrouter_key(self, openrouter_config):
        """Test initialization with missing OpenRouter API key."""
        openrouter_config.openrouter_key = None

        with pytest.raises(GPTError, match="OpenRouter API key is required"):
            GPTProcessor(openrouter_config)

    def test_set_model_default(self, openai_config):
        """Test setting the model to the default."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            processor = GPTProcessor(openai_config)

            # Set a different model first
            processor.current_model = "different-model"

            # Set to default (None)
            processor.set_model(None)

            # Check that the model was reset to default
            assert processor.current_model == "gpt-4-vision-preview"

    def test_set_model_by_name(self, openai_config):
        """Test setting the model by direct name."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            processor = GPTProcessor(openai_config)

            # Set by direct model name
            processor.set_model("gpt-4-vision-preview")

            # Check that the model was set correctly
            assert processor.current_model == "gpt-4-vision-preview"

    def test_set_model_by_alias(self, openai_config):
        """Test setting the model by alias."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            processor = GPTProcessor(openai_config)

            # Set by alias
            processor.set_model("gpt4")

            # Check that the model was set correctly
            assert processor.current_model == "gpt-4-vision-preview"

    def test_set_model_invalid_alias(self, openai_config):
        """Test setting the model with an invalid alias."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            processor = GPTProcessor(openai_config)

            # Try to set with invalid alias
            with pytest.raises(GPTError, match="Invalid model alias: invalid"):
                processor.set_model("invalid")

    def test_set_model_unsupported_by_provider(self, openai_config):
        """Test setting a model that's not supported by the provider."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            processor = GPTProcessor(openai_config)

            # Add an alias that maps to an unsupported model
            processor.config.models.alternate_models[
                "unsupported"
            ] = "unsupported-model"

            # Try to set with alias that maps to unsupported model
            with pytest.raises(GPTError, match="is not supported by provider"):
                processor.set_model("unsupported")

    @patch("consolidate_markdown.attachments.gpt.OpenAI")
    def test_analyze_image_openai(self, mock_openai, openai_config, mock_image_path):
        """Test analyzing an image with OpenAI."""
        # Set up mock response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is an image analysis"
        mock_client.chat.completions.create.return_value = mock_response

        # Create processor and analyze image
        processor = GPTProcessor(openai_config)
        result = processor.analyze_image(mock_image_path)

        # Check that the API was called with the correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-4-vision-preview"
        assert len(call_args["messages"]) == 1
        assert call_args["messages"][0]["role"] == "user"
        assert len(call_args["messages"][0]["content"]) == 2
        assert call_args["messages"][0]["content"][0]["type"] == "text"
        assert call_args["messages"][0]["content"][1]["type"] == "image_url"

        # Check the result
        assert result == "This is an image analysis"

    @patch("consolidate_markdown.attachments.gpt.OpenAI")
    def test_analyze_image_openrouter(
        self, mock_openai, openrouter_config, mock_image_path
    ):
        """Test analyzing an image with OpenRouter."""
        # Set up mock response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is an image analysis"
        mock_client.chat.completions.create.return_value = mock_response

        # Create processor and analyze image
        processor = GPTProcessor(openrouter_config)
        result = processor.analyze_image(mock_image_path)

        # Check that the API was called with the correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-4-vision-preview"
        assert len(call_args["messages"]) == 1
        assert call_args["messages"][0]["role"] == "user"
        assert len(call_args["messages"][0]["content"]) == 2
        assert call_args["messages"][0]["content"][0]["type"] == "text"
        assert call_args["messages"][0]["content"][1]["type"] == "image_url"

        # Check the result
        assert result == "This is an image analysis"

    @patch("consolidate_markdown.attachments.gpt.OpenAI")
    def test_analyze_image_with_custom_prompt(
        self, mock_openai, openai_config, mock_image_path
    ):
        """Test analyzing an image with a custom prompt."""
        # Set up mock response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is an image analysis"
        mock_client.chat.completions.create.return_value = mock_response

        # Create processor and analyze image with custom prompt
        processor = GPTProcessor(openai_config)
        result = processor.analyze_image(
            mock_image_path, prompt="Describe the colors in this image"
        )

        # Check that the API was called with the custom prompt
        call_args = mock_client.chat.completions.create.call_args[1]
        assert (
            call_args["messages"][0]["content"][0]["text"]
            == "Describe the colors in this image"
        )

        # Check the result
        assert result == "This is an image analysis"

    @patch("consolidate_markdown.attachments.gpt.OpenAI")
    def test_analyze_image_with_model_alias(
        self, mock_openai, openai_config, mock_image_path
    ):
        """Test analyzing an image with a specific model alias."""
        # Set up mock response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is an image analysis"
        mock_client.chat.completions.create.return_value = mock_response

        # Create processor and analyze image with model alias
        processor = GPTProcessor(openai_config)
        result = processor.analyze_image(mock_image_path, model_alias="gpt4")

        # Check that the model was set correctly
        assert processor.current_model == "gpt-4-vision-preview"

        # Check the result
        assert result == "This is an image analysis"

    @patch("consolidate_markdown.attachments.gpt.OpenAI")
    def test_analyze_image_with_cache(
        self, mock_openai, openai_config, mock_image_path, cache_manager
    ):
        """Test analyzing an image with caching."""
        # Set up mock response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is an image analysis"
        mock_client.chat.completions.create.return_value = mock_response

        # Create processor with cache manager
        processor = GPTProcessor(openai_config, cache_manager)

        # First call should hit the API
        result1 = processor.analyze_image(mock_image_path)
        assert result1 == "This is an image analysis"
        assert mock_client.chat.completions.create.call_count == 1

        # Second call should use the cache
        result2 = processor.analyze_image(mock_image_path)
        assert result2 == "This is an image analysis"
        assert (
            mock_client.chat.completions.create.call_count == 1
        )  # Still 1, no new API call

    @patch("consolidate_markdown.attachments.gpt.OpenAI")
    def test_analyze_image_api_error(self, mock_openai, openai_config, mock_image_path):
        """Test handling API errors during image analysis."""
        # Set up mock to raise an exception
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        # Create processor and try to analyze image
        processor = GPTProcessor(openai_config)

        with pytest.raises(
            GPTError,
            match="Error analyzing image with gpt-4-vision-preview: OpenAI API error: API error",
        ):
            processor.analyze_image(mock_image_path)

    @patch("consolidate_markdown.attachments.gpt.OpenAI")
    def test_analyze_image_empty_response(
        self, mock_openai, openai_config, mock_image_path
    ):
        """Test handling empty API responses."""
        # Set up mock with empty response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response

        # Create processor and try to analyze image
        processor = GPTProcessor(openai_config)

        with pytest.raises(
            GPTError,
            match="Error analyzing image with gpt-4-vision-preview: OpenAI API error: OpenAI API returned no content",
        ):
            processor.analyze_image(mock_image_path)

    @patch("consolidate_markdown.attachments.gpt.OpenAI")
    def test_describe_image_success(self, mock_openai, openai_config, mock_image_path):
        """Test describing an image successfully."""
        # Set up mock response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is an image description"
        mock_client.chat.completions.create.return_value = mock_response

        # Create processor and result tracker
        processor = GPTProcessor(openai_config)
        result = ProcessingResult()

        # Describe image
        description = processor.describe_image(
            mock_image_path, result, "test_processor"
        )

        # Check the description
        assert description == "This is an image description"

        # Check that the result was updated correctly
        assert result.gpt_new_analyses == 1
        assert result.gpt_cache_hits == 0
        assert result.gpt_skipped == 0

    @patch("consolidate_markdown.attachments.gpt.OpenAI")
    def test_describe_image_from_cache(
        self, mock_openai, openai_config, mock_image_path, cache_manager
    ):
        """Test describing an image with a cache hit."""
        # Set up mock response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is an image description"
        mock_client.chat.completions.create.return_value = mock_response

        # Create processor with cache manager
        processor = GPTProcessor(openai_config, cache_manager)
        result = ProcessingResult()

        # First call should hit the API and cache the result
        description1 = processor.describe_image(
            mock_image_path, result, "test_processor"
        )
        assert description1 == "This is an image description"
        assert result.gpt_new_analyses == 1
        assert result.gpt_cache_hits == 0

        # Reset the result tracker
        result = ProcessingResult()

        # Second call should use the cache
        description2 = processor.describe_image(
            mock_image_path, result, "test_processor"
        )
        assert description2 == "This is an image description"
        assert result.gpt_new_analyses == 0
        assert result.gpt_cache_hits == 1
        assert mock_client.chat.completions.create.call_count == 1  # Only one API call

    @patch("consolidate_markdown.attachments.gpt.OpenAI")
    def test_describe_image_api_error(
        self, mock_openai, openai_config, mock_image_path
    ):
        """Test handling API errors during image description."""
        # Set up mock to raise an exception
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        # Create processor and result tracker
        processor = GPTProcessor(openai_config)
        result = ProcessingResult()

        # Describe image should handle the error
        description = processor.describe_image(
            mock_image_path, result, "test_processor"
        )

        # Check that an error message was returned
        assert description == "[Error analyzing image]"

        # Check that the result was updated correctly
        assert result.gpt_skipped == 1
        assert result.gpt_new_analyses == 0
        assert result.gpt_cache_hits == 0

    @patch("consolidate_markdown.attachments.gpt.OpenAI")
    def test_describe_image_unsupported_format(
        self, mock_openai, openai_config, tmp_path
    ):
        """Test describing an image with an unsupported format."""
        # Create an unsupported file
        unsupported_path = tmp_path / "test.xyz"
        unsupported_path.write_bytes(b"unsupported format")

        # Create processor and result tracker
        processor = GPTProcessor(openai_config)
        result = ProcessingResult()

        # Mock the _convert_to_supported_format method to return None
        with patch.object(
            processor, "_convert_to_supported_format", return_value=(None, False)
        ):
            # Describe image should handle the unsupported format
            description = processor.describe_image(
                unsupported_path, result, "test_processor"
            )

            # Check that an error message was returned
            assert description == "[Error: Unsupported image format]"

            # Check that the result was updated correctly
            assert result.gpt_skipped == 1
            assert result.gpt_new_analyses == 0
            assert result.gpt_cache_hits == 0

    def test_get_placeholder(self, openai_config, mock_image_path):
        """Test getting a placeholder for an image."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            # Create processor and result tracker
            processor = GPTProcessor(openai_config)
            result = ProcessingResult()

            # Get placeholder
            placeholder = processor.get_placeholder(
                mock_image_path, result, "test_processor"
            )

            # Check the placeholder
            assert (
                placeholder
                == f"[GPT image analysis skipped for {mock_image_path.name}]"
            )

            # Check that the result was updated correctly
            assert result.gpt_skipped == 1
            assert result.gpt_new_analyses == 0
            assert result.gpt_cache_hits == 0

    @patch("consolidate_markdown.attachments.gpt.subprocess.run")
    def test_convert_to_supported_format_jpg(
        self, mock_run, openai_config, mock_image_path
    ):
        """Test converting a supported format (no conversion needed)."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            processor = GPTProcessor(openai_config)

            # Convert a JPG (already supported)
            path, needs_cleanup = processor._convert_to_supported_format(
                mock_image_path
            )

            # Check that no conversion was needed
            assert path == mock_image_path
            assert needs_cleanup is False
            mock_run.assert_not_called()

    @patch("consolidate_markdown.attachments.gpt.subprocess.run")
    def test_convert_to_supported_format_svg_with_png(
        self, mock_run, openai_config, mock_svg_path, tmp_path
    ):
        """Test converting an SVG with an existing PNG."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            processor = GPTProcessor(openai_config)

            # Create a PNG version of the SVG
            png_path = mock_svg_path.with_suffix(".png")
            png_path.write_bytes(b"fake png data")

            # Convert the SVG
            path, needs_cleanup = processor._convert_to_supported_format(mock_svg_path)

            # Check that the existing PNG was used
            assert path == png_path
            assert needs_cleanup is False
            mock_run.assert_not_called()

    @patch("consolidate_markdown.attachments.gpt.subprocess.run")
    def test_convert_to_supported_format_svg_conversion(
        self, mock_run, openai_config, mock_svg_path
    ):
        """Test converting an SVG using rsvg-convert."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            processor = GPTProcessor(openai_config)

            # Set up mock subprocess.run
            mock_run.return_value = MagicMock(returncode=0)

            # Convert the SVG
            path, needs_cleanup = processor._convert_to_supported_format(mock_svg_path)

            # Check that rsvg-convert was called
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0][0] == "rsvg-convert"

            # Check the result
            assert path == mock_svg_path.with_suffix(".png")
            assert needs_cleanup is True

    @patch("consolidate_markdown.attachments.gpt.subprocess.run")
    def test_convert_to_supported_format_svg_conversion_error(
        self, mock_run, openai_config, mock_svg_path
    ):
        """Test handling errors during SVG conversion."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            processor = GPTProcessor(openai_config)

            # Set up mock subprocess.run to raise an exception
            mock_run.side_effect = Exception("Conversion error")

            # Try to convert the SVG
            path, needs_cleanup = processor._convert_to_supported_format(mock_svg_path)

            # Check that the conversion failed
            assert path is None
            assert needs_cleanup is False

    @patch("consolidate_markdown.attachments.gpt.subprocess.run")
    def test_convert_to_supported_format_heic(
        self, mock_run, openai_config, mock_heic_path
    ):
        """Test converting a HEIC file."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            processor = GPTProcessor(openai_config)

            # Set up mock subprocess.run
            mock_run.return_value = MagicMock(returncode=0)

            # Convert the HEIC
            path, needs_cleanup = processor._convert_to_supported_format(mock_heic_path)

            # Check that sips was called
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0][0] == "sips"

            # Check the result
            assert path == mock_heic_path.with_suffix(".jpg")
            assert needs_cleanup is True

    @patch("consolidate_markdown.attachments.gpt.subprocess.run")
    def test_convert_to_supported_format_heic_error(
        self, mock_run, openai_config, mock_heic_path
    ):
        """Test handling errors during HEIC conversion."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            processor = GPTProcessor(openai_config)

            # Set up mock subprocess.run to raise an exception
            mock_run.side_effect = Exception("Conversion error")

            # Try to convert the HEIC
            path, needs_cleanup = processor._convert_to_supported_format(mock_heic_path)

            # Check that the conversion failed
            assert path is None
            assert needs_cleanup is False

    @patch("consolidate_markdown.attachments.gpt.subprocess.run")
    def test_convert_to_supported_format_unsupported(
        self, mock_run, openai_config, tmp_path
    ):
        """Test converting an unsupported format."""
        with patch("consolidate_markdown.attachments.gpt.OpenAI"):
            processor = GPTProcessor(openai_config)

            # Create an unsupported file
            unsupported_path = tmp_path / "test.xyz"
            unsupported_path.write_bytes(b"unsupported format")

            # Try to convert the unsupported file
            path, needs_cleanup = processor._convert_to_supported_format(
                unsupported_path
            )

            # Check that the conversion failed
            assert path is None
            assert needs_cleanup is False
            mock_run.assert_not_called()
