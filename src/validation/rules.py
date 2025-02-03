"""Rule validation module."""

import argparse
from pathlib import Path

import yaml


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

    # Extract frontmatter
    frontmatter_text = content.split("---")[1]
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError:
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
    if "globs:" not in content:
        raise ValueError(f"Missing glob patterns in {rule_file}")


def validate_version_format(rule_file: Path) -> None:
    """Validate version number format.

    Args:
        rule_file: Path to the rule file
    """
    import re

    content = rule_file.read_text()
    version_pattern = r"version: \d+\.\d+\.\d+"
    if not re.search(version_pattern, content):
        raise ValueError(f"Invalid version format in {rule_file}")


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

    for file_path in args.files:
        try:
            rule_file = Path(file_path)
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
