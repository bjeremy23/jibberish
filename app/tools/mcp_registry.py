"""
MCP Server Registry - Manages multiple MCP server configurations
Loads from .jbrsh configuration and provides discovery/management methods
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server"""
    name: str
    enabled: bool
    command: str = ''  # Command to execute (docker, local binary path, or URL)
    args: List[str] = None  # Arguments to pass to the command
    env: Dict[str, str] = None  # Environment variables
    description: str = ''
    tool_prefix: str = ''
    
    def __post_init__(self):
        # Initialize args as empty list if None
        if self.args is None:
            self.args = []
        # Initialize env as empty dict if None
        if self.env is None:
            self.env = {}
    
    def is_url(self) -> bool:
        """Check if this is a URL-based connection"""
        return self.command.startswith('http://') or self.command.startswith('https://')
    
    def is_docker(self) -> bool:
        """Check if this uses docker"""
        return self.command == 'docker' or 'docker' in self.command.lower()
    
    def get_connection_type(self) -> str:
        """Determine connection type: 'url', 'docker', or 'local'"""
        if self.is_url():
            return 'url'
        elif self.is_docker():
            return 'docker'
        else:
            return 'local'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'command': self.command,
            'args': self.args,
            'env': self.env,
            'description': self.description,
            'tool_prefix': self.tool_prefix
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPServerConfig':
        """Create from dictionary"""
        name = data.get('name', '')
        
        return cls(
            name=name,
            enabled=data.get('enabled', True),
            command=data.get('command', ''),
            args=data.get('args', []),
            env=data.get('env', {}),
            description=data.get('description', ''),
            tool_prefix=data.get('tool_prefix', name if name else 'mcp')
        )


class MCPServerRegistry:
    """Registry for managing multiple MCP server configurations"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerConfig] = {}
        self._load_from_config()
    
    def _load_from_config(self):
        """Load MCP server configurations from ~/.jbrsh-mcp-servers.json or .jbrsh file"""
        try:
            # First, try to load from separate JSON file (easier to edit)
            mcp_json_path = os.path.expanduser('~/.jbrsh-mcp-servers.json')
            
            if os.path.exists(mcp_json_path):
                try:
                    with open(mcp_json_path, 'r') as f:
                        mcp_servers_config = json.load(f)
                    self._parse_servers_config(mcp_servers_config)
                    return
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse {mcp_json_path}: {e}")
                    print("Falling back to .jbrsh file...")
            
            # Fall back to loading from ~/.jbrsh file
            jbrsh_path = os.path.expanduser('~/.jbrsh')
            
            if not os.path.exists(jbrsh_path):
                print("Warning: Neither ~/.jbrsh-mcp-servers.json nor ~/.jbrsh file found. No MCP servers configured.")
                return
            
            # Read the file and look for MCP_SERVERS configuration
            with open(jbrsh_path, 'r') as f:
                content = f.read()
            
            # Extract MCP_SERVERS JSON configuration
            mcp_servers_config = None
            
            # Look for MCP_SERVERS='...' or MCP_SERVERS="..."
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('MCP_SERVERS='):
                    # Extract the JSON content
                    config_str = line.split('=', 1)[1].strip()
                    
                    # Remove surrounding quotes if present
                    if config_str.startswith("'") and config_str.endswith("'"):
                        config_str = config_str[1:-1]
                    elif config_str.startswith('"') and config_str.endswith('"'):
                        config_str = config_str[1:-1]
                    
                    # For multi-line JSON, we need to read until we find the closing bracket
                    if not config_str.endswith(']'):
                        # Continue reading lines
                        lines_iter = iter(content.split('\n'))
                        # Skip to the MCP_SERVERS line
                        for l in lines_iter:
                            if l.strip().startswith('MCP_SERVERS='):
                                break
                        
                        # Now read the rest
                        full_config = config_str
                        for l in lines_iter:
                            full_config += '\n' + l
                            if l.strip().endswith("'") or l.strip().endswith('"'):
                                # Remove trailing quote
                                full_config = full_config.rstrip("'\"")
                                break
                        config_str = full_config
                    
                    try:
                        mcp_servers_config = json.loads(config_str)
                        break
                    except json.JSONDecodeError as e:
                        print(f"Warning: Failed to parse MCP_SERVERS JSON: {e}")
                        print(f"Config string was: {config_str[:200]}...")
                        return
            
            if mcp_servers_config is None:
                print("Info: No MCP_SERVERS configuration found in ~/.jbrsh")
                return
            
            self._parse_servers_config(mcp_servers_config)
            
        except Exception as e:
            print(f"Warning: Failed to load MCP server configurations: {e}")
    
    def _parse_servers_config(self, mcp_servers_config: Any):
        """Parse and load server configurations from JSON data"""
        try:
            # Parse servers - can be either object (new format) or array (old format)
            if isinstance(mcp_servers_config, dict):
                # New format: {"server_name": {config}, ...}
                for server_name, server_data in mcp_servers_config.items():
                    try:
                        # Add name if not present
                        if 'name' not in server_data:
                            server_data['name'] = server_name
                        
                        server_config = MCPServerConfig.from_dict(server_data)
                        self.servers[server_config.name] = server_config
                    except Exception as e:
                        print(f"Warning: Failed to parse MCP server config for '{server_name}': {e}")
                        
            elif isinstance(mcp_servers_config, list):
                # Old format: [{config}, {config}, ...]
                for server_data in mcp_servers_config:
                    try:
                        server_config = MCPServerConfig.from_dict(server_data)
                        self.servers[server_config.name] = server_config
                    except Exception as e:
                        print(f"Warning: Failed to parse MCP server config: {e}")
            else:
                print("Warning: MCP_SERVERS must be a JSON object or array")
            
            # Log loaded servers
            enabled_count = sum(1 for s in self.servers.values() if s.enabled)
            print(f"Loaded {len(self.servers)} MCP server configurations ({enabled_count} enabled)")
            
        except Exception as e:
            print(f"Warning: Failed to parse MCP server configurations: {e}")
    
    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get server configuration by name"""
        return self.servers.get(name)
    
    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """Get list of enabled server configurations"""
        return [server for server in self.servers.values() if server.enabled]
    
    def get_all_servers(self) -> List[MCPServerConfig]:
        """Get list of all server configurations"""
        return list(self.servers.values())
    
    def is_server_enabled(self, name: str) -> bool:
        """Check if a server is enabled"""
        server = self.servers.get(name)
        return server.enabled if server else False
    
    def get_server_by_container(self, container_name: str, container_image: str) -> Optional[MCPServerConfig]:
        """
        Deprecated: Find which MCP server config matches a container
        This method is no longer used since we spawn containers directly
        """
        return None
    
    def add_server(self, server_config: MCPServerConfig):
        """Add or update a server configuration"""
        self.servers[server_config.name] = server_config
    
    def remove_server(self, name: str):
        """Remove a server configuration"""
        if name in self.servers:
            del self.servers[name]
    
    def reload(self):
        """Reload configurations from .jbrsh file"""
        self.servers.clear()
        self._load_from_config()


# Global registry instance
_registry_instance = None


def get_mcp_registry() -> MCPServerRegistry:
    """Get the global MCP server registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = MCPServerRegistry()
    return _registry_instance
