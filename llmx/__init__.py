"""
LLM CLI wrapper providing enhanced functionality over simonw/llm.
"""

__version__ = "0.1.0"

from llmx.cli import app, run

# Import commands for easier access
from llmx.commands import pyclaude, simplify, zshclaude, zshcmd
from llmx.templates import TemplateManager
from llmx.utils import format_piped_content, get_piped_content
