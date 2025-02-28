"""
Main CLI entry point for the LLM wrapper.
"""

import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional

# Import the llm-core library as llm_core
import llm_core
import typer
from llm_core import (
    list_templates as llm_list_templates,
)
from rich.console import Console
from rich.markdown import Markdown

from llm.templates import TemplateManager
from llm.utils import format_piped_content, get_piped_content

# Create Typer app
app = typer.Typer(
    help="Enhanced wrapper for simonw/llm with sane defaults, better content handling, and rich output"
)

console = Console()

# Default values
DEFAULT_TEMPERATURE = 0
DEFAULT_TEMPLATE = "claude"
DEFAULT_MODEL = "anthropic/claude-3-7-sonnet-latest"

# Mapping of subcommands to supported features
SUBCOMMANDS_SUPPORTING_TEMPERATURE = ["prompt", "chat"]
SUBCOMMANDS_SUPPORTING_MARKDOWN = ["prompt"]
SUBCOMMANDS_SUPPORTING_PIPED_CONTENT = ["prompt"]
SUBCOMMANDS_SUPPORTING_SYSTEM_OPTION = ["chat", "prompt", "cmd"]
SUBCOMMANDS_SUPPORTING_TEMPLATE_OPTION = ["prompt", "chat"]
SUBCOMMANDS_SUPPORTING_MODEL_OPTION = ["prompt", "chat", "cmd"]


def get_piped_content() -> Optional[str]:
    """
    Check if content is being piped in and return it if so.
    """
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    # Common options
    temperature: Optional[float] = typer.Option(
        None, "-o", "--option", help="Temperature (0-1)"
    ),
    template: Optional[str] = typer.Option(
        None, "-t", "--template", help="Template name to use"
    ),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Model to use"),
    system: Optional[str] = typer.Option(None, "-s", "--system", help="System prompt"),
    # Format options
    format_stdin: bool = typer.Option(
        True, "--format-stdin/--no-format-stdin", help="Format piped content"
    ),
    md: bool = typer.Option(
        True, "--md/--no-md", help="Display output in markdown viewer"
    ),
    inline_code_lexer: str = typer.Option(
        "python", "-i", "--inline-code-lexer", help="Lexer for inline code blocks"
    ),
    stdin_tag: Optional[str] = typer.Option(
        None, "-st", "--stdin-tag", "--tag", help="Tag for piped content"
    ),
):
    """
    Enhanced wrapper for simonw/llm with sane defaults and improved output handling.
    """
    # If no subcommand is provided, default to 'prompt'
    if ctx.invoked_subcommand is None:
        # Save original args for later
        original_args = list(sys.argv[1:])

        # Replace the command with 'llm prompt' and re-run
        sys.argv = [sys.argv[0], "prompt"] + original_args
        app()
        return

    # Store options in the context for subcommands to use
    ctx.obj = {
        "temperature": temperature,
        "template": template,
        "model": model,
        "system": system,
        "format_stdin": format_stdin,
        "md": md,
        "inline_code_lexer": inline_code_lexer,
        "stdin_tag": stdin_tag,
    }


