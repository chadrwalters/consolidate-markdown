import os

import pytest
import tomli_w

from consolidate_markdown.config import load_config


def test_basic_config_loading(tmp_path):
    """Test basic config loading from TOML with minimal settings"""
    config_path = tmp_path / "config.toml"

    # Create required directories
    (tmp_path / ".cm").parent.mkdir(exist_ok=True)
    (tmp_path / "notes").mkdir(exist_ok=True)
    (tmp_path / "output").parent.mkdir(exist_ok=True)

    basic_config = {
        "global": {
            "cm_dir": str(tmp_path / ".cm"),
            "no_image": True,  # Disable image processing to avoid needing OpenAI key
            "api_provider": "openrouter",  # Use OpenRouter as provider
            "openrouter_key": "test-key",
        },
        "models": {
            "default_model": "gpt-4o",  # Use valid OpenRouter model
            "alternate_models": {
                "gpt4": "gpt-4o",
                "gemini": "google/gemini-pro-vision-1.0",
            },
        },
        "sources": [
            {
                "type": "bear",
                "srcDir": str(tmp_path / "notes"),
                "destDir": str(tmp_path / "output"),
            }
        ],
    }
    config_path.write_text(tomli_w.dumps(basic_config))

    config = load_config(config_path)
    assert config.global_config.cm_dir == tmp_path / ".cm"
    assert config.global_config.no_image is True
    assert len(config.sources) == 1
    assert config.sources[0].type == "bear"
    assert config.global_config.models.default_model == "gpt-4o"
    assert "gpt4" in config.global_config.models.alternate_models


def test_full_config_loading(tmp_path):
    """Test loading config with all options specified"""
    config_path = tmp_path / "config.toml"

    # Create required directories
    cm_dir = tmp_path / ".cm"
    notes_dir = tmp_path / "notes"
    output_dir = tmp_path / "output"
    cm_dir.mkdir(parents=True, exist_ok=True)
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set environment variables for testing
    os.environ["OPENROUTER_API_KEY"] = "test-key"
    os.environ["CM_API_PROVIDER"] = "openrouter"

    full_config = {
        "global": {
            "cm_dir": str(cm_dir),
            "log_level": "DEBUG",
            "force_generation": True,
            "no_image": True,
            "api_provider": "openrouter",
            "openrouter_key": "test-key",
        },
        "models": {
            "default_model": "gpt-4o",
            "alternate_models": {
                "gpt4": "gpt-4o",
                "gemini": "google/gemini-pro-vision-1.0",
                "yi": "yi/yi-vision-01",
            },
        },
        "sources": [
            {
                "type": "bear",
                "srcDir": str(notes_dir),
                "destDir": str(output_dir),
                "index_filename": "custom.md",
            }
        ],
    }
    config_path.write_text(tomli_w.dumps(full_config))

    try:
        config = load_config(config_path)
        assert config.global_config.cm_dir == cm_dir
        assert config.global_config.log_level == "DEBUG"
        assert config.global_config.force_generation is True
        assert config.global_config.no_image is True
        assert config.global_config.openrouter_key == "test-key"
        assert config.global_config.api_provider == "openrouter"
        assert config.global_config.models.default_model == "gpt-4o"
        assert config.global_config.models.alternate_models == {
            "gpt4": "gpt-4o",
            "gemini": "google/gemini-pro-vision-1.0",
            "yi": "yi/yi-vision-01",
        }
        assert len(config.sources) == 1
        assert config.sources[0].type == "bear"
        assert config.sources[0].src_dir == notes_dir
        assert config.sources[0].dest_dir == output_dir
        assert config.sources[0].index_filename == "custom.md"
    finally:
        # Clean up environment variables
        os.environ.pop("OPENROUTER_API_KEY", None)
        os.environ.pop("CM_API_PROVIDER", None)


