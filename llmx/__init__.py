"""
LLM CLI wrapper providing enhanced functionality over simonw/llm.
"""

__version__ = "0.1.0"

from llm.cli import app, run

# Import commands for easier access
from llm.commands import pyclaude, simplify, zshclaude, zshcmd
from llm.templates import TemplateManager
from llm.utils import format_piped_content, get_piped_content
