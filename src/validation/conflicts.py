"""Rule conflicts validation module."""

import argparse
import os
from itertools import combinations
from pathlib import Path
from typing import Dict, List

import yaml


def load_globs() -> Dict:
    """Load glob patterns from globs.yaml.

    Returns:
        Dict containing glob patterns
    """
    # Get the workspace root directory (where .cursor/rules is located)
    workspace_root = Path(os.getcwd())
    while (
        not (workspace_root / ".cursor").is_dir()
        and workspace_root != workspace_root.parent
    ):
        workspace_root = workspace_root.parent

    globs_file = workspace_root / ".cursor" / "rules" / "globs.yaml"
    if not globs_file.exists():
        raise FileNotFoundError(f"Could not find globs.yaml at {globs_file}")

    with open(globs_file) as f:
        return yaml.safe_load(f)


def patterns_conflict(pattern1: str, pattern2: str) -> bool:
    """Check if two patterns might conflict.

    Args:
        pattern1: First glob pattern
        pattern2: Second glob pattern

    Returns:
        True if patterns might conflict, False otherwise
    """
    p1_parts = pattern1.split("/")
    p2_parts = pattern2.split("/")

    if len(p1_parts) != len(p2_parts):
        return False

    for part1, part2 in zip(p1_parts, p2_parts):
        if part1 != part2 and "*" not in (part1, part2):
            return False
    return True


def collect_patterns(patterns) -> List[str]:
    """Recursively collect all patterns.

    Args:
        patterns: Pattern structure (str, list, or dict)

    Returns:
        List of all patterns
    """
    all_patterns = []

    if isinstance(patterns, str):
        all_patterns.append(patterns)
    elif isinstance(patterns, list):
        all_patterns.extend(patterns)
    elif isinstance(patterns, dict):
        for value in patterns.values():
            all_patterns.extend(collect_patterns(value))

    return all_patterns


def check_conflicts(globs: Dict) -> None:
    """Check for conflicting glob patterns.

    Args:
        globs: Dict containing glob patterns
    """
    all_patterns = collect_patterns(globs["patterns"])

    for p1, p2 in combinations(all_patterns, 2):
        if not (p1.startswith("!") or p2.startswith("!")):  # Ignore exclusions
            if patterns_conflict(p1, p2):
                raise ValueError(f"Potentially conflicting patterns: {p1} and {p2}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check for conflicting glob patterns")
    parser.add_argument("files", nargs="+", help="Rule files to check")
    # We don't use args.files since we check all patterns in globs.yaml
    _ = parser.parse_args()

    try:
        globs = load_globs()
        check_conflicts(globs)
        print("No conflicting patterns found")

    except Exception as e:
        print(f"Error checking conflicts: {str(e)}")
        raise


if __name__ == "__main__":
    main()
