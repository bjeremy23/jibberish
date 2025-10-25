"""
Tool system for jibberish AI interactions.

This module provides a framework for creating and using tools that can be called
by the AI to gather additional context for more informed responses.
"""

from .base import Tool, ToolRegistry
from .file_reader import FileReaderTool
from .file_writer import FileWriterTool
from .linux_command import LinuxCommandTool
from .mcp_server_manager import MCPServerManager
from .mcp_client import create_mcp_tools
from .mcp_registry import get_mcp_registry
from ..utils import is_debug_enabled

# Register built-in tools
ToolRegistry.register(FileReaderTool())
ToolRegistry.register(FileWriterTool())
ToolRegistry.register(LinuxCommandTool())

# Start and register all configured MCP servers
try:
    # Get the MCP registry
    mcp_registry = get_mcp_registry()
    enabled_servers = mcp_registry.get_enabled_servers()
    
    if not enabled_servers:
        if is_debug_enabled():
            print("No MCP servers configured or enabled")
    else:
        if is_debug_enabled():
            print(f"Discovering {len(enabled_servers)} enabled MCP servers")
        
        # Discover all MCP servers
        mcp_manager = MCPServerManager()
        running_servers = mcp_manager.discover_all_servers()
        
        if not running_servers:
            if is_debug_enabled():
                print("No MCP servers discovered successfully")
        else:
            # Register tools for each running MCP server
            for server_info in running_servers:
                server_config = server_info['server_config']
                conn_type = server_info['connection_type']
                
                if is_debug_enabled():
                    print(f"Registering tools for MCP server: {server_config.name} ({conn_type})")
                
                try:
                    # Create and register MCP proxy tools
                    mcp_tools = create_mcp_tools(server_info, server_config)
                    
                    for tool in mcp_tools:
                        ToolRegistry.register(tool)
                    
                    print(f"Registered {len(mcp_tools)} tools from MCP server '{server_config.name}'")
                    
                except Exception as e:
                    print(f"Warning: Failed to register tools for MCP server '{server_config.name}': {e}")
        
except Exception as e:
    print(f"Warning: Could not initialize MCP servers: {e}")
    import traceback
    if is_debug_enabled():
        traceback.print_exc()

__all__ = ['Tool', 'ToolRegistry', 'FileReaderTool', 'FileWriterTool', 'LinuxCommandTool']