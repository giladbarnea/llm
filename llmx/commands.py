"""
Convenience commands for specific templates and models.
"""

import sys
from typing import List, Optional

import llm
import typer
from rich.console import Console
from rich.markdown import Markdown

from llmx.templates import TemplateManager

app = typer.Typer(help="Additional helper commands for specific templates and models")
console = Console()
template_mgr = TemplateManager()


@app.command()
def simplify(
    ctx: typer.Context,
    text: List[str] = typer.Argument(None, help="Text to simplify"),
):
    """
    Simplify the given text using the simplify template.
    """
    # Get templates and merge them
    claude_template = template_mgr.get_template_content("claude")
    simplify_template = template_mgr.get_template_content("simplify")
    merged_content = f"{claude_template}\n\n{simplify_template}"

    # Run the prompt using llm
    try:
        model = llm.get_model("anthropic/claude-3-sonnet-20240229")
        response = model.prompt(
            " ".join(text) if text else "", system=merged_content, temperature=0
        )
        result = response.text()

        # Display the result
        if ctx.obj and ctx.obj.get("md", True):
            md = Markdown(result, code_theme="monokai")
            console.print(md)
        else:
            sys.stdout.write(result)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@app.command()
def zshclaude(
    ctx: typer.Context,
    prompt: List[str] = typer.Argument(None, help="Prompt for zshclaude"),
):
    """
    Run a prompt using the zshclaude template.
    """
    # Get the zshclaude template
    system_prompt = template_mgr.get_template_content("zshclaude")

    # Run the prompt using llm
    try:
        model = llm.get_model("anthropic/claude-3-sonnet-20240229")
        response = model.prompt(
            " ".join(prompt) if prompt else "", system=system_prompt, temperature=0
        )
        result = response.text()

        # Display the result
        if ctx.obj and ctx.obj.get("md", True):
            md = Markdown(result, code_theme="monokai")
            console.print(md)
        else:
            sys.stdout.write(result)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@app.command()
def zshcmd(
    ctx: typer.Context,
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Model to use"),
    command: List[str] = typer.Argument(None, help="Command for zshcmd"),
):
    """
    Run a command using the zshcmd template.
    """
    # Get the zshcmd template
    system_prompt = template_mgr.get_template_content("zshcmd")

    # Use the specified model or default
    model_name = model or "anthropic/claude-3-sonnet-20240229"

    # Execute the command and get the output
    import subprocess

    result = subprocess.run(
        " ".join(command), shell=True, capture_output=True, text=True
    )

    if result.returncode != 0:
        console.print(f"[bold red]Command error:[/bold red] {result.stderr}")
        sys.exit(result.returncode)

    # Run the prompt with the command output using llm
    try:
        llm_model = llm.get_model(model_name)
        response = llm_model.prompt(result.stdout, system=system_prompt, temperature=0)
        llm_result = response.text()

        # Display the result
        if ctx.obj and ctx.obj.get("md", True):
            md = Markdown(llm_result, code_theme="monokai")
            console.print(md)
        else:
            sys.stdout.write(llm_result)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@app.command()
def pyclaude(
    ctx: typer.Context,
    prompt: List[str] = typer.Argument(None, help="Prompt for pyclaude"),
):
    """
    Run a prompt using the pyclaude template.
    """
    # Get the pyclaude template
    template_content = template_mgr.get_template_content("pyclaude")

    # Run the prompt using llm
    try:
        model = llm.get_model("anthropic/claude-3-sonnet-20240229")
        response = model.prompt(
            " ".join(prompt) if prompt else "", system=template_content, temperature=0
        )
        result = response.text()

        # Display the result
        if ctx.obj and ctx.obj.get("md", True):
            md = Markdown(result, code_theme="monokai")
            console.print(md)
        else:
            sys.stdout.write(result)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
