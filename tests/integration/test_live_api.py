"""Integration tests for live API calls."""

import time
from pathlib import Path

import pytest
import tomli

from consolidate_markdown.attachments.gpt import GPTProcessor
from consolidate_markdown.config import GlobalConfig, ModelsConfig
from consolidate_markdown.processors.result import ProcessingResult


def load_root_config() -> dict:
    """Load the root config file."""
    config_path = Path("config.toml")
    if not config_path.exists():
        pytest.skip("Root config.toml not found")

    with open(config_path, "rb") as f:
        return tomli.load(f)


@pytest.fixture
def openrouter_live_config() -> GlobalConfig:
    """Create test configuration for OpenRouter."""
    root_config = load_root_config()

    config = GlobalConfig(
        cm_dir=Path(".cm"),
        log_level="INFO",
        force_generation=False,
        no_image=False,
        openai_key=None,
        api_provider="openrouter",
        openrouter_key=root_config["global"]["openrouter_key"],
        openrouter_base_url=root_config["global"]["openrouter_base_url"],
        models=ModelsConfig(
            default_model="gpt-4o",
            alternate_models={
                "gpt4": "gpt-4o",
                "gemini": "google/gemini-pro-vision-1.0",
                "yi": "yi/yi-vision-01",
                "blip": "deepinfra/blip",
                "llama": "meta/llama-3.2-90b-vision-instruct",
            },
        ),
    )
    return config


@pytest.fixture
def openai_live_config() -> GlobalConfig:
    """Create test configuration for OpenAI."""
    root_config = load_root_config()

    config = GlobalConfig(
        cm_dir=Path(".cm"),
        log_level="INFO",
        force_generation=False,
        no_image=False,
        openai_key=root_config["global"]["openai_key"],
        openai_base_url=root_config["global"]["openai_base_url"],
        api_provider="openai",
        openrouter_key=None,
        models=ModelsConfig(
            default_model="gpt-4-vision-preview",
            alternate_models={
                "gpt4": "gpt-4-vision-preview",
            },
        ),
    )
    return config


@pytest.mark.live_api
def test_openai_live_api(openai_live_config, test_image):
    """Test actual OpenAI API call with GPT-4 Vision.

    This test requires:
    1. --run-live-api flag
    2. OPENAI_API_KEY environment variable
    """
    processor = GPTProcessor(openai_live_config)
    result = ProcessingResult()

    # Attempt to analyze the test image
    description = processor.describe_image(test_image, result, "test")

    # Verify we got a meaningful response
    assert len(description) > 50, "Description should be detailed"
    assert "blue" in description.lower(), "Should mention the blue rectangle"
    assert "red" in description.lower(), "Should mention the red circle"
    assert result.gpt_new_analyses == 1, "Should count as new analysis"
    assert result.gpt_cache_hits == 0, "Should not be cached"
    assert result.gpt_skipped == 0, "Should not be skipped"


@pytest.mark.live_api
def test_openrouter_live_api(openrouter_live_config, test_image):
    """Test actual OpenRouter API call.

    This test requires:
    1. --run-live-api flag
    2. OPENROUTER_API_KEY environment variable
    """
    processor = GPTProcessor(openrouter_live_config)
    result = ProcessingResult()

    # Attempt to analyze the test image
    description = processor.describe_image(test_image, result, "test")

    # Verify we got a meaningful response
    assert len(description) >= 50, "Description should be at least 50 characters"
    assert result.gpt_new_analyses == 1, "Should count as new analysis"
    assert result.gpt_cache_hits == 0, "Should not be cached"
    assert result.gpt_skipped == 0, "Should not be skipped"


@pytest.mark.live_api
def test_caching_with_live_api(openai_live_config, test_image, tmp_path):
    """Test caching behavior with live API calls.

    This test requires:
    1. --run-live-api flag
    2. OPENAI_API_KEY environment variable
    """
    from consolidate_markdown.cache import CacheManager

    # Set up cache manager
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()
    cache_manager = CacheManager(cm_dir)

    # Create processor with cache
    processor = GPTProcessor(openai_live_config, cache_manager)

    # First call - should hit API
    result1 = ProcessingResult()
    description1 = processor.describe_image(test_image, result1, "test")
    assert result1.gpt_new_analyses == 1, "First call should be new"
    assert result1.gpt_cache_hits == 0, "First call should not hit cache"

    # Second call - should use cache
    result2 = ProcessingResult()
    description2 = processor.describe_image(test_image, result2, "test")
    assert description2 == description1, "Cached result should match"
    assert result2.gpt_new_analyses == 0, "Second call should not be new"
    assert result2.gpt_cache_hits == 1, "Second call should hit cache"


