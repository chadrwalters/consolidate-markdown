"""Rule validation module."""

import argparse
import os
from pathlib import Path
from typing import Optional

import yaml


def find_workspace_root() -> Path:
    """Find the workspace root directory.

    Returns:
        Path to workspace root
    """
    workspace_root = Path(os.getcwd())
    while (
        not (workspace_root / ".cursor").is_dir()
        and workspace_root != workspace_root.parent
    ):
        workspace_root = workspace_root.parent

    if not (workspace_root / ".cursor").is_dir():
        raise FileNotFoundError(
            "Could not find workspace root (no .cursor directory found)"
        )

    return workspace_root


def extract_frontmatter(content: str) -> Optional[dict]:
    """Extract frontmatter from markdown content.

    Args:
        content: The markdown content

    Returns:
        Frontmatter as dict if found, None otherwise
    """
    if not content.startswith("---"):
        return None

    end = content.find("---", 3)
    if end == -1:
        return None

    try:
        return yaml.safe_load(content[3:end])
    except yaml.YAMLError:
        return None


def validate_rule_structure(rule_file: Path) -> None:
    """Validate rule file structure.

    Args:
        rule_file: Path to the rule file
    """
    required_sections = [
        "Abstract/Purpose",
        "Table of Contents",
        "Mandatory Constraints",
        "Advisory Guidelines",
        "Exception Clauses",
        "Examples",
        "Dependencies",
        "Changelog",
    ]

    content = rule_file.read_text()
    for section in required_sections:
        if section not in content:
            raise ValueError(f"Missing {section} in {rule_file}")


def validate_frontmatter(rule_file: Path) -> None:
    """Validate rule frontmatter.

    Args:
        rule_file: Path to the rule file
    """
    content = rule_file.read_text()

    if "---" not in content:
        raise ValueError(f"Missing frontmatter in {rule_file}")

    frontmatter = extract_frontmatter(content)
    if not frontmatter:
        raise ValueError(f"Invalid frontmatter YAML in {rule_file}")

    required_fields = ["description", "version", "status"]
    for field in required_fields:
        if field not in frontmatter:
            raise ValueError(f"Missing {field} in frontmatter of {rule_file}")


def validate_glob_patterns(rule_file: Path) -> None:
    """Validate glob patterns in rule file.

    Args:
        rule_file: Path to the rule file
    """
    content = rule_file.read_text()
    frontmatter = extract_frontmatter(content)
    if not frontmatter or "globs" not in frontmatter:
        raise ValueError(f"Missing glob patterns in frontmatter of {rule_file}")


def validate_version_format(rule_file: Path) -> None:
    """Validate version number format.

    Args:
        rule_file: Path to the rule file
    """
    import re

    content = rule_file.read_text()
    frontmatter = extract_frontmatter(content)
    if not frontmatter or "version" not in frontmatter:
        raise ValueError(f"Missing version in frontmatter of {rule_file}")

    version = frontmatter["version"]
    if not re.match(r"^\d+\.\d+\.\d+$", str(version)):
        raise ValueError(f"Invalid version format in {rule_file} (must be x.y.z)")


def validate_dependencies(rule_file: Path) -> None:
    """Validate rule dependencies.

    Args:
        rule_file: Path to the rule file
    """
    content = rule_file.read_text()
    if "Dependencies:" in content:
        deps_section = content.split("Dependencies:")[1].split("\n\n")[0]
        if not deps_section.strip():
            raise ValueError(f"Empty dependencies section in {rule_file}")


def validate_rule(rule_file: Path) -> None:
    """Validate a single rule file.

    Args:
        rule_file: Path to the rule file
    """
    # Skip summary files
    if rule_file.name.endswith(".summary.md"):
        return

    validators = [
        validate_rule_structure,
        validate_frontmatter,
        validate_glob_patterns,
        validate_version_format,
        validate_dependencies,
    ]

    for validator in validators:
        validator(rule_file)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate rule files")
    parser.add_argument("files", nargs="+", help="Rule files to validate")
    args = parser.parse_args()

    workspace_root = find_workspace_root()

    for file_path in args.files:
        try:
            # Convert to absolute path if relative
            rule_file = Path(file_path)
            if not rule_file.is_absolute():
                rule_file = workspace_root / rule_file

            if not rule_file.exists():
                print(f"Error: File not found: {file_path}")
                continue

            validate_rule(rule_file)
            print(f"Validated {file_path}")

        except Exception as e:
            print(f"Error validating {file_path}: {str(e)}")
            raise


if __name__ == "__main__":
    main()
