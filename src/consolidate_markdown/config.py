import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Valid source types
VALID_SOURCE_TYPES = ["bear", "xbookmarks", "chatgptexport", "claude"]

# Valid API providers
VALID_API_PROVIDERS = ["openai", "openrouter"]

# Default API URLs
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Default model
DEFAULT_MODEL = "google/gemini-pro-vision-1.0"

# Valid models per provider
VALID_MODELS = {
    "openai": ["gpt-4o"],
    "openrouter": [
        "gpt-4o",
        "google/gemini-pro-vision-1.0",
        "yi/yi-vision-01",
        "deepinfra/blip",
        "meta/llama-3.2-90b-vision-instruct",
    ],
}


@dataclass
class ModelsConfig:
    """Configuration for model settings."""

    def __init__(
        self,
        default_model: str = DEFAULT_MODEL,
        alternate_models: Optional[Dict[str, str]] = None,
    ):
        """Initialize model configuration."""
        self.default_model = default_model
        self.alternate_models = alternate_models or {}

    def validate(self, api_provider: str) -> Tuple[bool, List[str]]:
        """Validate model configuration."""
        errors = []
        valid_models = {
            "openrouter": [
                "gpt-4o",
                "google/gemini-pro-vision-1.0",
                "yi/yi-vision-01",
                "deepinfra/blip",
                "meta/llama-3.2-90b-vision-instruct",
            ],
            "openai": ["gpt-4-vision-preview"],
        }

        if api_provider not in valid_models:
            errors.append(
                f"Invalid API provider: {api_provider}. Must be one of: {', '.join(valid_models.keys())}"
            )
            return False, errors

        provider_models = valid_models[api_provider]

        # Validate default model
        if self.default_model not in provider_models:
            errors.append(
                f"Invalid default model for {api_provider}: {self.default_model}. Must be one of: {', '.join(provider_models)}"
            )

        # Validate alternate models
        for alias, model in self.alternate_models.items():
            if model not in provider_models:
                errors.append(
                    f"Invalid model for alias '{alias}': {model}. Must be one of: {', '.join(provider_models)}"
                )

        return len(errors) == 0, errors

    def get_model(self, alias: Optional[str] = None) -> str:
        """Get the model name for the given alias."""
        if not alias:
            return self.default_model
        return self.alternate_models.get(alias, self.default_model)


@dataclass
class SourceConfig:
    type: str
    src_dir: Path
    dest_dir: Path
    index_filename: str = "index.md"


@dataclass
class GlobalConfig:
    cm_dir: Path = Path(".cm")
    log_level: str = "INFO"
    force_generation: bool = False
    no_image: bool = False
    openai_key: Optional[str] = None
    api_provider: str = "openai"
    openrouter_key: Optional[str] = None
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL
    openrouter_base_url: str = DEFAULT_OPENROUTER_BASE_URL
    models: ModelsConfig = field(default_factory=ModelsConfig)

    def __init__(
        self,
        cm_dir: Path = Path(".cm"),
        log_level: str = "INFO",
        force_generation: bool = False,
        no_image: bool = False,
        openai_key: Optional[str] = None,
        api_provider: str = "openai",
        openrouter_key: Optional[str] = None,
        openai_base_url: str = DEFAULT_OPENAI_BASE_URL,
        openrouter_base_url: str = DEFAULT_OPENROUTER_BASE_URL,
        models: Optional[ModelsConfig] = None,
    ):
        """Initialize global configuration."""
        self.cm_dir = cm_dir
        self.log_level = log_level
        self.force_generation = force_generation
        self.no_image = no_image
        self.openai_key = openai_key
        self.api_provider = api_provider
        self.openrouter_key = openrouter_key
        self.openai_base_url = openai_base_url
        self.openrouter_base_url = openrouter_base_url
        self.models = models or ModelsConfig()