def test_config_validation(tmp_path):
    """Test configuration validation"""
    config_path = tmp_path / "config.toml"

    # Create required directories
    notes_dir = tmp_path / "notes"
    output_dir = tmp_path / "output"
    cm_dir = tmp_path / ".cm"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    cm_dir.mkdir(parents=True, exist_ok=True)

    # Test invalid source type
    invalid_config = {
        "global": {
            "cm_dir": str(cm_dir),
            "no_image": True,
            "api_provider": "openrouter",
            "openrouter_key": "test-key",
        },
        "models": {
            "default_model": "gpt-4o",
            "alternate_models": {
                "gpt4": "gpt-4o",
                "gemini": "google/gemini-pro-vision-1.0",
            },
        },
        "sources": [
            {
                "type": "invalid",
                "srcDir": str(notes_dir),
                "destDir": str(output_dir),
            }
        ],
    }
    config_path.write_text(tomli_w.dumps(invalid_config))

    with pytest.raises(ValueError) as exc_info:
        load_config(config_path)
    assert "Invalid source type: invalid" in str(exc_info.value)

    # Test missing OpenRouter key when image processing is enabled
    invalid_config = {
        "global": {
            "cm_dir": str(cm_dir),
            "no_image": False,  # This requires openrouter_key
            "api_provider": "openrouter",
        },
        "models": {"default_model": "gpt-4o", "alternate_models": {"gpt4": "gpt-4o"}},
        "sources": [
            {
                "type": "bear",
                "srcDir": str(notes_dir),
                "destDir": str(output_dir),
            }
        ],
    }
    config_path.write_text(tomli_w.dumps(invalid_config))

    with pytest.raises(ValueError) as exc_info:
        config = load_config(config_path)
        config.validate()  # Explicitly call validate to check API key requirement
    assert (
        "OpenRouter API key required when using OpenRouter provider with image processing"
        in str(exc_info.value)
    )

    # Test invalid model for provider
    invalid_config = {
        "global": {
            "cm_dir": str(tmp_path / ".cm"),
            "no_image": True,
            "api_provider": "openrouter",
            "openrouter_key": "test-key",
        },
        "models": {
            "default_model": "invalid-model",  # Invalid model
            "alternate_models": {"gpt4": "gpt-4o"},
        },
        "sources": [
            {
                "type": "bear",
                "srcDir": str(tmp_path / "notes"),
                "destDir": str(tmp_path / "output"),
            }
        ],
    }
    config_path.write_text(tomli_w.dumps(invalid_config))

    with pytest.raises(ValueError) as exc_info:
        load_config(config_path)
    assert "Invalid default model for openrouter" in str(exc_info.value)


def test_env_var_overrides(tmp_path, monkeypatch):
    """Test environment variable overrides"""
    config_path = tmp_path / "config.toml"

    # Create required directories
    (tmp_path / ".cm").parent.mkdir(exist_ok=True)
    (tmp_path / "notes").mkdir(exist_ok=True)
    (tmp_path / "output").parent.mkdir(exist_ok=True)

    basic_config = {
        "global": {
            "cm_dir": str(tmp_path / ".cm"),
            "openrouter_key": "default_key",
            "no_image": True,  # Disable image processing to avoid validation issues
            "api_provider": "openrouter",  # Use OpenRouter as provider
        },
        "models": {
            "default_model": "gpt-4o",  # Use valid OpenRouter model
            "alternate_models": {"gpt4": "gpt-4o"},
        },
        "sources": [
            {
                "type": "bear",
                "srcDir": str(tmp_path / "notes"),
                "destDir": str(tmp_path / "output"),
            }
        ],
    }
    config_path.write_text(tomli_w.dumps(basic_config))

    # Set environment variables
    monkeypatch.setenv("OPENROUTER_API_KEY", "env_key")
    monkeypatch.setenv("CM_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CM_NO_IMAGE", "true")

    config = load_config(config_path)
    assert config.global_config.openrouter_key == "env_key"
    assert config.global_config.log_level == "DEBUG"
    assert config.global_config.no_image is True


def test_validate_invalid_source_type(tmp_path):
    """Test validation with invalid source type."""
    config_file = tmp_path / "test_config.toml"
    config_file.write_text(
        f"""
[global]
cm_dir = "{tmp_path / '.cm'}"
log_level = "INFO"
force_generation = false
no_image = true
api_provider = "openrouter"
openrouter_key = "test-key"

[models]
default_model = "gpt-4o"
alternate_models = {{ gpt4 = "gpt-4o" }}

[[sources]]
type = "invalid"
srcDir = "{tmp_path / 'invalid'}"
destDir = "{tmp_path / 'output/invalid'}"
"""
    )

    with pytest.raises(ValueError) as exc_info:
        load_config(config_file)

    assert "Invalid source type: invalid" in str(exc_info.value)
