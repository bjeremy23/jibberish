"""
File writer tool for the jibberish tool system.

This tool allows AI to write content to files, particularly useful for saving
AI responses from ask_question() to specified locations.
"""

import os
from pathlib import Path
from typing import Dict, Any
from .base import Tool


class FileWriterTool(Tool):
    """
    Tool for writing content to files.
    
    This tool can create new files or overwrite existing files with specified content.
    It includes safety checks for file permissions, directory creation, and path validation.
    """
    
    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "Write content to a file at the specified filepath. Creates the file and/or directories if they don't exist and appends or overwrites based on the 'append' flag. Useful for saving AI responses, notes, or generated content to files."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The path where the file should be written. Can be absolute or relative to current working directory. Supports tilde (~) expansion for home directory."
                },
                "content": {
                    "type": "string", 
                    "description": "The content to write to the file. This will completely replace any existing file content."
                },
                "append": {
                    "type": "boolean",
                    "description": "If true, append content to the file instead of overwriting. If false or not specified, overwrites the file. Default is false."
                },
                "encoding": {
                    "type": "string",
                    "description": "Text encoding to use when writing the file. Default is 'utf-8'. Common options: 'utf-8', 'ascii', 'latin-1'."
                }
            },
            "required": ["filepath", "content"]
        }
    
    def execute(self, **kwargs) -> str:
        """
        Write content to a file.
        
        Args:
            filepath (str): Path to the file to write
            content (str): Content to write to the file
            append (bool): Whether to append (True) or overwrite (False). Default: False
            encoding (str): Text encoding to use. Default: 'utf-8'
            
        Returns:
            str: Success message with file details
            
        Raises:
            Exception: If file cannot be written due to permissions, invalid path, etc.
        """
        filepath = kwargs.get('filepath', '')
        content = kwargs.get('content', '')
        append = kwargs.get('append', False)
        encoding = kwargs.get('encoding', 'utf-8')

        if not filepath:
            raise ValueError("filepath parameter is required")
        
        if content is None:
            content = ""  # Allow writing empty files
        
        try:
            # make sure the content is not in "```" scripting block
            if content.startswith("```") and content.endswith("```"):
                content = content.strip("```").strip()

            content = content.replace('\\n', '\n').replace('\\t', '\t')

            # Expand tilde for home directory
            expanded_path = os.path.expanduser(filepath)
            
            # Convert to Path object for easier manipulation
            file_path = Path(expanded_path).resolve()
            
            # Ensure parent directories exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine write mode
            mode = 'a' if append else 'w'
            
            # Check if we're appending to an existing file
            file_existed = file_path.exists()
            original_size = file_path.stat().st_size if file_existed else 0
            
            # Write the content
            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)
            
            # Get file stats after writing
            new_size = file_path.stat().st_size
            content_length = len(content.encode(encoding))
            
            # Build result message
            if append and file_existed:
                result = f"✅ Content appended to file: {file_path}\n"
                result += f"   Original size: {original_size} bytes\n"
                result += f"   Added: {content_length} bytes\n" 
                result += f"   New size: {new_size} bytes\n"
                result += f"   Encoding: {encoding}"
            else:
                action = "overwritten" if file_existed else "created"
                result = f"✅ File {action}: {file_path}\n"
                result += f"   Size: {new_size} bytes ({content_length} bytes written)\n"
                result += f"   Encoding: {encoding}\n"
                result += f"   Lines: {content.count(chr(10)) + 1 if content else 0}"
            
            return result
            
        except PermissionError:
            raise Exception(f"Permission denied: Cannot write to '{expanded_path}'. Check file permissions and directory access.")
        
        except OSError as e:
            if e.errno == 36:  # File name too long
                raise Exception(f"File name too long: '{expanded_path}'")
            elif e.errno == 28:  # No space left on device
                raise Exception(f"No space left on device: Cannot write to '{expanded_path}'")
            else:
                raise Exception(f"OS error writing to '{expanded_path}': {str(e)}")
        
        except UnicodeEncodeError as e:
            raise Exception(f"Encoding error: Cannot encode content using '{encoding}' encoding. Try 'utf-8' or 'latin-1'.")
        
        except Exception as e:
            raise Exception(f"Failed to write file '{expanded_path}': {str(e)}")