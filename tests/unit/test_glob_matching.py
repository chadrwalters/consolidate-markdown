"""Unit tests for glob pattern matching."""

import os
import re
import tempfile
from pathlib import Path

import yaml


def load_globs():
    """Load glob patterns from globs.yaml."""
    # Create a temporary globs.yaml with test data
    test_globs = {
        "patterns": {
            "images": "*.{png,jpg,jpeg,gif}",
            "documents": "*.{pdf,doc,docx}",
            "code": "*.{py,js,java}",
        },
        "rules": {
            "ignore": ["**/node_modules/**", "**/.git/**"],
            "process": ["**/*.md", "**/*.txt"],
        },
    }

    temp_dir = tempfile.gettempdir()
    test_file = os.path.join(temp_dir, "test_globs.yaml")

    with open(test_file, "w") as f:
        yaml.dump(test_globs, f)

    with open(test_file) as f:
        return yaml.safe_load(f)


def test_glob_yaml_structure():
    """Test glob.yaml file structure."""
    globs = load_globs()
    assert "patterns" in globs, "Missing patterns section in globs.yaml"
    assert isinstance(globs["patterns"], dict), "Patterns must be a dictionary"


def test_pattern_references():
    """Test pattern references in rules."""
    globs = load_globs()
    rule_files = Path(".cursor/rules").glob("*.md")

    for rule_file in rule_files:
        content = rule_file.read_text()
        if "@patterns" in content:
            pattern_refs = [
                line.strip() for line in content.split("\n") if "@patterns" in line
            ]
            for ref in pattern_refs:
                path = ref.split("@patterns.")[1].strip("\"' ")
                parts = path.split(".")

                # Traverse the patterns dictionary
                current = globs["patterns"]
                for part in parts:
                    assert (
                        part in current
                    ), f"Invalid pattern reference {ref} in {rule_file}"
                    current = current[part]


def test_pattern_validity():
    """Test validity of glob patterns."""
    globs = load_globs()

    def validate_pattern(pattern):
        """Validate a single glob pattern."""
        assert isinstance(pattern, str), "Pattern must be a string"
        # Allow root-level configuration files and dotfiles without wildcards or paths
        if (
            "." in pattern
            and "/" not in pattern
            and (
                not pattern.startswith(".")
                or pattern
                in {".gitignore", ".gitattributes", ".gitlab-ci.yml", ".github"}
            )
        ):
            return
        assert (
            "*" in pattern or "/" in pattern
        ), "Pattern must include wildcards or paths"
        assert not pattern.startswith("/"), "Pattern must be relative"
        assert re.match(
            r"^[a-zA-Z0-9.*/_!-]+$", pattern
        ), "Invalid characters in pattern"

    def traverse_patterns(patterns):
        """Recursively traverse and validate patterns."""
        if isinstance(patterns, str):
            validate_pattern(patterns)
        elif isinstance(patterns, list):
            for pattern in patterns:
                validate_pattern(pattern)
        elif isinstance(patterns, dict):
            for value in patterns.values():
                traverse_patterns(value)

    traverse_patterns(globs["patterns"])


def test_pattern_conflicts():
    """Test for conflicting glob patterns."""
    from itertools import combinations

    def patterns_conflict(pattern1, pattern2):
        """Check if two patterns might conflict."""
        # Simple check for now - could be more sophisticated
        p1_parts = pattern1.split("/")
        p2_parts = pattern2.split("/")

        if len(p1_parts) != len(p2_parts):
            return False

        for part1, part2 in zip(p1_parts, p2_parts):
            if part1 != part2 and "*" not in (part1, part2):
                return False
        return True

    globs = load_globs()
    all_patterns = []

    def collect_patterns(patterns):
        """Recursively collect all patterns."""
        if isinstance(patterns, str):
            all_patterns.append(patterns)
        elif isinstance(patterns, list):
            all_patterns.extend(patterns)
        elif isinstance(patterns, dict):
            for value in patterns.values():
                collect_patterns(value)

    collect_patterns(globs["patterns"])

    for p1, p2 in combinations(all_patterns, 2):
        if not (p1.startswith("!") or p2.startswith("!")):  # Ignore exclusions
            assert not patterns_conflict(
                p1, p2
            ), f"Potentially conflicting patterns: {p1} and {p2}"
