"""
Template management for the LLM CLI.
"""

import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import llm_core for template handling
import llm_core
import yaml
from llm_core import get_template_dir as llm_get_template_dir
from llm_core import list_templates as llm_list_templates
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
        # Try to get the templates path using llm_core
        try:
            template_dir = llm_get_template_dir()
            return Path(template_dir)
        except Exception as e:
            console.print(
                f"[yellow]Warning:[/yellow] Could not get templates path from llm_core: {e}"
            )

            # Fallback to default locations
            # Check if it's in the standard location first
            user_data_dir = Path.home() / ".local" / "share"
            if os.name == "nt":  # Windows
                user_data_dir = Path(
                    os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
                )

            default_path = user_data_dir / "io.datasette.llm" / "templates"
            if default_path.exists():
                return default_path

            # Create the directory if it doesn't exist
            default_path.mkdir(parents=True, exist_ok=True)
            return default_path

    def list_templates(self) -> List[str]:
        """
        List available templates.
        """
        # Get both system and local templates
        local_templates = [p.stem for p in self.templates_path.glob("*.yaml")]
        return sorted(local_templates)

    def get_template_path(self, template_name: str) -> Optional[Path]:
        """
        Get the path to a template.
        """
        # Check if it's a file path
        if Path(template_name).exists() and Path(template_name).is_file():
            return Path(template_name)

        # Check if it's a template name
        template_path = self.templates_path / f"{template_name}.yaml"
        if template_path.exists():
            return template_path

        # Check if it's a template name without .yaml extension
        if not template_name.endswith(".yaml"):
            template_path = self.templates_path / f"{template_name}"
            if template_path.exists():
                return template_path

        return None

    def get_template_content(self, template_name: str, raw: bool = False) -> str:
        """
        Get the content of a template.

        Args:
            template_name: The name of the template or a path to a template file
            raw: If True, return the raw template content without processing

        Returns:
            The template content
        """
        # If it's a system template, try to get it from llm_core
        try:
            if template_name in llm_list_templates():
                return llm_core.get_template(template_name)
        except Exception:
            pass  # Fall back to local handling

        # Try to get the template from our local collection
        template_path = self.get_template_path(template_name)
        if not template_path:
            raise ValueError(f"Template not found: {template_name}")

        with open(template_path, "r") as f:
            content = f.read()

        if raw:
            return content

        # Process the template content
        try:
            yaml_content = yaml.safe_load(content)
            if not isinstance(yaml_content, dict):
                return content

            # Get the prompt from the YAML
            prompt = yaml_content.get("prompt", "")
            if not prompt:
                # Fall back to using the entire content
                return content

            return prompt
        except yaml.YAMLError:
            # If it's not valid YAML, return the content as is
            return content

    def merge_templates(self, template1: str, template2: str) -> str:
        """
        Merge two templates and return the result.

        Args:
            template1: The first template (name or content)
            template2: The second template (name or content)

        Returns:
            The merged template content
        """
        # Get template content
        content1 = self.get_template_content(template1)
        content2 = self.get_template_content(template2)

        # Create a temporary file with the merged content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            merged_content = f"{content1}\n\n{content2}"
            tmp.write(merged_content)
            tmp_path = Path(tmp.name)

        # Schedule deletion for later (to allow the command to use the file)
        self._schedule_deletion(tmp_path)

        return str(tmp_path)

    def _schedule_deletion(self, file_path: Path):
        """
        Schedule a file for deletion after 10 seconds.
        """
        import threading

        def delete_file():
            time.sleep(10)
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                console.print(
                    f"[bold red]Error deleting temporary file {file_path}:[/bold red] {e}"
                )

        thread = threading.Thread(target=delete_file)
        thread.daemon = True
        thread.start()

    def interpolate_template_variables(
        self, template_content: str, variables: Dict[str, Any] = None
    ) -> str:
        """
        Interpolate variables in a template.

        Args:
            template_content: The template content
            variables: The variables to interpolate (defaults to empty dict)

        Returns:
            The interpolated template content
        """
        if not variables:
            variables = {}

        # Simple variable replacement using string formatting
        content = template_content

        # Find all variables in the format {variable_name}
        var_pattern = r"\{([a-zA-Z0-9_]+)\}"
        matches = set(re.findall(var_pattern, content))

        # For each variable, if it's in the provided variables, replace it
        for var_name in matches:
            if var_name in variables:
                placeholder = "{" + var_name + "}"
                content = content.replace(placeholder, str(variables[var_name]))

        return content

    def create_template(self, name: str, content: str) -> Path:
        """
        Create a new template file.

        Args:
            name: The name of the template
            content: The content of the template

        Returns:
            The path to the created template file
        """
        # Make sure the templates directory exists
        self.templates_path.mkdir(parents=True, exist_ok=True)

        # Create the template file path
        if not name.endswith(".yaml"):
            name = f"{name}.yaml"

        template_path = self.templates_path / name

        # Write the content to the file
        with open(template_path, "w") as f:
            f.write(content)

        return template_path
