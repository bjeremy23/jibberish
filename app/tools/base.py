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
        
        Looks for patterns like:
        - TOOL_CALL: read_file(filepath="/path/to/file")
        - USE_TOOL: file_reader {"filepath": "/path/to/file"}
        - [TOOL] read_file: filepath="/path/to/file"
        
        Returns a list of tool calls with name and arguments.
        """
        tool_calls = []
        
        # Pattern 1: TOOL_CALL: tool_name(param=value)
        pattern1 = r'TOOL_CALL:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)'
        matches1 = re.finditer(pattern1, response, re.IGNORECASE)
        
        for match in matches1:
            tool_name = match.group(1)
            params_str = match.group(2)
            
            # Parse parameters (basic key=value parsing)
            params = {}
            if params_str.strip():
                param_pairs = re.findall(r'(\w+)\s*=\s*["\']([^"\']*)["\']', params_str)
                for key, value in param_pairs:
                    params[key] = value
            
            tool_calls.append({
                "name": tool_name,
                "arguments": params
            })
        
        # Pattern 2: USE_TOOL: tool_name {json}
        pattern2 = r'USE_TOOL:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*({.*?})'
        matches2 = re.finditer(pattern2, response, re.IGNORECASE | re.DOTALL)
        
        for match in matches2:
            tool_name = match.group(1)
            json_str = match.group(2)
            
            try:
                params = json.loads(json_str)
                tool_calls.append({
                    "name": tool_name,
                    "arguments": params
                })
            except json.JSONDecodeError:
                continue
        
        # Pattern 3: [TOOL] tool_name: param=value
        pattern3 = r'\[TOOL\]\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*?)(?=\n|$)'
        matches3 = re.finditer(pattern3, response, re.IGNORECASE)
        
        for match in matches3:
            tool_name = match.group(1)
            params_str = match.group(2).strip()
            
            params = {}
            if '=' in params_str:
                # Parse key=value format
                param_pairs = re.findall(r'(\w+)\s*=\s*["\']?([^,"\'\n]*)["\']?', params_str)
                for key, value in param_pairs:
                    params[key.strip()] = value.strip().strip('"\'')
            
            tool_calls.append({
                "name": tool_name,
                "arguments": params
            })
        
        return tool_calls
    
    @staticmethod
    def should_use_tools(response: str) -> bool:
        """
        Check if the response indicates tools should be used.
        """
        tool_indicators = [
            'TOOL_CALL:',
            'USE_TOOL:',
            '[TOOL]',
            'I need to read the file',
            'Let me examine the file',
            'I should check the contents'
        ]
        
        return any(indicator.lower() in response.lower() for indicator in tool_indicators)