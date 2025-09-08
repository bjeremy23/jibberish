"""
Linux Command Tool for executing Linux commands directly using executor.py.
"""

import os
from typing import Dict, Any
from .base import Tool
from ..executor import execute_shell_command
from ..utils import prompt_before_execution, execute_command_with_built_ins


class LinuxCommandTool(Tool):
    """
    Tool for executing Linux commands directly using the executor module.
    This tool takes a Linux command string and executes it using the same
    executor that jibberish uses internally.
    """
    
    @property
    def name(self) -> str:
        return "linux_command"
    
    @property
    def description(self) -> str:
        return "Execute Linux shell commands with support for built-ins and command chaining. ALWAYS use this tool when executing any Linux command. For compound requests, chain commands with && or ; (e.g., 'mkdir dir && cd dir'). Do not ask permission - execute immediately."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The Linux command to execute. Chain multiple commands with && or ; (e.g., 'mkdir dir && cd dir'). Execute commands immediately without asking permission."
                }
            },
            "required": ["command"]
        }
    
    def execute(self, command: str, **kwargs) -> str:
        """
        Execute a Linux command using the same logic as jibberish shell.
        
        Args:
            command: The Linux command string to execute
            
        Returns:
            String containing the result of the command execution or an error message
        """
        try:
            # Check if the command is in the WARN_LIST and should not be executed
            if self._is_command_in_warn_list(command):
                return f"SECURITY: Cannot execute command '{command}' - it is in the WARN_LIST of potentially dangerous commands. This command requires manual execution by the user for safety."
            
            # Check if we should prompt before executing (respect PROMPT_AI_COMMANDS setting)
            if not prompt_before_execution(f"command '{command}'"):
                return f"Command execution cancelled: {command}"
            
            # Use execute_shell_command directly to capture output for tool use
            from ..executor import execute_shell_command
            returncode, output, error = execute_shell_command(command)
            
            if returncode == 0:
                # Command succeeded, return the output
                return output.strip() if output else f"Command '{command}' executed successfully (no output)"
            elif returncode == -1:
                # Special case for interrupted commands
                return f"ERROR: Command '{command}' was interrupted: {error}"
            else:
                # Command failed, return error information
                error_msg = f"ERROR: Command '{command}' failed with exit code {returncode}"
                if error:
                    error_msg += f": {error}"
                return error_msg
                
        except Exception as e:
            return f"ERROR: Failed to execute command '{command}': {str(e)}"
    
    def _is_command_in_warn_list(self, command: str) -> bool:
        """
        Check if the command starts with any item in the WARN_LIST environment variable.
        
        Args:
            command: The command to check
            
        Returns:
            True if the command is in the warn list, False otherwise
        """
        warn_list = os.environ.get("WARN_LIST", "").split(",")
        command_stripped = command.strip()
        
        for item in warn_list:
            item_stripped = item.strip()
            if item_stripped and (command_stripped.startswith(item_stripped) or item_stripped == "all"):
                return True
                
        return False