@dataclass
class Config:
    global_config: GlobalConfig
    sources: List[SourceConfig] = field(default_factory=list)

    def validate(self) -> tuple[bool, List[str]]:
        """Validate configuration settings."""
        errors = []

        # Validate global settings
        if not self.global_config.cm_dir.parent.exists():
            errors.append(
                f"Parent directory for cm_dir does not exist: {self.global_config.cm_dir}"
            )

        # Validate API provider
        if self.global_config.api_provider not in VALID_API_PROVIDERS:
            errors.append(
                f"Invalid API provider: {self.global_config.api_provider}. "
                f"Must be one of: {', '.join(VALID_API_PROVIDERS)}"
            )

        # Validate API keys when image processing is enabled
        if not self.global_config.no_image:
            if (
                self.global_config.api_provider == "openai"
                and not self.global_config.openai_key
            ):
                errors.append(
                    "OpenAI API key required when using OpenAI provider with image processing"
                )
            elif (
                self.global_config.api_provider == "openrouter"
                and not self.global_config.openrouter_key
            ):
                errors.append(
                    "OpenRouter API key required when using OpenRouter provider with image processing"
                )

        # Validate models configuration
        is_valid, model_errors = self.global_config.models.validate(
            self.global_config.api_provider
        )
        if not is_valid:
            errors.extend(model_errors)

        # Validate sources
        for source in self.sources:
            if not source.src_dir.exists():
                errors.append(f"Source directory does not exist: {source.src_dir}")
            if not source.dest_dir.parent.exists():
                errors.append(
                    f"Parent of destination directory does not exist: {source.dest_dir}"
                )
            if source.type not in VALID_SOURCE_TYPES:
                errors.append(f"Invalid source type: {source.type}")

        return len(errors) == 0, errors


def load_config(config_path: Path) -> Config:
    """Load and validate configuration from TOML file."""
    import tomli

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "rb") as f:
        data = tomli.load(f)

    # Load models configuration
    models_data = data.get("models", {})
    alternate_models = models_data.get("alternate_models", {})
    models_config = ModelsConfig(
        default_model=os.environ.get(
            "CM_DEFAULT_MODEL", models_data.get("default_model", DEFAULT_MODEL)
        ),
        alternate_models=alternate_models,
    )

    # Create GlobalConfig with environment variable overrides
    global_config = GlobalConfig(
        cm_dir=Path(data.get("global", {}).get("cm_dir", ".cm")),
        log_level=os.environ.get(
            "CM_LOG_LEVEL", data.get("global", {}).get("log_level", "INFO")
        ),
        force_generation=data.get("global", {}).get("force_generation", False),
        no_image=os.environ.get("CM_NO_IMAGE", "").lower() == "true"
        or data.get("global", {}).get("no_image", False),
        openai_key=os.environ.get(
            "OPENAI_API_KEY", data.get("global", {}).get("openai_key")
        ),
        api_provider=os.environ.get(
            "CM_API_PROVIDER", data.get("global", {}).get("api_provider", "openai")
        ),
        openrouter_key=os.environ.get(
            "OPENROUTER_API_KEY", data.get("global", {}).get("openrouter_key")
        ),
        openai_base_url=os.environ.get(
            "OPENAI_API_BASE_URL",
            data.get("global", {}).get("openai_base_url", DEFAULT_OPENAI_BASE_URL),
        ),
        openrouter_base_url=os.environ.get(
            "OPENROUTER_API_BASE_URL",
            data.get("global", {}).get(
                "openrouter_base_url", DEFAULT_OPENROUTER_BASE_URL
            ),
        ),
        models=models_config,
    )

    # Create SourceConfigs
    sources = []
    for source_data in data.get("sources", []):
        sources.append(
            SourceConfig(
                type=source_data["type"],
                src_dir=Path(source_data["srcDir"]),
                dest_dir=Path(source_data["destDir"]),
                index_filename=source_data.get("index_filename", "index.md"),
            )
        )

    config = Config(global_config=global_config, sources=sources)
    is_valid, errors = config.validate()
    if not is_valid:
        raise ValueError("Invalid configuration:\n" + "\n".join(errors))

    return config
