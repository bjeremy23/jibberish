"""
Base classes for the jibberish tool system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import re

class Tool(ABC):
    """
    Abstract base class for all tools in the jibberish system.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool as it should be referenced by the AI."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the tool does for the AI to understand when to use it."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """
        JSON schema describing the parameters this tool accepts.
        Should follow OpenAI function calling format.
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        Execute the tool with the given parameters.
        Returns a string result that will be added to the AI context.
        """
        pass
    
    def to_function_definition(self) -> Dict[str, Any]:
        """
        Convert this tool to an OpenAI function definition format.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class ToolRegistry:
    """
    Registry for managing available tools.
    """
    
    _tools: Dict[str, Tool] = {}
    
    @classmethod
    def register(cls, tool: Tool):
        """Register a tool in the registry."""
        cls._tools[tool.name] = tool
    
    @classmethod
    def get_tool(cls, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return cls._tools.get(name)
    
    @classmethod
    def get_all_tools(cls) -> Dict[str, Tool]:
        """Get all registered tools."""
        return cls._tools.copy()
    
    @classmethod
    def get_function_definitions(cls) -> List[Dict[str, Any]]:
        """Get all tools as OpenAI function definitions."""
        return [tool.to_function_definition() for tool in cls._tools.values()]


class ToolCallParser:
    """
    Parser for extracting tool calls from AI responses.
    """
    
    @staticmethod
    def extract_tool_calls(response: str) -> List[Dict[str, Any]]:
        """
        Extract tool calls from an AI response.
        
        Looks for JSON format tool calls in code blocks:
        ```json
        {
          "tool_calls": [
            {"name": "tool_name", "arguments": {"param": "value"}}
          ]
        }
        ```
        
        Returns a list of tool calls with name and arguments.
        """
        tool_calls = []
        
        # Primary pattern: JSON format in code blocks (this handles 99% of cases now)
        json_pattern = r'```json\s*\n(.*?)\n\s*```'
        matches = re.finditer(json_pattern, response, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            json_str = match.group(1).strip()
            try:
                data = json.loads(json_str)
                if isinstance(data, dict) and 'tool_calls' in data:
                    for tool_call in data['tool_calls']:
                        if isinstance(tool_call, dict) and 'name' in tool_call:
                            # Handle parameter name variations for backward compatibility
                            args = tool_call.get('arguments', {})
                            if tool_call['name'] == 'write_file':
                                if 'path' in args:
                                    args['filepath'] = args.pop('path')
                                if 'file_path' in args:
                                    args['filepath'] = args.pop('file_path')
                            
                            tool_calls.append({
                                "name": tool_call['name'],
                                "arguments": args
                            })
            except json.JSONDecodeError:
                continue
        
        # Simple fallback: TOOL_CALL: tool_name with JSON (minimal legacy support)
        if not tool_calls:
            pattern = r'TOOL_CALL:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\n\s*({.*?})'
            matches = re.finditer(pattern, response, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                tool_name = match.group(1)
                try:
                    params = json.loads(match.group(2))
                    # Handle parameter name variations
                    if tool_name == 'write_file':
                        if 'path' in params:
                            params['filepath'] = params.pop('path')
                        if 'file_path' in params:
                            params['filepath'] = params.pop('file_path')
                    
                    tool_calls.append({
                        "name": tool_name,
                        "arguments": params
                    })
                except json.JSONDecodeError:
                    continue
        
        return tool_calls
    
    @staticmethod
    def should_use_tools(response: str) -> bool:
        """
        Check if the response contains tool calls.
        """
        import re
        
        # Primary check: JSON code blocks with tool_calls
        json_pattern = r'```json\s*\n.*?"tool_calls".*?\n\s*```'
        if re.search(json_pattern, response, re.IGNORECASE | re.DOTALL):
            return True
        
        # Simple fallback check
        if re.search(r'TOOL_CALL:\s*[a-zA-Z_][a-zA-Z0-9_]*', response, re.IGNORECASE):
            return True
            
        return False