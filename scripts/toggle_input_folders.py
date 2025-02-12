#!/usr/bin/env python3

import sys
from pathlib import Path

# Base directory for input folders
BASE_DIR = Path(
    "/Users/chadwalters/Library/Mobile Documents/com~apple~CloudDocs/_Input"
)

# Known processor types
PROCESSORS = ["_BearNotes", "_ChatGPTExport", "_ClaudeExport", "_XBookmarks"]


def get_current_mode():
    """Determine if Full or Small folders are currently active."""
    # Check the first processor to determine the mode
    base_folder = Path(BASE_DIR) / PROCESSORS[0]
    full_folder = Path(BASE_DIR) / "{}Full".format(PROCESSORS[0])

    if base_folder.exists() and full_folder.exists():
        return "Small"  # If we see both, the base one must be Small
    elif base_folder.exists():
        small_folder = Path(BASE_DIR) / "{}Small".format(PROCESSORS[0])
        return "Full" if small_folder.exists() else "Unknown"
    else:
        return "Unknown"


def rename_folders(current_mode):
    """Rename folders based on the current mode."""
    other_mode = "Small" if current_mode == "Full" else "Full"

    print(
        "\nRenaming folders to switch from {} to {}...".format(current_mode, other_mode)
    )

    for processor in PROCESSORS:
        base_folder = BASE_DIR / processor
        current_folder = BASE_DIR / "{}{}".format(processor, current_mode)
        target_folder = BASE_DIR / "{}{}".format(processor, other_mode)

        if base_folder.exists():
            print("Renaming {} → {}".format(base_folder, current_folder))
            base_folder.rename(current_folder)

        if target_folder.exists():
            print("Renaming {} → {}".format(target_folder, base_folder))
            target_folder.rename(base_folder)


def main():
    # Determine current mode
    current_mode = get_current_mode()

    if current_mode == "Unknown":
        print(
            "Error: Unable to determine if Full or Small folders are currently active."
        )
        print("Please ensure your folder structure is correct.")
        sys.exit(1)

    # Print current status
    print("\nCurrent Status:")
    print("=" * 40)
    print("Active folders are: {}".format(current_mode))
    print("\nThis means:")
    for processor in PROCESSORS:
        base = BASE_DIR / processor
        if base.exists():
            print("- {} is the {} version".format(base, current_mode))

    # Ask for confirmation
    response = input("\nDo you want to switch the active folders? (yes/no): ")
    if response.lower() not in ["y", "yes"]:
        print("Operation cancelled.")
        return

    # Perform the rename
    rename_folders(current_mode)
    print("\nFolder switch completed successfully!")


if __name__ == "__main__":
    main()
