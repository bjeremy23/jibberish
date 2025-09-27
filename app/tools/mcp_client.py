"""
MCP Client for communicating with MCP servers in Docker containers
Handles JSON-RPC communication and tool discovery
"""

import subprocess
import json
import uuid
import threading
import time
from typing import Dict, Any, Optional, List
from queue import Queue, Empty
from .base import Tool
from ..utils import is_debug_enabled


class MCPClient:
    """Client for communicating with MCP servers via Docker exec"""
    
    def __init__(self, container_id: str):
        self.container_id = container_id
        self.request_id_counter = 0
        self.pending_requests = {}
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
        Send JSON-RPC request to MCP server via docker exec
        
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
        
        try:
            # Send JSON-RPC request to MCP server via stdin
            request_json = json.dumps(request) + "\n"
            
            if is_debug_enabled():
                print(f"[MCP DEBUG] Sending request: {request_json.strip()}")
            
            # Execute the MCP server directly and send JSON-RPC via stdin
            process = subprocess.Popen([
                "docker", "exec", "-i", self.container_id, 
                "/usr/local/bin/mcp-kubernetes", "--transport", "stdio", "--access-level", "readwrite"
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
               stderr=subprocess.PIPE, text=True)
            
            # Send the request and get response
            stdout, stderr = process.communicate(input=request_json, timeout=30)
            
            if is_debug_enabled():
                print(f"[MCP DEBUG] Response stdout: {stdout}")
                print(f"[MCP DEBUG] Response stderr: {stderr}")
            
            if process.returncode != 0:
                raise Exception(f"MCP server error (code {process.returncode}): {stderr}")
            
            # Parse response - MCP server may send multiple JSON objects
            response_lines = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
            
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
            # If MCP call fails, fall back to direct kubectl execution for backwards compatibility
            if is_debug_enabled():
                print(f"[MCP DEBUG] MCP call failed, falling back to direct execution: {e}")
            
            return self._fallback_kubectl_execution(tool_name, arguments)
    
    def _fallback_kubectl_execution(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Fallback method that directly executes kubectl commands if MCP JSON-RPC fails
        This maintains backwards compatibility with the previous implementation
        """
        try:
            if tool_name == "kubectl_cluster_resources":
                operation = arguments.get("operation", "get")
                resource = arguments.get("resource", "")
                args = arguments.get("args", "")
                
                cmd_args = ["kubectl", operation, resource] + (args.split() if args else [])
                cmd_args = [arg for arg in cmd_args if arg]  # Remove empty strings
                
                result = subprocess.run([
                    "docker", "exec", self.container_id
                ] + cmd_args, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    output = result.stdout.strip() or result.stderr.strip() or "Command executed successfully but returned no output"
                    
                    # Add namespace context to help AI understand what namespace the results are from
                    namespace_context = ""
                    if "-n " in args or "--namespace " in args:
                        import re
                        ns_match = re.search(r'-n\s+(\S+)|--namespace\s+(\S+)', args)
                        if ns_match:
                            namespace = ns_match.group(1) or ns_match.group(2)
                            namespace_context = f"Kubectl {operation} {resource} results from namespace '{namespace}':\n\n"
                    elif operation == "get" and not any(ns_flag in args for ns_flag in ["-n", "--namespace", "--all-namespaces", "-A"]):
                        namespace_context = f"Kubectl {operation} {resource} results from default namespace:\n\n"
                    
                    return namespace_context + output
                else:
                    return f"Error: {result.stderr}"
                    
            elif tool_name == "kubectl_cluster_diagnostics":
                operation = arguments.get("operation", "logs")
                resource = arguments.get("resource", "")
                args = arguments.get("args", "")
                
                if operation == "logs":
                    cmd_args = ["kubectl", "logs"] + (args.split() if args else [])
                elif operation == "events":
                    cmd_args = ["kubectl", "get", "events"] + (args.split() if args else [])
                elif operation == "top":
                    cmd_args = ["kubectl", "top", resource] + (args.split() if args else [])
                else:
                    cmd_args = ["kubectl", operation] + (args.split() if args else [])
                
                cmd_args = [arg for arg in cmd_args if arg]  # Remove empty strings
                
                result = subprocess.run([
                    "docker", "exec", self.container_id
                ] + cmd_args, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    output = result.stdout.strip() or result.stderr.strip() or "Command executed successfully but returned no output"
                    
                    # Add context about what the diagnostic command was
                    context_prefix = f"Kubectl {operation}"
                    if resource:
                        context_prefix += f" {resource}"
                    if "-n " in args or "--namespace " in args:
                        import re
                        ns_match = re.search(r'-n\s+(\S+)|--namespace\s+(\S+)', args)
                        if ns_match:
                            namespace = ns_match.group(1) or ns_match.group(2)
                            context_prefix += f" from namespace '{namespace}'"
                    context_prefix += " results:\n\n"
                    
                    return context_prefix + output
                else:
                    return f"Error: {result.stderr}"
                    
            elif tool_name == "kubectl_cluster_info":
                operation = arguments.get("operation", "cluster-info")
                resource = arguments.get("resource", "")
                args = arguments.get("args", "")
                
                if operation == "cluster-info":
                    if resource == "dump":
                        cmd_args = ["kubectl", "cluster-info", "dump"]
                    else:
                        cmd_args = ["kubectl", "cluster-info"]
                elif operation == "api-resources":
                    cmd_args = ["kubectl", "api-resources"] + (args.split() if args else [])
                elif operation == "explain":
                    cmd_args = ["kubectl", "explain", resource] + (args.split() if args else [])
                else:
                    cmd_args = ["kubectl", operation] + (args.split() if args else [])
                
                cmd_args = [arg for arg in cmd_args if arg]  # Remove empty strings
                
                result = subprocess.run([
                    "docker", "exec", self.container_id
                ] + cmd_args, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    return result.stdout.strip() or result.stderr.strip() or "Command executed successfully but returned no output"
                else:
                    return f"Error: {result.stderr}"
            
            return f"Tool {tool_name} not implemented in fallback mode"
                
        except Exception as e:
            return f"Error calling tool {tool_name} (fallback): {e}"
    
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


class MCPKubernetesProxyTool(Tool):
    """Proxy tool that forwards requests to MCP Kubernetes server"""
    
    def __init__(self, mcp_tool_name: str, mcp_tool_spec: Dict[str, Any], mcp_client: MCPClient):
        self.mcp_tool_name = mcp_tool_name
        self.mcp_tool_spec = mcp_tool_spec
        self.mcp_client = mcp_client
    
    @property
    def name(self) -> str:
        return f"k8s_{self.mcp_tool_name.replace('-', '_').replace('.', '_')}"
    
    @property 
    def description(self) -> str:
        base_description = self.mcp_tool_spec.get("description", f"Kubernetes tool: {self.mcp_tool_name}")
        return f"MCP Kubernetes: {base_description}"
    
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


def create_mcp_kubernetes_tools(container_id: str) -> List[MCPKubernetesProxyTool]:
    """
    Create proxy tools for all available MCP Kubernetes tools
    
    Args:
        container_id: Docker container ID of running MCP server
        
    Returns:
        List of proxy tools
    """
    try:
        client = MCPClient(container_id)
        available_tools = client.list_tools()
        
        proxy_tools = []
        for tool_name, tool_spec in available_tools.items():
            proxy_tool = MCPKubernetesProxyTool(tool_name, tool_spec, client)
            proxy_tools.append(proxy_tool)
        
        if is_debug_enabled():
            print(f"Created {len(proxy_tools)} MCP Kubernetes proxy tools")
        return proxy_tools
        
    except Exception as e:
        print(f"Error creating MCP tools: {e}")
        return []