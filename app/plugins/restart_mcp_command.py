"""
Restart MCP command plugin.
Reloads MCP server registry and rediscovers all configured MCP servers.
"""
from ..plugin_system import BuiltinCommand, BuiltinCommandRegistry
from ..tools.mcp_registry import get_mcp_registry
from ..tools.mcp_server_manager import MCPServerManager
from ..tools.mcp_client import create_mcp_tools
from ..tools.base import ToolRegistry
from ..utils import is_debug_enabled


class RestartMcpCommand(BuiltinCommand):
    """Plugin for the 'restart-mcp' command to reload MCP servers"""
    
    # Plugin attributes
    plugin_name = "restart_mcp_command"
    is_required = False  # Optional plugin, enabled by default
    is_enabled = True  # Enabled by default
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        command_lower = command.lower().strip()
        return command_lower == "restart-mcp" or command_lower == "reload-mcp"
    
    def execute(self, command):
        """Reload MCP server registry and rediscover all servers"""
        print("Reloading MCP server configuration...")
        
        try:
            # Get the registry and reload it
            mcp_registry = get_mcp_registry()
            mcp_registry.reload()
            
            enabled_servers = mcp_registry.get_enabled_servers()
            
            if not enabled_servers:
                print("No MCP servers configured or enabled")
                return True
            
            print(f"Discovering {len(enabled_servers)} enabled MCP servers...")
            
            # Unregister existing MCP tools
            self._unregister_mcp_tools()
            
            # Discover all servers
            mcp_manager = MCPServerManager()
            running_servers = mcp_manager.discover_all_servers()
            
            if not running_servers:
                print("No MCP servers discovered successfully")
                return True
            
            # Register tools for each running MCP server
            total_tools = 0
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
                    
                    total_tools += len(mcp_tools)
                    print(f"Registered {len(mcp_tools)} tools from MCP server '{server_config.name}'")
                    
                except Exception as e:
                    print(f"Warning: Failed to register tools for MCP server '{server_config.name}': {e}")
            
            print(f"\nMCP reload complete: {len(running_servers)} servers, {total_tools} tools registered")
            return True
            
        except Exception as e:
            print(f"Error reloading MCP servers: {e}")
            if is_debug_enabled():
                import traceback
                traceback.print_exc()
            return True
    
    def _unregister_mcp_tools(self):
        """Remove all existing MCP tools from the registry"""
        # Get all registered tools
        all_tools = list(ToolRegistry._tools.keys())
        
        # Find MCP tools (they have prefixes from MCP servers)
        # We'll identify them by checking if they're MCPProxyTool instances
        mcp_tool_names = []
        for tool_name in all_tools:
            tool = ToolRegistry._tools[tool_name]
            # Check if it's an MCP proxy tool by checking its class name
            if tool.__class__.__name__ == 'MCPProxyTool':
                mcp_tool_names.append(tool_name)
        
        # Unregister all MCP tools
        for tool_name in mcp_tool_names:
            del ToolRegistry._tools[tool_name]
        
        if is_debug_enabled() and mcp_tool_names:
            print(f"Unregistered {len(mcp_tool_names)} existing MCP tools")


# Register the plugin with the registry
BuiltinCommandRegistry.register(RestartMcpCommand())