@pytest.mark.live_api
def test_gemini_code_analysis(openrouter_live_config, code_screenshot):
    """Test Gemini Pro Vision with code screenshot."""
    processor = GPTProcessor(openrouter_live_config)
    processor.set_model("gemini")
    result = ProcessingResult()

    # Analyze code screenshot
    description = processor.describe_image(code_screenshot, result, "test")

    # Verify code understanding
    assert len(description) > 100, "Description should be detailed"
    assert "python" in description.lower(), "Should identify Python code"
    assert "test" in description.lower(), "Should identify test context"
    assert "openrouter" in description.lower(), "Should identify OpenRouter"
    assert result.gpt_new_analyses == 1, "Should count as new analysis"


@pytest.mark.live_api
def test_yi_text_analysis(openrouter_live_config, text_editor_screenshot):
    """Test Yi Vision with text editor screenshot.

    This test requires:
    1. --run-live-api flag
    2. OPENROUTER_API_KEY environment variable
    """
    processor = GPTProcessor(openrouter_live_config)
    processor.set_model("yi")
    result = ProcessingResult()

    # Analyze text editor screenshot
    description = processor.describe_image(text_editor_screenshot, result, "test")

    # Verify text recognition
    assert len(description) > 100, "Description should be detailed"
    assert "model comparison" in description.lower(), "Should identify document title"
    assert "guide" in description.lower(), "Should identify document type"
    assert "openrouter" in description.lower(), "Should identify technical content"
    assert result.gpt_new_analyses == 1, "Should count as new analysis"


@pytest.mark.live_api
def test_blip_ui_analysis(openrouter_live_config, ui_screenshot):
    """Test DeepInfra BLIP with UI screenshot."""
    processor = GPTProcessor(openrouter_live_config)
    processor.set_model("blip")
    result = ProcessingResult()

    # Analyze UI screenshot
    description = processor.describe_image(ui_screenshot, result, "test")

    # Verify UI element recognition
    assert len(description) > 50, "Description should be detailed"
    assert "window" in description.lower(), "Should identify window"
    assert "terminal" in description.lower(), "Should identify terminal"
    assert "code editor" in description.lower(), "Should identify code editor"
    assert result.gpt_new_analyses == 1, "Should count as new analysis"


@pytest.mark.live_api
def test_llama_mixed_content(
    openrouter_live_config, code_screenshot, ui_screenshot, text_editor_screenshot
):
    """Test Llama Vision with mixed content."""
    processor = GPTProcessor(openrouter_live_config)
    processor.set_model("llama")
    result = ProcessingResult()

    # Test with each type of content
    images = [
        (code_screenshot, "code"),
        (ui_screenshot, "ui"),
        (text_editor_screenshot, "text"),
    ]

    for image, content_type in images:
        description = processor.describe_image(image, result, "test")
        assert (
            len(description) > 50
        ), f"Description for {content_type} should be detailed"
        result.gpt_new_analyses += (
            1  # Increment counter manually since we're using the same result object
        )


@pytest.mark.live_api
def test_model_switching(openrouter_live_config, code_screenshot, ui_screenshot):
    """Test switching between models and compare their responses.

    This test requires:
    1. --run-live-api flag
    2. OPENROUTER_API_KEY environment variable
    """
    processor = GPTProcessor(openrouter_live_config)
    result = ProcessingResult()

    # Test with all models on both images
    models = ["gpt4", "gemini", "yi", "blip"]
    images = {"code": code_screenshot, "ui": ui_screenshot}

    all_descriptions = {}

    for image_type, image_path in images.items():
        print(f"\n=== Testing {image_type.upper()} Screenshot ===")
        all_descriptions[image_type] = {}

        for model in models:
            print(f"\nModel: {model}")
            print("-" * 40)
            start_time = time.time()
            try:
                processor.set_model(model)
                description = processor.describe_image(
                    image_path, result, f"test_{image_type}"
                )
                all_descriptions[image_type][model] = description
                print(f"Response:\n{description}\n")
                print(f"Length: {len(description)} chars")
                assert (
                    len(description) > 50
                ), f"Description from {model} should be detailed"
            except Exception as e:
                print(f"Error with model {model}: {str(e)}")
                raise
            finally:
                elapsed = time.time() - start_time
                print(f"Time taken: {elapsed:.2f} seconds")

        # Verify different models give different responses for each image
        unique_descriptions = set(all_descriptions[image_type].values())
        assert (
            len(unique_descriptions) > 1
        ), f"Different models should give varied responses for {image_type}"

    return all_descriptions  # Return the descriptions for analysis


