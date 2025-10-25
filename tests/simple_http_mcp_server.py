#!/usr/bin/env python3
"""
Simple HTTP MCP Server for testing URL-based MCP connections

This server implements a basic MCP server over HTTP that provides
a few simple tools for testing purposes.

Usage:
    python simple_http_mcp_server.py [--port PORT]

Default port: 8080
"""

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any


class MCPHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for MCP JSON-RPC requests"""
    
    def log_message(self, format, *args):
        """Override to provide cleaner logging"""
        sys.stderr.write(f"[HTTP MCP Server] {format % args}\n")
    
    def do_POST(self):
        """Handle POST requests with JSON-RPC"""
        try:
            # Read the request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # Parse JSON-RPC request
            request = json.loads(body.decode('utf-8'))
            
            # Log the request
            self.log_message(f"Received request: {request.get('method')}")
            
            # Process the request
            response = self.process_jsonrpc(request)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.log_message(f"Error processing request: {e}")
            self.send_error(500, str(e))
    
    def do_HEAD(self):
        """Handle HEAD requests for connectivity checks"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests - return server info"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        info = {
            "server": "Simple HTTP MCP Server",
            "version": "1.0",
            "status": "running"
        }
        self.wfile.write(json.dumps(info).encode('utf-8'))
    
    def process_jsonrpc(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process JSON-RPC request and return response"""
        request_id = request.get('id')
        method = request.get('method')
        params = request.get('params', {})
        
        try:
            if method == 'tools/list':
                result = self.handle_tools_list()
            elif method == 'tools/call':
                result = self.handle_tools_call(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            }
    
    def handle_tools_list(self) -> Dict[str, Any]:
        """Return list of available tools"""
        return {
            "tools": [
                {
                    "name": "greet",
                    "description": "Generate a greeting message",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the person to greet"
                            }
                        },
                        "required": ["name"]
                    }
                },
                {
                    "name": "calculate",
                    "description": "Perform basic arithmetic calculation",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "description": "Operation to perform (add, subtract, multiply, divide)",
                                "enum": ["add", "subtract", "multiply", "divide"]
                            },
                            "a": {
                                "type": "number",
                                "description": "First number"
                            },
                            "b": {
                                "type": "number",
                                "description": "Second number"
                            }
                        },
                        "required": ["operation", "a", "b"]
                    }
                },
                {
                    "name": "reverse",
                    "description": "Reverse a string",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to reverse"
                            }
                        },
                        "required": ["text"]
                    }
                }
            ]
        }
    
    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return the result"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if tool_name == 'greet':
            name = arguments.get('name', 'World')
            result_text = f"Hello, {name}! Welcome to the HTTP MCP Server."
            
        elif tool_name == 'calculate':
            operation = arguments.get('operation')
            a = float(arguments.get('a', 0))
            b = float(arguments.get('b', 0))
            
            if operation == 'add':
                result = a + b
            elif operation == 'subtract':
                result = a - b
            elif operation == 'multiply':
                result = a * b
            elif operation == 'divide':
                if b == 0:
                    result_text = "Error: Division by zero"
                else:
                    result = a / b
                    result_text = f"{a} {operation} {b} = {result}"
            else:
                result_text = f"Unknown operation: {operation}"
            
            if 'result' in locals():
                result_text = f"{a} {operation} {b} = {result}"
                
        elif tool_name == 'reverse':
            text = arguments.get('text', '')
            result_text = text[::-1]
            
        else:
            raise Exception(f"Unknown tool: {tool_name}")
        
        # Return in MCP format with content array
        return {
            "content": [
                {
                    "type": "text",
                    "text": result_text
                }
            ]
        }


def main():
    """Start the HTTP MCP server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple HTTP MCP Server')
    parser.add_argument('--port', type=int, default=8080,
                        help='Port to listen on (default: 8080)')
    parser.add_argument('--host', default='localhost',
                        help='Host to bind to (default: localhost)')
    args = parser.parse_args()
    
    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, MCPHTTPHandler)
    
    print(f"Starting HTTP MCP Server on http://{args.host}:{args.port}")
    print("Available tools: greet, calculate, reverse")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()


if __name__ == '__main__':
    main()
