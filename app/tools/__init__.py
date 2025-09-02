"""
Tool system for jibberish AI interactions.

This module provides a framework for creating and using tools that can be called
by the AI to gather additional context for more informed responses.
"""

from .base import Tool, ToolRegistry
from .file_reader import FileReaderTool
from .file_writer import FileWriterTool

# Register built-in tools
ToolRegistry.register(FileReaderTool())
ToolRegistry.register(FileWriterTool())

__all__ = ['Tool', 'ToolRegistry', 'FileReaderTool', 'FileWriterTool']