@pytest.mark.live_api
def test_multi_model_caching(openrouter_live_config, code_screenshot, tmp_path):
    """Test caching behavior with multiple models."""
    from consolidate_markdown.cache import CacheManager

    # Set up cache manager
    cm_dir = tmp_path / ".cm"
    cm_dir.mkdir()
    cache_manager = CacheManager(cm_dir)

    # Create processor with cache
    processor = GPTProcessor(openrouter_live_config, cache_manager)

    # Test models
    models = ["gpt4", "gemini", "yi"]

    # First round - should all hit API
    first_results = {}
    for model in models:
        processor.set_model(model)
        result = ProcessingResult()
        description = processor.describe_image(code_screenshot, result, f"test_{model}")
        first_results[model] = description
        assert len(description) > 50, f"Description from {model} should be detailed"
        result.gpt_new_analyses += (
            1  # Increment counter manually since we're using the same result object
        )

    # Second round - should use cache
    for model in models:
        processor.set_model(model)
        result = ProcessingResult()
        description = processor.describe_image(code_screenshot, result, f"test_{model}")
        assert (
            description == first_results[model]
        ), f"Cached result for {model} should match"
        assert (
            result.gpt_new_analyses == 0
        ), f"Second call with {model} should not be new"
        assert result.gpt_cache_hits == 1, f"Second call with {model} should hit cache"


@pytest.mark.live_api
def test_model_error_handling(openrouter_live_config):
    """Test error handling for invalid models."""
    processor = GPTProcessor(openrouter_live_config)

    # Test invalid model name
    with pytest.raises(Exception) as exc_info:
        processor.set_model("invalid-model")
    assert "Invalid model alias" in str(exc_info.value)

    # Test invalid model alias
    with pytest.raises(Exception) as exc_info:
        processor.set_model("nonexistent-alias")
    assert "Invalid model alias" in str(exc_info.value)

    # Test model not available for provider
    processor.provider = "openai"
    with pytest.raises(Exception) as exc_info:
        processor.set_model("google/gemini-pro-vision-1.0")
    assert "Invalid model alias" in str(exc_info.value)


@pytest.mark.live_api
def test_model_validation(openrouter_live_config):
    """Test model validation during configuration.

    This test requires:
    1. --run-live-api flag
    2. OPENROUTER_API_KEY environment variable
    """
    from consolidate_markdown.config import ModelsConfig

    # Test valid configuration
    valid_config = ModelsConfig(
        default_model="gpt-4o",
        alternate_models={
            "code": "google/gemini-pro-vision-1.0",
            "fast": "yi/yi-vision-01",
        },
    )
    is_valid, errors = valid_config.validate("openrouter")
    assert is_valid, "Valid configuration should pass validation"
    assert not errors, "Valid configuration should have no errors"

    # Test invalid default model
    invalid_default = ModelsConfig(default_model="invalid-model", alternate_models={})
    is_valid, errors = invalid_default.validate("openrouter")
    assert not is_valid, "Invalid default model should fail validation"
    assert any("default model" in err.lower() for err in errors)

    # Test invalid alternate model
    invalid_alternate = ModelsConfig(
        default_model="gpt-4o", alternate_models={"test": "invalid-model"}
    )
    is_valid, errors = invalid_alternate.validate("openrouter")
    assert not is_valid, "Invalid alternate model should fail validation"
    assert any("invalid model" in err.lower() for err in errors)

    # Test wrong provider
    openai_config = ModelsConfig(
        default_model="gpt-4o",
        alternate_models={"gemini": "google/gemini-pro-vision-1.0"},
    )
    is_valid, errors = openai_config.validate("openai")
    assert not is_valid, "OpenAI provider should not support Gemini"
    assert any("invalid model" in err.lower() for err in errors)
