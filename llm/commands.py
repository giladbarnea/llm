"""
Convenience commands for specific templates and models.
"""

import sys
from typing import List, Optional

import llm_core
import typer
from rich.console import Console
from rich.markdown import Markdown

from llm.templates import TemplateManager

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

    # Run the prompt using llm_core
    try:
        result = llm_core.run_llm_command(
            subcommand="prompt",
            args=text,
            system=merged_content,
            model="anthropic/claude-3-sonnet-20240229",
            options={"temperature": 0},
        )

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

    # Run the prompt using llm_core
    try:
        result = llm_core.run_llm_command(
            subcommand="prompt",
            args=prompt,
            system=system_prompt,
            model="anthropic/claude-3-sonnet-20240229",
            options={"temperature": 0},
        )

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
    model_to_use = model or "anthropic/claude-3-sonnet-20240229"

    # Execute the command and get the output
    import subprocess

    result = subprocess.run(
        " ".join(command), shell=True, capture_output=True, text=True
    )

    if result.returncode != 0:
        console.print(f"[bold red]Command error:[/bold red] {result.stderr}")
        sys.exit(result.returncode)

    # Run the prompt with the command output using llm_core
    try:
        llm_result = llm_core.run_llm_command(
            subcommand="prompt",
            args=[],
            content=result.stdout,
            system=system_prompt,
            model=model_to_use,
            options={"temperature": 0},
        )

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

    # Run the prompt using llm_core
    try:
        result = llm_core.run_llm_command(
            subcommand="prompt",
            args=prompt,
            system=template_content,
            model="anthropic/claude-3-sonnet-20240229",
            options={"temperature": 0},
        )

        # Display the result
        if ctx.obj and ctx.obj.get("md", True):
            md = Markdown(result, code_theme="monokai")
            console.print(md)
        else:
            sys.stdout.write(result)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
