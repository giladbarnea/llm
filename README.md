# LLM Wrapper

An enhanced wrapper for [simonw/llm](https://github.com/simonw/llm) with sane defaults, better content handling, and rich output.

## Features

- **Sane Defaults**: Sets optimal temperature and model defaults for each command type
- **Rich Markdown Output**: Displays LLM responses in a beautiful markdown viewer with syntax highlighting and customizable inline code lexer
- **Template Management**: Load templates by name or path, merge templates, and interpolate variables
- **Enhanced Piped Content**: Format piped content for better prompt engineering and tagging
- **Direct API Integration**: Uses the llm Python API directly instead of subprocess calls for better reliability and efficiency
- **Shell Completion**: Integrates with your shell for command completion

## Installation

Requirements:
- Python 3.11+

Install the package:

```bash
pip install llm
```

## Usage

Basic usage:

```bash
llm --help
```
