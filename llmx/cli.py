"""
Main CLI entry point for the LLM wrapper.
"""

import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.markdown import Markdown

import llm
from llmx.templates import TemplateManager

# Create Typer app
app = typer.Typer(
    help="Enhanced wrapper for simonw/llm with sane defaults, better content handling, and rich output"
)

console = Console()

# Default values
DEFAULT_TEMPERATURE = 0
DEFAULT_MODEL = "gpt-4o-mini"

# User path for templates (same as from llm)
USER_PATH = os.environ.get("LLM_USER_PATH") or os.path.join(
    os.path.expanduser("~"),
    "Library/Application Support/io.datasette.llm"
    if sys.platform == "darwin"
    else ".local/share/io.datasette.llm",
)

# Subcommands that support various options
SUBCOMMANDS_SUPPORTING_SYSTEM_OPTION = ["prompt", "chat"]
SUBCOMMANDS_SUPPORTING_TEMPLATE_OPTION = ["prompt", "chat"]
SUBCOMMANDS_SUPPORTING_TEMPERATURE = ["prompt", "chat"]
SUBCOMMANDS_SUPPORTING_MODEL_OPTION = ["prompt", "chat"]

# Import the remaining modules
# Import other commands
from llmx.commands import app as commands_app
from llmx.utils import format_piped_content, get_piped_content


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
    Enhanced wrapper for simonw/llm with sane defaults, better content handling, and rich output.
    """
    # Set up context object if not already done
    if ctx.obj is None:
        ctx.obj = {}

    # Store options in context
    ctx.obj.update(
        {
            "temperature": temperature,
            "template": template,
            "model": model,
            "system": system,
            "format_stdin": format_stdin,
            "md": md,
            "inline_code_lexer": inline_code_lexer,
            "stdin_tag": stdin_tag,
        }
    )

    # Skip if --help was passed
    if ctx.invoked_subcommand is None and not sys.argv[1:]:
        ctx.invoke(prompt, ctx=ctx)
        return


def build_llm_params(
    subcommand: str,
    ctx_obj: Dict[str, Any],
    args: List[str],
    piped_content: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build parameters for llm API calls.
    """
    template_mgr = TemplateManager()
    params = {}

    # Handle prompt content
    if args and isinstance(args, list):
        prompt_content = " ".join(args) if args else ""
    else:
        prompt_content = ""
    if piped_content:
        # If we have piped content and prompt content, use the prompt content normally
        # and add the piped content to the prompt
        if prompt_content:
            prompt_content = f"{prompt_content}\n\n{piped_content}"
        else:
            prompt_content = piped_content

    params["prompt"] = prompt_content

    # Handle system prompt
    if (
        subcommand in SUBCOMMANDS_SUPPORTING_SYSTEM_OPTION
        and ctx_obj
        and ctx_obj.get("system")
    ):
        # If it's a template reference, resolve it
        if ctx_obj["system"] in template_mgr.list_templates():
            system_prompt = template_mgr.get_template_content(ctx_obj["system"])
        else:
            system_prompt = ctx_obj["system"]
        params["system"] = system_prompt

    # Handle temperature
    if (
        subcommand in SUBCOMMANDS_SUPPORTING_TEMPERATURE
        and ctx_obj
        and ctx_obj.get("temperature") is not None
    ):
        params["temperature"] = ctx_obj["temperature"]
    elif subcommand in SUBCOMMANDS_SUPPORTING_TEMPERATURE:
        params["temperature"] = DEFAULT_TEMPERATURE

    # Handle model name (returned separately)
    model_name = DEFAULT_MODEL
    if (
        subcommand in SUBCOMMANDS_SUPPORTING_MODEL_OPTION
        and ctx_obj
        and ctx_obj.get("model")
    ):
        model_name = ctx_obj["model"]

    return params, model_name


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
        params, model_name = build_llm_params(
            "prompt", ctx.obj, prompt_text, piped_content
        )

        # Use the llm API
        try:
            model = llm.get_model(model_name)
            response = model.prompt(**params)
            result = response.text()
            tmp.write(result)
            tmp.close()

            # Handle markdown display
            if ctx.obj.get("md", True):
                md = Markdown(result, code_theme="monokai")
                console.print(md)
            else:
                with open(tmp.name, "r") as f:
                    sys.stdout.write(f.read())
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            sys.exit(1)
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp.name)
            except:
                pass


@app.command()
def chat(
    ctx: typer.Context,
    message: List[str] = typer.Argument(None, help="Chat message"),
):
    """
    Start an interactive chat with the selected model.
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

    # Build llm params and prepare for chat
    params, model_name = build_llm_params("chat", ctx.obj, message, piped_content)

    # If there's an initial message, send it first
    try:
        model = llm.get_model(model_name)

        # Create a conversation
        conversation = None
        if params.get("prompt"):
            # Send the initial message
            response = model.prompt(
                params["prompt"],
                system=params.get("system"),
                temperature=params.get("temperature", DEFAULT_TEMPERATURE),
            )
            result = response.text()

            # Display response
            if ctx.obj.get("md", True):
                md = Markdown(result, code_theme="monokai")
                console.print(md)
            else:
                sys.stdout.write(result)

            # Get the conversation ID for continuation
            conversation = response.response.conversation

        # Run the interactive chat
        console.print(
            "\nEntering interactive chat mode. Type 'exit' or 'quit' to exit."
        )
        console.print("Type '!multi' to enter multiple lines, then '!end' to finish")

        # Interactive chat loop
        while True:
            user_input = input("> ")
            if user_input.lower() in ["exit", "quit"]:
                break

            # Call the API with input
            response = model.prompt(
                user_input,
                system=params.get("system"),
                temperature=params.get("temperature", DEFAULT_TEMPERATURE),
                conversation=conversation,
            )
            result = response.text()

            # Update conversation ID for continuation
            conversation = response.response.conversation

            # Display response
            if ctx.obj.get("md", True):
                md = Markdown(result, code_theme="monokai")
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
    Execute a command and pass the output to the LLM for analysis.
    """
    if not command:
        console.print("[bold red]Error:[/bold red] No command provided")
        sys.exit(1)

    # Execute the command and get the output
    try:
        result = subprocess.run(
            " ".join(command), shell=True, capture_output=True, text=True
        )

        if result.returncode != 0:
            console.print(f"[bold red]Command error:[/bold red] {result.stderr}")
            sys.exit(result.returncode)

        # Build the LLM params and get the model name
        params, model_name = build_llm_params("prompt", ctx.obj, [], result.stdout)

        # Call the LLM API
        model = llm.get_model(model_name)
        response = model.prompt(
            params["prompt"],
            system=params.get("system"),
            temperature=params.get("temperature", DEFAULT_TEMPERATURE),
        )
        llm_result = response.text()

        # Display the result
        if ctx.obj.get("md", True):
            md = Markdown(llm_result, code_theme="monokai")
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
    templates = template_mgr.list_templates()

    if not templates:
        console.print("No templates found.")
        return

    console.print("Available templates:")
    for template in sorted(templates):
        console.print(f"  - {template}")


# Add subcommands
app.add_typer(commands_app, name="cmd")


def run():
    """
    Entry point for the CLI.
    """
    app()
