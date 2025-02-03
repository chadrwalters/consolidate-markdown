"""Unit tests for rule validation system."""

from pathlib import Path


def test_rule_structure():
    """Test rule file structure validation."""
    # Test required sections
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

    rule_files = [
        f
        for f in Path(".cursor/rules").glob("*.md")
        if not f.name.endswith(".summary.md")
    ]
    for rule_file in rule_files:
        content = rule_file.read_text()
        for section in required_sections:
            assert section in content, f"Missing {section} in {rule_file}"


def test_frontmatter():
    """Test rule frontmatter validation."""
    rule_files = [
        f
        for f in Path(".cursor/rules").glob("*.md")
        if not f.name.endswith(".summary.md")
    ]
    for rule_file in rule_files:
        content = rule_file.read_text()
        assert "---" in content, f"Missing frontmatter in {rule_file}"
        assert "description:" in content, f"Missing description in {rule_file}"
        assert "version:" in content, f"Missing version in {rule_file}"
        assert "status:" in content, f"Missing status in {rule_file}"


def test_glob_patterns():
    """Test glob pattern validation."""
    rule_files = [
        f
        for f in Path(".cursor/rules").glob("*.md")
        if not f.name.endswith(".summary.md")
    ]
    for rule_file in rule_files:
        content = rule_file.read_text()
        assert "globs:" in content, f"Missing glob patterns in {rule_file}"


def test_version_format():
    """Test version number format."""
    import re

    version_pattern = r"\d+\.\d+\.\d+"
    rule_files = [
        f
        for f in Path(".cursor/rules").glob("*.md")
        if not f.name.endswith(".summary.md")
    ]
    for rule_file in rule_files:
        content = rule_file.read_text()
        assert re.search(
            f"version: {version_pattern}", content
        ), f"Invalid version format in {rule_file}"


def test_rule_dependencies():
    """Test rule dependency validation."""
    rule_files = Path(".cursor/rules").glob("*.md")
    for rule_file in rule_files:
        content = rule_file.read_text()
        if "Dependencies:" in content:
            deps_section = content.split("Dependencies:")[1].split("\n\n")[0]
            assert (
                len(deps_section.strip()) > 0
            ), f"Empty dependencies section in {rule_file}"
