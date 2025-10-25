"""
MCP Client for communicating with MCP servers
Handles JSON-RPC communication via subprocess (Docker/local) or HTTP (URL)
"""

import subprocess
import json
import requests
from typing import Dict, Any, Optional, List
from .base import Tool
from .mcp_registry import MCPServerConfig
from ..utils import is_debug_enabled


class MCPClient:
    """Client for communicating with MCP servers via subprocess or HTTP"""
    
    def __init__(self, server_info: Dict[str, Any], server_config: MCPServerConfig):
        """
        Initialize MCP client
        
        Args:
            server_info: Server information dict (contains connection_type, command, url, etc.)
            server_config: MCP server configuration
        """
        self.server_info = server_info
        self.server_config = server_config
        self.connection_type = server_info.get('connection_type', 'local')
        self.request_id_counter = 0
        self.available_tools = {}
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize connection and discover available tools"""
        try:
            # First, list available tools
            self._discover_tools()
        except Exception as e:
            print(f"Warning: Failed to initialize MCP connection: {e}")
            
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        self.request_id_counter += 1
        return str(self.request_id_counter)
    
    def _send_jsonrpc_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send JSON-RPC request to MCP server
        
        Args:
            method: JSON-RPC method name
            params: Method parameters
            
        Returns:
            Response dictionary
        """
        request_id = self._generate_request_id()
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        if self.connection_type == 'url':
            return self._send_http_request(request)
        else:
            return self._send_subprocess_request(request)
    
    def _send_http_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request via HTTP"""
        try:
            url = self.server_info.get('url')
            
            if is_debug_enabled():
                print(f"[MCP DEBUG] Sending HTTP request to {url}: {json.dumps(request)}")
            
            response = requests.post(
                url,
                json=request,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if is_debug_enabled():
                print(f"[MCP DEBUG] HTTP Response: {json.dumps(result)}")
            
            if "error" in result:
                raise Exception(f"MCP server error: {result['error']}")
            
            return result.get("result", {})
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"MCP HTTP communication failed: {e}")
        except Exception as e:
            raise Exception(f"MCP communication failed: {e}")
    
    def _send_subprocess_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request via subprocess (Docker or local)"""
        try:
            # Send JSON-RPC request to MCP server via stdin
            request_json = json.dumps(request) + "\n"
            
            if is_debug_enabled():
                print(f"[MCP DEBUG] Sending subprocess request: {request_json.strip()}")
            
            # Get command from server_info
            cmd = self.server_info.get('command', [])
            env = self.server_info.get('env', {})
            
            if not cmd:
                raise Exception("No command specified for MCP server")
            
            if is_debug_enabled():
                print(f"[MCP DEBUG] Executing command: {' '.join(cmd)}")
            
            # Execute the MCP server
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, 
                text=True,
                env=env if env else None
            )
            
            # Send the request and get response
            stdout, stderr = process.communicate(input=request_json, timeout=30)
            
            if is_debug_enabled():
                print(f"[MCP DEBUG] Response stdout: {stdout}")
                print(f"[MCP DEBUG] Response stderr: {stderr}")
            
            if process.returncode != 0:
                raise Exception(f"MCP server error (code {process.returncode}): {stderr}")
            
            # Parse response - MCP server may send multiple JSON objects
            response_lines = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
            
            request_id = request.get("id")
            
            for line in response_lines:
                try:
                    response = json.loads(line)
                    # Look for response with matching ID
                    if response.get("id") == request_id:
                        if "error" in response:
                            raise Exception(f"MCP server error: {response['error']}")
                        return response.get("result", {})
                except json.JSONDecodeError:
                    if is_debug_enabled():
                        print(f"[MCP DEBUG] Failed to parse line as JSON: {line}")
                    continue
            
            # If no matching response found, try to return the first valid JSON response
            for line in response_lines:
                try:
                    response = json.loads(line)
                    if "result" in response:
                        return response.get("result", {})
                except json.JSONDecodeError:
                    continue
                    
            raise Exception("No valid JSON-RPC response received from MCP server")
            
        except subprocess.TimeoutExpired:
            raise Exception("MCP request timeout")
        except Exception as e:
            raise Exception(f"MCP communication failed: {e}")
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on the MCP server
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result as string
        """
        if tool_name not in self.available_tools:
            return f"Error: Tool '{tool_name}' not available"
        
        try:
            # Debug: Log the actual arguments being passed
            if is_debug_enabled():
                print(f"[MCP DEBUG] Tool: {tool_name}")
                print(f"[MCP DEBUG] Arguments: {arguments}")
            
            # Call the tool via JSON-RPC
            result = self._send_jsonrpc_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
            # Extract the tool result from the MCP response
            if isinstance(result, dict):
                # MCP tool responses typically have content with text
                if "content" in result:
                    content = result["content"]
                    if isinstance(content, list) and len(content) > 0:
                        # Get the first content item
                        first_content = content[0]
                        if isinstance(first_content, dict) and "text" in first_content:
                            tool_output = first_content["text"]
                        else:
                            tool_output = str(first_content)
                    else:
                        tool_output = str(content)
                elif "text" in result:
                    tool_output = result["text"]
                else:
                    tool_output = str(result)
            else:
                tool_output = str(result)
            
            if is_debug_enabled():
                print(f"[MCP DEBUG] Tool result length: {len(tool_output)}")
                print(f"[MCP DEBUG] Tool result first 300 chars: {repr(tool_output[:300])}")
                
            return tool_output
                
        except Exception as e:
            return f"Error calling MCP tool '{tool_name}': {e}"
    
    def _discover_tools(self):
        """Discover available tools from the MCP server"""
        try:
            # Send tools/list request to discover available tools
            result = self._send_jsonrpc_request("tools/list")
            
            if "tools" in result:
                for tool in result["tools"]:
                    tool_name = tool.get("name")
                    if tool_name:
                        self.available_tools[tool_name] = {
                            "name": tool_name,
                            "description": tool.get("description", ""),
                            "inputSchema": tool.get("inputSchema", {}),
                            "spec": tool
                        }
                        
            if is_debug_enabled():
                print(f"Discovered {len(self.available_tools)} MCP tools")
            
        except Exception as e:
            print(f"Warning: Could not discover MCP tools: {e}")
            # Continue without tools rather than failing
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available tools"""
        return self.available_tools.copy()


