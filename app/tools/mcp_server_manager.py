"""
MCP Server Manager for spawning and connecting to MCP servers
Supports Docker run commands, local processes, and URL-based connections
"""

import subprocess
import json
import os
import requests
from typing import Dict, Any, Optional, List
from .mcp_registry import get_mcp_registry, MCPServerConfig


class MCPServerManager:
    """Discovers and connects to existing MCP servers"""
    
    def __init__(self):
        self.registry = get_mcp_registry()
        self.discovered_servers = {}  # Track discovered servers by server name
    
    def discover_all_servers(self) -> List[Dict[str, Any]]:
        """
        Discover all enabled MCP servers
        
        Returns:
            List of dictionaries with server info
        """
        all_servers = []
        
        for server_config in self.registry.get_enabled_servers():
            try:
                if not server_config.command:
                    print(f"Warning: Server '{server_config.name}' has no command specified, skipping")
                    continue
                
                server_info = self.discover_server(server_config)
                if server_info:
                    all_servers.append(server_info)
                    self.discovered_servers[server_config.name] = server_info
            except Exception as e:
                print(f"Failed to discover MCP server '{server_config.name}': {e}")
        
        print(f"Discovered {len(all_servers)} MCP servers")
        return all_servers
    
    def discover_server(self, server_config: MCPServerConfig) -> Optional[Dict[str, Any]]:
        """
        Discover a single MCP server (check if it exists and is accessible)
        
        Args:
            server_config: Server configuration
            
        Returns:
            Server info dictionary or None
        """
        conn_type = server_config.get_connection_type()
        
        print(f"Discovering MCP server '{server_config.name}' (type: {conn_type})")
        
        if conn_type == 'url':
            return self._discover_url_server(server_config)
        elif conn_type == 'docker':
            return self._discover_docker_server(server_config)
        elif conn_type == 'local':
            return self._discover_local_server(server_config)
        else:
            print(f"Unknown connection type for server '{server_config.name}'")
            return None
    
    def _discover_url_server(self, server_config: MCPServerConfig) -> Optional[Dict[str, Any]]:
        """
        Discover URL-based MCP server (check if accessible)
        
        Args:
            server_config: Server configuration
            
        Returns:
            Server info dictionary or None
        """
        url = server_config.command
        
        try:
            # Quick connectivity check
            response = requests.head(url, timeout=5)
            # Any response (including errors) means server exists
            print(f"URL server '{server_config.name}' is accessible at {url}")
        except Exception as e:
            print(f"Warning: Could not connect to URL server '{server_config.name}' at {url}: {e}")
            print(f"Will still attempt to use it for tool calls")
        
        # Return connection info regardless of connectivity check
        # The actual tool calls will fail if server is truly unavailable
        return {
            'connection_type': 'url',
            'name': server_config.name,
            'url': url,
            'server_config': server_config,
            'process': None
        }
    
    def _discover_docker_server(self, server_config: MCPServerConfig) -> Optional[Dict[str, Any]]:
        """
        Discover Docker-based MCP server
        
        Args:
            server_config: Server configuration
            
        Returns:
            Server info dictionary or None
        """
        try:
            # Build the command that will be used per-request
            cmd = [server_config.command] + server_config.args
            
            # Prepare environment
            env = os.environ.copy()
            if server_config.env:
                env.update(server_config.env)
            
            # For Docker containers, we'll run them per-request
            # The command should include "docker run" with appropriate flags
            print(f"Docker MCP server '{server_config.name}' configured: {' '.join(cmd[:4])}...")
            
            return {
                'connection_type': 'docker',
                'name': server_config.name,
                'command': cmd,
                'env': env,
                'server_config': server_config,
                'process': None  # Will be spawned per-request
            }
            
        except Exception as e:
            print(f"Error configuring Docker MCP server '{server_config.name}': {e}")
            return None
    
    def _discover_local_server(self, server_config: MCPServerConfig) -> Optional[Dict[str, Any]]:
        """
        Discover local executable MCP server
        
        Args:
            server_config: Server configuration
            
        Returns:
            Server info dictionary or None
        """
        try:
            # Build the command that will be used per-request
            cmd = [server_config.command] + server_config.args
            
            # Prepare environment
            env = os.environ.copy()
            if server_config.env:
                env.update(server_config.env)
            
            # For local executables, we'll run them per-request
            print(f"Local MCP server '{server_config.name}' configured: {' '.join(cmd)}")
            
            return {
                'connection_type': 'local',
                'name': server_config.name,
                'command': cmd,
                'env': env,
                'server_config': server_config,
                'process': None  # Will be spawned per-request
            }
            
        except Exception as e:
            print(f"Error configuring local MCP server '{server_config.name}': {e}")
            return None
    
    def stop_all_servers(self):
        """No-op: We don't manage server processes, they run independently"""
        pass
    
    def __del__(self):
        """Cleanup on destruction"""
        # No cleanup needed - we don't spawn processes
        pass


# Backwards compatibility alias
MCPContainerManager = MCPServerManager
