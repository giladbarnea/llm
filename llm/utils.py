"""
Utility functions for the LLM CLI.
"""

import os
import sys
from typing import Optional


def get_piped_content() -> Optional[str]:
    """
    Check if content is being piped to the command and read it.

    Returns:
        The piped content or None if no content is piped
    """
    if not os.isatty(sys.stdin.fileno()):
        content = sys.stdin.read().strip()
        if content:
            return content
    return None


def format_piped_content(content: str, stdin_tag: Optional[str] = None) -> str:
    """
    Format piped content for better prompt engineering.

    Args:
        content: The content to format
        stdin_tag: Optional tag to add to the content (e.g., 'python', 'bash', 'json')

    Returns:
        Formatted content
    """
    if not content:
        return content

    if stdin_tag:
        # Convert underscore_separated tag to space separated for display
        tag_display = stdin_tag.replace("_", " ")

        # Convert to Title_Case_With_Underscores for the XML-like tag
        xml_tag = "".join(word.title() for word in tag_display.split())

        return (
            f"Given the following {tag_display}:\n\n"
            f"<{xml_tag}>\n"
            f"{content}\n"
            f"</{xml_tag}>\n\n"
        )
    else:
        return f"Given the following:\n\n{content}\n---\n"


def shorten_string(s: str, max_length: int = 310) -> str:
    """
    Shorten a string if it's longer than max_length.

    Args:
        s: The string to shorten
        max_length: The maximum length of the string

    Returns:
        The shortened string
    """
    if len(s) <= max_length:
        return s

    # Show first 200 chars and last 100 chars
    prefix_length = min(200, int(2 / 3 * max_length) - 5)
    suffix_length = min(100, int(1 / 3 * max_length) - 5)

    prefix = s[:prefix_length]
    suffix = s[-suffix_length:]

    if "\n" in s or "\n" in suffix:
        return f"{prefix}\n...\n{suffix}"
    else:
        return f"{prefix} ... {suffix}"