class MCPProxyTool(Tool):
    """Proxy tool that forwards requests to any MCP server"""
    
    def __init__(self, mcp_tool_name: str, mcp_tool_spec: Dict[str, Any], mcp_client: MCPClient):
        self.mcp_tool_name = mcp_tool_name
        self.mcp_tool_spec = mcp_tool_spec
        self.mcp_client = mcp_client
    
    @property
    def name(self) -> str:
        # Use the server's tool prefix to create unique tool names
        prefix = self.mcp_client.server_config.tool_prefix
        tool_name = self.mcp_tool_name.replace('-', '_').replace('.', '_')
        return f"{prefix}_{tool_name}"
    
    @property 
    def description(self) -> str:
        base_description = self.mcp_tool_spec.get("description", f"{self.mcp_client.server_config.name} tool: {self.mcp_tool_name}")
        server_name = self.mcp_client.server_config.name.title()
        return f"MCP {server_name}: {base_description}"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        # Convert MCP input schema to Jibberish tool parameter format
        input_schema = self.mcp_tool_spec.get("inputSchema", {})
        return {
            "type": "object",
            "properties": input_schema.get("properties", {}),
            "required": input_schema.get("required", [])
        }
    
    def execute(self, **kwargs) -> str:
        """Execute the MCP tool with provided arguments"""
        return self.mcp_client.call_tool(self.mcp_tool_name, kwargs)


def create_mcp_tools(server_info: Dict[str, Any], server_config: MCPServerConfig) -> List[MCPProxyTool]:
    """
    Create proxy tools for all available MCP server tools
    
    Args:
        server_info: Server information dict (contains connection_type, container_id or full_command, etc.)
        server_config: MCP server configuration
        
    Returns:
        List of proxy tools
    """
    try:
        client = MCPClient(server_info, server_config)
        available_tools = client.list_tools()
        
        proxy_tools = []
        for tool_name, tool_spec in available_tools.items():
            proxy_tool = MCPProxyTool(tool_name, tool_spec, client)
            proxy_tools.append(proxy_tool)
        
        if is_debug_enabled():
            print(f"Created {len(proxy_tools)} MCP {server_config.name} proxy tools")
        return proxy_tools
        
    except Exception as e:
        print(f"Error creating MCP tools for {server_config.name}: {e}")
        return []


# Backwards compatibility alias
def create_mcp_kubernetes_tools(container_id: str) -> List[MCPProxyTool]:
    """
    Deprecated: Create proxy tools for MCP Kubernetes server
    This function is kept for backwards compatibility but is no longer used
    """
    print("Warning: create_mcp_kubernetes_tools is deprecated")
    return []