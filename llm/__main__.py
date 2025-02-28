"""
Main entry point for the LLM CLI.
"""

import typer

from llm.cli import app as main_app
from llm.commands import app as commands_app

# Combine the apps
app = typer.Typer(help="Enhanced wrapper for simonw/llm")
app.add_typer(main_app)
app.add_typer(commands_app, name="commands")

if __name__ == "__main__":
    app()
