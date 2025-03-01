#!/usr/bin/env python
"""Run all issue tests to verify fixes."""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all issue tests."""
    # Get the directory of this script
    script_dir = Path(__file__).parent

    # List of test files to run
    test_files = [
        "unit/test_chatgpt_processor_issues.py",
        "unit/test_claude_processor_issues.py",
        "unit/test_xbookmarks_processor_issues.py",
        "unit/test_image_processor_issues.py",
    ]

    # Run each test file
    for test_file in test_files:
        test_path = script_dir / test_file
        if not test_path.exists():
            print(f"Test file not found: {test_path}")
            continue

        print(f"\n\n{'=' * 80}")
        print(f"Running tests in {test_file}")
        print(f"{'=' * 80}\n")

        # Run the test with pytest
        result = subprocess.run(
            ["pytest", "-xvs", str(test_path)],
            cwd=script_dir.parent,
            capture_output=False,
        )

        if result.returncode != 0:
            print(f"\nTests in {test_file} failed with return code {result.returncode}")
            return result.returncode

    print("\n\nAll tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(run_tests())
