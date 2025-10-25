#!/usr/bin/env python3
"""
Simple MCP Server for testing
Provides basic tools via stdio JSON-RPC
"""

import json
import sys


def send_response(request_id, result):
    """Send JSON-RPC response"""
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }
    print(json.dumps(response), flush=True)


def handle_tools_list(request_id):
    """Handle tools/list request"""
    result = {
        "tools": [
            {
                "name": "repeat",
                "description": "Echo back the input message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo back"
                        }
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "add",
                "description": "Add two numbers together",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "First number"
                        },
                        "b": {
                            "type": "number",
                            "description": "Second number"
                        }
                    },
                    "required": ["a", "b"]
                }
            }
        ]
    }
    send_response(request_id, result)


def handle_tools_call(request_id, params):
    """Handle tools/call request"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if tool_name == "repeat":
        message = arguments.get("message", "")
        result = {
            "content": [
                {
                    "type": "text",
                    "text": f"Echo: {message}"
                }
            ]
        }
        send_response(request_id, result)
    
    elif tool_name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        sum_result = a + b
        result = {
            "content": [
                {
                    "type": "text",
                    "text": f"{a} + {b} = {sum_result}"
                }
            ]
        }
        send_response(request_id, result)
    
    else:
        # Unknown tool
        error_response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Unknown tool: {tool_name}"
            }
        }
        print(json.dumps(error_response), flush=True)


def main():
    """Main server loop - read JSON-RPC requests from stdin"""
    # Read line by line from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})
            
            if method == "tools/list":
                handle_tools_list(request_id)
            elif method == "tools/call":
                handle_tools_call(request_id, params)
            else:
                # Unknown method
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                print(json.dumps(error_response), flush=True)
                
        except json.JSONDecodeError as e:
            # Invalid JSON
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {e}"
                }
            }
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            # Other errors
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {e}"
                }
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
