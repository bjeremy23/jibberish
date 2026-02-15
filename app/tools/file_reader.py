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
                    "description": "Maximum number of lines to read. If not specified, reads entire file (auto-truncated to 500 lines for files over 1MB). Useful for large files.",
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
            
            # Check if file exists, if the file does not exist, look for the file recursivly starting from the 
            # current directory and ask if the user meant that file
            if not os.path.exists(expanded_path):
                for root, dirs, files in os.walk('.'):
                    if os.path.basename(filepath) in files:
                        found_path = os.path.join(root, os.path.basename(filepath))
                        return f"File '{filepath}' not found. Did you mean '{found_path}'?"
                return f"ERROR: File '{filepath}' not found."

            # Check if it's actually a file (not a directory)
            if not os.path.isfile(expanded_path):
                return f"ERROR: '{filepath}' is not a file."
            
            # Check if file is readable
            if not os.access(expanded_path, os.R_OK):
                return f"ERROR: Cannot read file '{filepath}' - permission denied."
            
            # Get file info
            file_size = os.path.getsize(expanded_path)

            # For large files without line limits, auto-truncate instead of refusing
            MAX_RETURN_LINES = 500
            truncated = False
            if file_size > 1024 * 1024 and max_lines is None:
                max_lines = MAX_RETURN_LINES
                truncated = True

            # Stream lines lazily to avoid loading entire large files into memory
            total_lines = 0
            selected_lines = []
            start_idx = max(0, start_line - 1)

            with open(expanded_path, 'r', encoding='utf-8', errors='replace') as f:
                for i, line in enumerate(f):
                    total_lines = i + 1
                    if i < start_idx:
                        continue
                    if max_lines is not None and len(selected_lines) >= max_lines:
                        continue
                    selected_lines.append(line)

            if start_idx >= total_lines:
                return f"ERROR: start_line {start_line} is beyond the file length ({total_lines} lines)."

            # Format the result
            content = ''.join(selected_lines)

            # Add metadata header
            result_lines = len(selected_lines)
            metadata = f"=== File: {filepath} ===\n"
            metadata += f"=== Lines {start_line}-{start_idx + result_lines} of {total_lines} total ===\n"

            if truncated:
                metadata += f"=== [Truncated: showing first {MAX_RETURN_LINES} lines. Use start_line/max_lines to read more.] ===\n"

            metadata += "\n"

            return metadata + content
            
        except UnicodeDecodeError:
            return f"ERROR: File '{filepath}' contains binary data or uses an unsupported encoding."
        except Exception as e:
            return f"ERROR: Failed to read file '{filepath}': {str(e)}"