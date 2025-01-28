import pytest
import tomli_w

from consolidate_markdown.config import Config, GlobalConfig, load_config


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
    assert isinstance(config, Config)
    assert isinstance(config.global_config, GlobalConfig)
    assert len(config.sources) == 1
    assert config.sources[0].type == "bear"
    assert config.sources[0].src_dir == tmp_path / "notes"
    assert config.sources[0].dest_dir == tmp_path / "output"


def test_full_config_loading(tmp_path):
    """Test loading config with all options specified"""
    config_path = tmp_path / "config.toml"

    # Create required directories
    (tmp_path / ".cm").parent.mkdir(exist_ok=True)
    (tmp_path / "notes").mkdir(exist_ok=True)
    (tmp_path / "output").parent.mkdir(exist_ok=True)

    full_config = {
        "global": {
            "cm_dir": str(tmp_path / ".cm"),
            "log_level": "DEBUG",
            "force_generation": True,
            "no_image": True,
            "openai_key": "test_key",
        },
        "sources": [
            {
                "type": "bear",
                "srcDir": str(tmp_path / "notes"),
                "destDir": str(tmp_path / "output"),
                "index_filename": "custom.md",
            }
        ],
    }
    config_path.write_text(tomli_w.dumps(full_config))

    config = load_config(config_path)
    assert config.global_config.log_level == "DEBUG"
    assert config.global_config.force_generation is True
    assert config.global_config.no_image is True
    assert config.global_config.openai_key == "test_key"
    assert config.sources[0].index_filename == "custom.md"


def test_config_validation(tmp_path):
    """Test configuration validation"""
    config_path = tmp_path / "config.toml"

    # Test invalid source type
    invalid_config = {
        "global": {"cm_dir": str(tmp_path / ".cm"), "no_image": True},
        "sources": [
            {
                "type": "invalid",  # Invalid source type
                "srcDir": str(tmp_path / "notes"),
                "destDir": str(tmp_path / "output"),
            }
        ],
    }
    config_path.write_text(tomli_w.dumps(invalid_config))

    with pytest.raises(ValueError) as exc_info:
        load_config(config_path)
    assert "Invalid source type: invalid" in str(exc_info.value)

    # Test missing OpenAI key when image processing is enabled
    invalid_config = {
        "global": {
            "cm_dir": str(tmp_path / ".cm"),
            "no_image": False,  # This requires openai_key
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
    assert "OpenAI key required when image processing is enabled" in str(exc_info.value)


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
            "openai_key": "default_key",
            "no_image": True,  # Disable image processing to avoid validation issues
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
    monkeypatch.setenv("OPENAI_API_KEY", "env_key")
    monkeypatch.setenv("CM_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CM_NO_IMAGE", "true")

    config = load_config(config_path)
    assert config.global_config.openai_key == "env_key"
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
openai_key = "test-key"

[[sources]]
type = "invalid"
srcDir = "{tmp_path / 'invalid'}"
destDir = "{tmp_path / 'output/invalid'}"
"""
    )

    with pytest.raises(ValueError) as exc_info:
        load_config(config_file)

    assert "Invalid source type: invalid" in str(exc_info.value)
