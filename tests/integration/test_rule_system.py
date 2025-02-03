"""Integration tests for the rules system."""

import subprocess
from pathlib import Path


def test_rule_validation_pipeline():
    """Test the complete rule validation pipeline."""
    # Run pre-commit hooks
    result = subprocess.run(
        ["pre-commit", "run", "--all-files"], capture_output=True, text=True
    )

    # Check if only black and isort modified files
    if result.returncode != 0:
        # Extract the failing hooks from the output
        failing_hooks = []
        for line in result.stdout.split("\n"):
            if line.strip().endswith("Failed"):
                # Extract hook name from lines like "black...Failed"
                hook = line.strip().split("...")[0].strip()
                failing_hooks.append(hook)
        # Only black and isort failures are acceptable
        assert set(failing_hooks) <= {"black", "isort"}, (
            "Pre-commit hooks failed with unexpected errors. "
            f"Failing hooks: {failing_hooks}"
        )


def test_rule_cross_references():
    """Test cross-references between rules."""
    rule_files = list(Path(".cursor/rules").glob("*.md"))

    # Build reference map
    references = {}
    for rule_file in rule_files:
        content = rule_file.read_text()
        references[rule_file.name] = []

        # Find markdown links
        import re

        links = re.findall(r"\[([^\]]+)\]\(([^\)]+)\)", content)
        for text, link in links:
            if link.endswith(".md"):
                references[rule_file.name].append(link)

    # Verify all references exist
    for rule, refs in references.items():
        for ref in refs:
            ref_path = Path(".cursor/rules") / Path(ref).name
            assert ref_path.exists(), f"Missing reference {ref} in {rule}"


def test_rule_summaries():
    """Test generation and validation of rule summaries."""
    rule_files = [
        f
        for f in Path(".cursor/rules").glob("*.md")
        if not f.name.endswith(".summary.md")
    ]

    for rule_file in rule_files:
        # Generate summary
        result = subprocess.run(
            ["pre-commit", "run", "rule-summary", "--files", str(rule_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Summary generation failed for {rule_file}"


def test_startup_sequence():
    """Test the rule system startup sequence."""
    # Test bootup rule
    bootup_file = Path(".cursor/rules/00-bootup.md")
    assert bootup_file.exists(), "Missing bootup rule"

    # Verify bootup content
    content = bootup_file.read_text()
    required_sections = [
        "Rule Discovery",
        "Mode Enforcement",
        "Loading Sequence",
        "Context Validation",
        "User Confirmation",
    ]

    for section in required_sections:
        assert section in content, f"Missing {section} in bootup rule"


def test_mode_transitions():
    """Test mode transition validation."""
    # Test operation modes rule
    modes_file = Path(".cursor/rules/50-operation-modes.md")
    assert modes_file.exists(), "Missing operation modes rule"

    content = modes_file.read_text()
    required_modes = ["PLAN", "ACT"]

    for mode in required_modes:
        assert mode in content, f"Missing {mode} mode definition"
        assert (
            f"{mode} Mode Constraints" in content
        ), f"Missing constraints for {mode} mode"
