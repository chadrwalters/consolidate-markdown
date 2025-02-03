"""Rule summary generation."""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

import yaml


def extract_frontmatter(content: str) -> Optional[Dict]:
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


def extract_sections(content: str) -> Dict[str, List[str]]:
    """Extract sections from markdown content.

    Args:
        content: The markdown content

    Returns:
        Dict mapping section names to lists of items
    """
    sections = {}
    current_section = None
    current_items: List[str] = []

    for line in content.split("\n"):
        if line.startswith("### "):
            if current_section and current_items:
                sections[current_section] = current_items
            current_section = line[4:].strip()
            current_items = []
        elif line.startswith("- ") and current_section:
            current_items.append(line[2:].strip())

    if current_section and current_items:
        sections[current_section] = current_items

    return sections


def generate_summary(rule_file: Path) -> Dict:
    """Generate a summary for a rule file.

    Args:
        rule_file: Path to the rule file

    Returns:
        Summary as dict
    """
    content = rule_file.read_text()
    frontmatter = extract_frontmatter(content)
    sections = extract_sections(content)

    if not frontmatter:
        raise ValueError(f"Missing or invalid frontmatter in {rule_file}")

    # Convert date objects to strings if present
    last_updated = frontmatter.get("last_updated", "")
    if last_updated and hasattr(last_updated, "strftime"):
        last_updated = last_updated.strftime("%Y-%m-%d")

    # Build summary
    summary = {
        "title": frontmatter.get("title", "Untitled Rule"),
        "description": frontmatter.get("description", ""),
        "version": frontmatter.get("version", "0.0.0"),
        "status": frontmatter.get("status", "Draft"),
        "last_updated": last_updated,
        "constraints": {
            "must": sections.get("MUST", []),
            "must_not": sections.get("MUST NOT", []),
            "should": sections.get("SHOULD", []),
            "recommended": sections.get("RECOMMENDED", []),
        },
        "globs": frontmatter.get("globs", []),
    }

    return summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate rule summaries")
    parser.add_argument("files", nargs="+", help="Rule files to process")
    args = parser.parse_args()

    # Create summaries directory if it doesn't exist
    summaries_dir = Path(".cursor/rules/summaries")
    summaries_dir.mkdir(parents=True, exist_ok=True)

    for file_path in args.files:
        try:
            rule_file = Path(file_path)
            if not rule_file.exists():
                print(f"Error: File not found: {file_path}")
                continue

            summary = generate_summary(rule_file)
            summary_file = summaries_dir / f"{rule_file.stem}.json"
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2)
            print(f"Generated summary for {file_path}")

        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            raise


if __name__ == "__main__":
    main()
