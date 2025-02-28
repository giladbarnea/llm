"""
Template management for the LLM CLI.
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import llm
import yaml
from llm.templates import Template
from rich.console import Console

console = Console()


class TemplateManager:
    """
    Manages LLM templates, including loading, merging, and interpolating variables.
    """

    def __init__(self):
        """
        Initialize the template manager.
        """
        self.templates_path = self._get_templates_path()

    def _get_templates_path(self) -> Path:
        """
        Get the path to the templates directory.
        """
        # Try to get the templates path using llm
        try:
            # The llm library uses llm.user_dir() to get the base user directory
            base_dir = llm.user_dir()
            templates_path = base_dir / "templates"
            if not templates_path.exists():
                templates_path.mkdir(parents=True, exist_ok=True)
            return templates_path
        except Exception as e:
            console.print(
                f"[yellow]Warning:[/yellow] Could not get templates path from llm: {e}"
            )
            # Fallback to standard location
            user_home = Path.home()
            if os.name == "posix":  # Linux/Mac
                base_path = user_home / (
                    "Library/Application Support/io.datasette.llm"
                    if os.uname().sysname == "Darwin"
                    else ".local/share/io.datasette.llm"
                )
            else:  # Windows
                base_path = user_home / "AppData/Local/io.datasette.llm"

            templates_path = base_path / "templates"
            templates_path.mkdir(parents=True, exist_ok=True)
            return templates_path

    def list_templates(self) -> List[str]:
        """
        List available templates.
        """
        # Get system templates using llm API
        system_templates = llm.get_templates()

        # Get user templates
        user_templates = []
        if self.templates_path.exists():
            user_templates = [f.stem for f in self.templates_path.glob("*.yaml")]

        # Combine and deduplicate
        all_templates = list(set(system_templates + user_templates))
        return sorted(all_templates)

    def get_template_path(self, template_name: str) -> Optional[Path]:
        """
        Get the path to a template file.
        Returns None if not found.
        """
        # Check user templates first
        template_path = self.templates_path / f"{template_name}.yaml"
        if template_path.exists():
            return template_path

        # If not found, try to get it from llm system templates
        try:
            template_content = llm.get_template(template_name)
            if template_content:
                # Create a temporary file for the template
                fd, temp_path = tempfile.mkstemp(suffix=".yaml")
                os.close(fd)
                temp_path = Path(temp_path)
                temp_path.write_text(template_content)
                self._schedule_deletion(temp_path)
                return temp_path
        except Exception:
            pass

        return None

    def get_template_content(self, template_name: str, raw: bool = False) -> str:
        """
        Get the content of a template by name.
        If raw is True, returns the raw YAML content, otherwise returns the prompt.
        """
        # Use llm.get_template which handles both system and user templates
        try:
            content = llm.get_template(template_name)
            if content:
                if raw:
                    return content

                # Parse the YAML and extract the prompt
                try:
                    template_data = yaml.safe_load(content)
                    if template_data and "prompt" in template_data:
                        return template_data["prompt"]
                    else:
                        # If no prompt field, return the entire content
                        return content
                except yaml.YAMLError:
                    # If not valid YAML, return as is
                    return content
        except Exception:
            pass

        # If template not found
        raise ValueError(f"Template '{template_name}' not found")

    def merge_templates(self, template1: str, template2: str) -> str:
        """
        Merge two templates by combining their prompts.
        """
        content1 = self.get_template_content(template1)
        content2 = self.get_template_content(template2)
        return f"{content1}\n\n{content2}"

    def _schedule_deletion(self, file_path: Path):
        """
        Schedule a file for deletion after a delay.
        Helps with temporary files for system templates.
        """
        delay = 60  # 1 minute

        def delete_file():
            try:
                time.sleep(delay)
                if file_path.exists():
                    file_path.unlink()
            except Exception:
                pass

        # Start thread to delete file after delay
        import threading

        threading.Thread(target=delete_file, daemon=True).start()

    def interpolate_template_variables(
        self, template_content: str, variables: Dict[str, Any] = None
    ) -> str:
        """
        Interpolate variables in a template using llm.templates.Template.
        """
        if not variables:
            return template_content

        # Create a Template instance
        template = Template(
            name="temp",  # Temporary name
            prompt=template_content,  # Use the content as prompt
        )

        try:
            # Use Template.interpolate to handle variable substitution
            interpolated_prompt, _ = template.evaluate("", variables)
            return interpolated_prompt or template_content
        except Template.MissingVariables:
            # If variables are missing, return the original content
            return template_content
        except Exception as e:
            console.print(
                f"[yellow]Warning:[/yellow] Error interpolating variables: {e}"
            )
            return template_content

    def create_template(self, name: str, content: str) -> Path:
        """
        Create a new template with the given name and content.
        Returns the path to the new template file.
        """
        # Make sure the templates directory exists
        self.templates_path.mkdir(parents=True, exist_ok=True)

        # Create the template file
        template_path = self.templates_path / f"{name}.yaml"

        # Check if it's already in YAML format, if not wrap it
        if content.strip().startswith("{") or content.strip().startswith("prompt:"):
            # Content is already in YAML format
            template_path.write_text(content)
        else:
            # Wrap content in YAML format
            newline_indent = "\n  "
            simple_newline = "\n"
            yaml_content = f"prompt: |{newline_indent}{content.replace(simple_newline, newline_indent)}"
            template_path.write_text(yaml_content)

        return template_path
