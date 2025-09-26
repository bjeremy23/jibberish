"""
Tool system for jibberish AI interactions.

This module provides a framework for creating and using tools that can be called
by the AI to gather additional context for more informed responses.
"""

from .base import Tool, ToolRegistry
from .file_reader import FileReaderTool
from .file_writer import FileWriterTool
from .linux_command import LinuxCommandTool
from .mcp_container_manager import MCPContainerManager
from .mcp_client import create_mcp_kubernetes_tools
from ..utils import is_debug_enabled

# Register built-in tools
ToolRegistry.register(FileReaderTool())
ToolRegistry.register(FileWriterTool())
ToolRegistry.register(LinuxCommandTool())

# Check if MCP Kubernetes container is running and register tools if available
try:
    mcp_manager = MCPContainerManager()
    container_info = mcp_manager.find_running_container()
    
    if container_info:
        if is_debug_enabled():
            print(f"Found MCP Kubernetes container: {container_info['name']}")
        try:
            # Create and register MCP Kubernetes proxy tools
            mcp_tools = create_mcp_kubernetes_tools(container_info['container_id'])
            for tool in mcp_tools:
                ToolRegistry.register(tool)
            if is_debug_enabled():
                print(f"Registered {len(mcp_tools)} MCP Kubernetes tools")
        except Exception as e:
            print(f"Warning: Failed to register MCP tools: {e}")
    else:
        if is_debug_enabled():
            print("No MCP Kubernetes container found - skipping Kubernetes tools")
        
except Exception as e:
    print(f"Warning: Could not check MCP container status: {e}")

__all__ = ['Tool', 'ToolRegistry', 'FileReaderTool', 'FileWriterTool', 'LinuxCommandTool']