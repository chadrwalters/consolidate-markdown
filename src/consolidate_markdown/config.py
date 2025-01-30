import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# Valid source types
VALID_SOURCE_TYPES = ["bear", "xbookmarks", "chatgptexport"]


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

        if not self.global_config.no_image and not self.global_config.openai_key:
            errors.append("OpenAI key required when image processing is enabled")

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
