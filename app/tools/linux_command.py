"""
Linux Command Tool for executing Linux commands directly using executor.py.
"""

import os

# Capture the user's PROMPT_AI_COMMANDS setting before any other imports that might modify it
_USER_PROMPT_SETTING = os.environ.get('PROMPT_AI_COMMANDS', '').lower()

import re
import click
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
        return "All requests to use a linux command MUST use this tool. This tool is called with only executable linux command strings; (e.g., 'mkdir dir && cd dir' or 'ls' or 'git log'). You will use this tool without prompting the user or waiting for confirmation."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "All requests to use a linux command MUST use this tool. This tool is called with only executable linux command strings; (e.g., 'mkdir dir && cd dir' or 'ls' or 'git log'). You will use this tool without prompting the user or waitng for confirmation."
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
        # Capture the user's original PROMPT_AI_COMMANDS setting before any imports modify it
        user_prompt_setting = _USER_PROMPT_SETTING
        
        try:
            # Get the raw response from the AI
            raw_response = command
            
            # Process the raw response to get the final command
            final_command = None
            
            # Remove markdown code block formatting if present
            # This handles patterns like ```bash\ncommand\n``` or ```\ncommand\n```
            code_block_pattern = r"```(?:bash|sh)?\s*([\s\S]*?)```"
            match = re.search(code_block_pattern, raw_response)
            if match:
                # Get the command inside the code block and handle possible newlines
                command_text = match.group(1).strip()
                
                # Process multiple lines of commands
                lines = command_text.splitlines()
                if len(lines) >= 2:
                    # Handle multiple separate commands - join with && to execute sequentially locally
                    if len(lines) >= 2:
                        combined_commands = []
                        for line in lines:
                            line = line.strip()
                            if line:  # Only include non-empty lines
                                combined_commands.append(line)
                        # Join all commands with && to execute them sequentially
                        final_command = ' && '.join(combined_commands)
                        
                # For simple one-line commands or commands with line continuations
                if len(lines) == 1 or any(line.strip().endswith('\\') for line in lines[:-1]):
                    final_command = ' '.join(line.strip() for line in lines)
            else:
                # If no code block found, process the original response
                lines = raw_response.splitlines()
                
                # Special handling for SSH commands
                if len(lines) >= 2:
                    first_line = lines[0].strip()
                    second_line = lines[1].strip()
                    
                    # If the first line is an SSH command and doesn't end with quotes
                    if first_line.startswith('ssh ') and not (first_line.endswith('"') or first_line.endswith("'")):
                        # Combine the SSH command with the next line in quotes
                        final_command = f"{first_line} \"{second_line}\""
                        
                    # Multiple separate commands - join with && to execute sequentially
                    elif first_line and second_line and not first_line.endswith('\\'):
                        combined_commands = []
                        for line in lines:
                            line = line.strip()
                            if line:  # Only include non-empty lines
                                combined_commands.append(line)
                        # Join all commands with && to execute them sequentially
                        final_command = ' && '.join(combined_commands)
            
            # Otherwise use the first line or the raw response
            if final_command is None:
                final_command = lines[0] if lines else raw_response

            # Check if the response has multiple lines (comment + command structure)
            actual_command = final_command
            if '\n' in final_command:
                lines = final_command.strip().split('\n')
                # Extract the last line as the actual command to execute
                # (assuming comment lines come first and the actual command is last)
                actual_command = lines[-1].strip()

            # Sanitize command: remove any remaining newlines/carriage returns that could cause
            # "syntax error: unexpected end of file" in bash
            actual_command = actual_command.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
            # Collapse multiple spaces into one
            actual_command = ' '.join(actual_command.split())

            # Check if we should prompt before executing based on user's original setting
            # Only prompt if user explicitly set PROMPT_AI_COMMANDS to enable prompting
            if user_prompt_setting in ('true', 'always', 'yes', '1'):
                if not prompt_before_execution(f"'{actual_command}'"):
                    return "Command execution cancelled by user"

            # Execute the command directly
            try:
                # Use a special marker to indicate this is a tool-generated command
                success, result = execute_command_with_built_ins(actual_command, original_command="__TOOL_GENERATED__", add_to_history=True)
                if success == 0:
                    return f"SUCCESS: {result}"
                else:
                    return f"ERROR: {result}"
            except Exception as e:
                return f"ERROR: {str(e)}"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
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