def build_llm_command(
    subcommand: str,
    ctx_obj: Dict[str, Any],
    args: List[str],
    piped_content: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Construct the llm command parameters using the llm-core API.
    Returns a dictionary of parameters to pass to the llm-core API.
    """
    template_mgr = TemplateManager()
    params = {
        "subcommand": subcommand,
        "args": args,
    }

    # Handle template (if no system prompt is provided)
    if (
        subcommand in SUBCOMMANDS_SUPPORTING_TEMPLATE_OPTION
        and ctx_obj.get("template")
        and not ctx_obj.get("system")
    ):
        params["template"] = ctx_obj["template"]

    # Handle system prompt
    if subcommand in SUBCOMMANDS_SUPPORTING_SYSTEM_OPTION and ctx_obj.get("system"):
        # If it's a template reference, resolve it
        if ctx_obj["system"] in template_mgr.list_templates():
            system_prompt = template_mgr.get_template_content(ctx_obj["system"])
        else:
            system_prompt = ctx_obj["system"]
        params["system"] = system_prompt

    # Handle temperature
    if (
        subcommand in SUBCOMMANDS_SUPPORTING_TEMPERATURE
        and ctx_obj.get("temperature") is not None
    ):
        params["options"] = {"temperature": ctx_obj["temperature"]}
    elif subcommand in SUBCOMMANDS_SUPPORTING_TEMPERATURE:
        params["options"] = {"temperature": DEFAULT_TEMPERATURE}

    # Handle model
    if subcommand in SUBCOMMANDS_SUPPORTING_MODEL_OPTION and ctx_obj.get("model"):
        params["model"] = ctx_obj["model"]
    elif subcommand in SUBCOMMANDS_SUPPORTING_MODEL_OPTION:
        params["model"] = DEFAULT_MODEL

    # Handle piped content
    if piped_content:
        params["content"] = piped_content

    return params


@app.command()
def prompt(
    ctx: typer.Context,
    prompt_text: List[str] = typer.Argument(None, help="Prompt text"),
):
    """
    Send a prompt to the LLM and display the response.
    """
    # Get piped content and format it if needed
    raw_piped_content = get_piped_content()
    piped_content = None

    if raw_piped_content and ctx.obj.get("format_stdin", True):
        piped_content = format_piped_content(
            raw_piped_content, stdin_tag=ctx.obj.get("stdin_tag")
        )
    elif raw_piped_content:
        piped_content = raw_piped_content

    # Create temporary file for output
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        # Build llm params and call API
        params = build_llm_command("prompt", ctx.obj, prompt_text, piped_content)

        # Use the llm-core API instead of subprocess
        try:
            result = llm_core.run_llm_command(**params)
            tmp.write(result)
            tmp.close()

            # Handle markdown display
            if ctx.obj.get("md", True):
                with open(tmp.name, "r") as f:
                    content = f.read()
                md = Markdown(
                    content,
                    code_theme="monokai",
                    inline_code_lexer=ctx.obj.get("inline_code_lexer", "python"),
                )
                console.print(md)
            else:
                with open(tmp.name, "r") as f:
                    sys.stdout.write(f.read())
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            sys.exit(1)
        finally:
            # Clean up temp file
            os.unlink(tmp.name)


@app.command()
def chat(
    ctx: typer.Context,
    message: List[str] = typer.Argument(None, help="Chat message"),
):
    """
    Start or continue a chat session with the LLM.
    """
    # Get piped content and format it if needed
    raw_piped_content = get_piped_content()
    piped_content = None

    if raw_piped_content and ctx.obj.get("format_stdin", True):
        piped_content = format_piped_content(
            raw_piped_content, stdin_tag=ctx.obj.get("stdin_tag")
        )
    elif raw_piped_content:
        piped_content = raw_piped_content

    params = build_llm_command("chat", ctx.obj, message, piped_content)

    # Use the llm-core API
    try:
        result = llm_core.run_llm_command(**params)

        # Handle markdown display
        if ctx.obj.get("md", True):
            md = Markdown(
                result,
                code_theme="monokai",
                inline_code_lexer=ctx.obj.get("inline_code_lexer", "python"),
            )
            console.print(md)
        else:
            sys.stdout.write(result)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@app.command()
def cmd(
    ctx: typer.Context,
    command: List[str] = typer.Argument(None, help="Command to execute"),
):
    """
    Execute a shell command and send its output to the LLM.
    """
    # This function still uses subprocess to run the shell command
    # but uses llm-core API for the LLM interaction
    result = subprocess.run(
        " ".join(command), shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        console.print(f"[bold red]Command error:[/bold red] {result.stderr}")
        sys.exit(result.returncode)

    # Send command output to LLM
    params = build_llm_command("prompt", ctx.obj, [], result.stdout)

    try:
        llm_result = llm_core.run_llm_command(**params)

        # Handle markdown display
        if ctx.obj.get("md", True):
            md = Markdown(
                llm_result,
                code_theme="monokai",
                inline_code_lexer=ctx.obj.get("inline_code_lexer", "python"),
            )
            console.print(md)
        else:
            sys.stdout.write(llm_result)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@app.command()
def templates():
    """
    List available templates.
    """
    template_mgr = TemplateManager()
    console.print("[bold]Local Templates:[/bold]")
    for template in template_mgr.list_templates():
        console.print(f"  • {template}")

    console.print("\n[bold]System Templates:[/bold]")
    for template in llm_list_templates():
        console.print(f"  • {template}")


def run():
    """
    Entry point for the CLI.
    """
    # Register shell completion if needed
    try:
        import click_completion

        click_completion.init()
    except ImportError:
        pass  # Optional dependency

    app()
