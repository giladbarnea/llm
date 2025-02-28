"""
Main entry point for the LLM CLI.
"""

import typer

from llmx.cli import app as main_app
from llmx.commands import app as commands_app

# Combine the apps
app = typer.Typer(help="Enhanced wrapper for simonw/llm")
app.add_typer(main_app)
app.add_typer(commands_app, name="commands")

if __name__ == "__main__":
    app()
