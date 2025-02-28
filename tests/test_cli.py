"""
Tests for the CLI entry point.
"""

import subprocess
from pathlib import Path


def test_llm_smoke_test():
    """
    Smoke test for the CLI - verify that running 'uv run bin/llm' with no arguments
    returns a string and 0 status code.
    """
    # Get the root directory of the project
    root_dir = Path(__file__).parent.parent.absolute()

    # Run the command
    result = subprocess.run(
        ["uv", "run", str(root_dir / "bin" / "llm")],
        capture_output=True,
        text=True,
    )

    # Check that the command returned a 0 status code
    assert result.returncode == 0

    # Check that the command returned some output
    assert result.stdout.strip() != ""


def test_llm_with_help_argument():
    """
    Test that running 'uv run bin/llm --help' returns help text and 0 status code.
    """
    # Get the root directory of the project
    root_dir = Path(__file__).parent.parent.absolute()

    # Run the command
    result = subprocess.run(
        ["uv", "run", str(root_dir / "bin" / "llm"), "--help"],
        capture_output=True,
        text=True,
    )

    # Check that the command returned a 0 status code
    assert result.returncode == 0

    # Check that the command returned some output
    assert result.stdout.strip() != ""

    # Check that the output contains help text
    assert "Usage:" in result.stdout
    assert "Options" in result.stdout
    assert "Commands" in result.stdout


def test_llm_with_invalid_argument():
    """
    Test that running 'uv run bin/llm' with an invalid argument returns a non-zero status code.
    """
    # Get the root directory of the project
    root_dir = Path(__file__).parent.parent.absolute()

    # Run the command with an invalid argument
    result = subprocess.run(
        ["uv", "run", str(root_dir / "bin" / "llm"), "--invalid-argument"],
        capture_output=True,
        text=True,
    )

    # Check that the command returned a non-zero status code
    assert result.returncode != 0

    # Check that the command returned an error message
    assert result.stderr.strip() != ""
    assert "Error" in result.stderr


def test_llm_prompt_command():
    """
    Test that running 'uv run bin/llm prompt' with a simple text input
    returns a 0 status code.

    Note: This test may take longer to run as it will actually make an API call
    to the LLM service. It's skipped by default to avoid unnecessary API calls
    during regular testing.
    """
    import pytest

    pytest.skip("Skipping test to avoid unnecessary API calls")

    # Get the root directory of the project
    root_dir = Path(__file__).parent.parent.absolute()

    # Run the command with a simple prompt
    # Using a very simple prompt to minimize token usage
    result = subprocess.run(
        ["uv", "run", str(root_dir / "bin" / "llm"), "prompt", "hi"],
        capture_output=True,
        text=True,
        timeout=30,  # Add a timeout to prevent hanging
    )

    # Check that the command returned a 0 status code
    assert result.returncode == 0

    # Check that the command returned some output
    assert result.stdout.strip() != ""
