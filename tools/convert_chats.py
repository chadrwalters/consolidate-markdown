#!/usr/bin/env python3
"""
ChatGPT Export Converter

This script converts ChatGPT conversation exports (conversations.json) into markdown files.
Each conversation is converted to a separate markdown file with the format: YYYYMMDD_Title.md

Usage:
    1. Export your conversations from ChatGPT
    2. Place this script in the same directory as conversations.json
    3. Run the script: python3 convert_chats.py
    4. Markdown files will be created in a 'markdown_chats' subdirectory

The script handles:
    - Conversation metadata (title, date)
    - Messages in chronological order
    - Role-based formatting (user, assistant)
    - Timestamps for each message
"""

import json
import os
from datetime import datetime


def create_markdown_folder():
    """Create markdown_chats directory if it doesn't exist."""
    md_folder = "markdown_chats"
    if not os.path.exists(md_folder):
        os.makedirs(md_folder)
    return md_folder


def sanitize_filename(title):
    """Remove or replace invalid filename characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, "_")
    return title


def format_message(message):
    """Format a single message with role and timestamp."""
    if not message:
        return ""

    content = message.get("content", {})
    parts = content.get("parts", [])
    text = "\n".join(str(part) for part in parts if part)

    role = message.get("author", {}).get("role", "unknown")
    create_time = message.get("create_time")
    timestamp = ""
    if create_time:
        try:
            timestamp = datetime.fromtimestamp(create_time).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except:
            pass

    return f"### {role.capitalize()} ({timestamp})\n\n{text}\n\n"


def process_conversation(conversation, folder):
    """Process a single conversation and write to markdown file."""
    title = conversation.get("title", "Untitled Chat")
    create_time = conversation.get("create_time", 0)
    date_str = datetime.fromtimestamp(create_time).strftime("%Y%m%d")

    # Create filename with date prefix and sanitized title
    filename = f"{date_str}_{sanitize_filename(title)}.md"
    filepath = os.path.join(folder, filename)

    # Process messages in chronological order
    messages = []
    mapping = conversation.get("mapping", {})
    for node_id, node in mapping.items():
        if node.get("message"):
            messages.append(
                (node.get("message", {}).get("create_time", 0), node.get("message", {}))
            )

    # Sort messages by creation time
    messages.sort(key=lambda x: x[0] if x[0] else 0)

    # Write to markdown file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        create_time_str = datetime.fromtimestamp(create_time).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        try:
            create_time = datetime.strptime(create_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            print(f"Error parsing create time: {e}")
            pass
        f.write(f"Date: {create_time_str}\n\n")

        for _, message in messages:
            f.write(format_message(message))

    print(f"Created: {filename}")


def main():
    """Main function to process all conversations."""
    try:
        # Read conversations
        with open("conversations.json", "r", encoding="utf-8") as f:
            conversations = json.load(f)

        # Create markdown folder
        md_folder = create_markdown_folder()

        # Process each conversation
        for conversation in conversations:
            try:
                process_conversation(conversation, md_folder)
            except Exception as e:
                print(
                    f"Error processing conversation: {conversation.get('title', 'Unknown')} - {str(e)}"
                )

    except FileNotFoundError:
        print("Error: conversations.json not found in current directory")
    except json.JSONDecodeError:
        print("Error: conversations.json is not valid JSON")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
