"""
File Reader Tool for reading file contents and providing them as context.
"""

import os
from typing import Dict, Any
from .base import Tool

class FileReaderTool(Tool):
    """
    Tool for reading file contents to provide context to the AI.
    """
    
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "Read the contents of a file and return them as text. Useful for examining source code, configuration files, logs, or any text-based files to provide context for answering questions."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The path to the file to read. Can be absolute or relative to current working directory."
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to read. If not specified, reads entire file. Useful for large files.",
                    "default": None
                },
                "start_line": {
                    "type": "integer", 
                    "description": "Line number to start reading from (1-based). If not specified, starts from beginning.",
                    "default": 1
                }
            },
            "required": ["filepath"]
        }
    
    def execute(self, filepath: str, max_lines: int = None, start_line: int = 1, **kwargs) -> str:
        """
        Read the contents of a file.
        
        Args:
            filepath: Path to the file to read
            max_lines: Maximum number of lines to read
            start_line: Line number to start reading from (1-based)
            
        Returns:
            String containing the file contents or an error message
        """
        try:
            # Expand user path (~) and resolve relative paths
            expanded_path = os.path.expanduser(filepath)
            
            # Check if file exists
            if not os.path.exists(expanded_path):
                return f"ERROR: File '{filepath}' does not exist."
            
            # Check if it's actually a file (not a directory)
            if not os.path.isfile(expanded_path):
                return f"ERROR: '{filepath}' is not a file."
            
            # Check if file is readable
            if not os.access(expanded_path, os.R_OK):
                return f"ERROR: Cannot read file '{filepath}' - permission denied."
            
            # Get file info
            file_size = os.path.getsize(expanded_path)
            
            # Warn about very large files
            if file_size > 1024 * 1024:  # 1MB
                return f"ERROR: File '{filepath}' is very large ({file_size} bytes). Please specify max_lines parameter to limit output."
            
            with open(expanded_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # Apply line filtering
            total_lines = len(lines)
            
            # Adjust start_line to 0-based indexing
            start_idx = max(0, start_line - 1)
            
            if start_idx >= total_lines:
                return f"ERROR: start_line {start_line} is beyond the file length ({total_lines} lines)."
            
            # Select lines based on parameters
            if max_lines is not None:
                end_idx = min(total_lines, start_idx + max_lines)
                selected_lines = lines[start_idx:end_idx]
            else:
                selected_lines = lines[start_idx:]
            
            # Format the result
            content = ''.join(selected_lines)
            
            # Add metadata header
            result_lines = len(selected_lines)
            metadata = f"=== File: {filepath} ===\n"
            metadata += f"=== Lines {start_line}-{start_idx + result_lines} of {total_lines} total ===\n\n"
            
            return metadata + content
            
        except UnicodeDecodeError:
            return f"ERROR: File '{filepath}' contains binary data or uses an unsupported encoding."
        except Exception as e:
            return f"ERROR: Failed to read file '{filepath}': {str(e)}"