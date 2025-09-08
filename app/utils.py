"""
Utility functions for Jibberish shell that don't fit elsewhere.

This module contains functions for:
- generate_tool_context_message() - Creates system messages for AI tool usage
- is_debug_enabled() - Controls output verbosity based on JIBBERISH_DEBUG environment variable
"""
import os
import sys
import io
import click
from contextlib import contextmanager

def should_prompt_ai_commands():
    """
    Check if AI commands should be prompted before execution based on PROMPT_AI_COMMANDS environment variable.
    
    Returns:
        bool: True if commands should be prompted, False if they should execute immediately
    """
    prompt_setting = os.environ.get('PROMPT_AI_COMMANDS', '').lower()
    return prompt_setting in ('true', 'always', 'yes', '1')

def prompt_before_execution(command_description="this command"):
    """
    Prompt the user before executing a command if PROMPT_AI_COMMANDS is enabled.
    
    Args:
        command_description: Description of what will be executed (default: "this command")
        
    Returns:
        bool: True if user agrees to execute, False if cancelled
    """
    if not should_prompt_ai_commands():
        return True
        
    # Add an explicit newline and prompt message
    click.echo("")
    choice = input(click.style(f"Execute {command_description}? [y/n]: ", fg="blue"))
    
    sys.stdout.flush()
    if choice.lower() != 'y':
        click.echo(click.style("Command execution cancelled", fg="yellow"))
        return False
    
    return True

def execute_command_with_built_ins(command, original_command=None, add_to_history=False):
    """
    Execute a command handling built-ins and chained commands.
    This is the core command execution logic used by both jibberish.py and linux_command.py.
    
    Args:
        command: The command to execute
        original_command: The original command (used for history when processing AI commands)
        add_to_history: Whether to add generated commands to history
        
    Returns:
        tuple: (success: bool, output: str) - success indicates if command executed without errors
    """
    try:
        # Import here to avoid circular imports
        from .executor import execute_command, execute_chained_commands, is_built_in
        if add_to_history:
            import readline
            from . import history
        
        # Check if the command is a built-in command or requires special handling
        handled, new_command = is_built_in(command)
        
        # If a plugin returned a new command to process, update the command
        if not handled and new_command is not None:
            # Add the generated command to history as well (for AI-generated commands)
            # This ensures both the original request and the generated command are in history
            if add_to_history and original_command and original_command.startswith('#'):
                readline.add_history(new_command)
                # Apply history limit after adding a new command
                history.limit_history_size()
            
            command = new_command
            
            # Process the new command
            if '&&' in command or ';' in command:
                execute_chained_commands(command, 0)
                return True, f"Executed chained command: {command}"
            else:
                # Check if the new command is a built-in
                new_handled, another_command = is_built_in(command)
                if not new_handled:
                    # Just execute the command directly
                    execute_command(command)
                    return True, f"Executed command: {command}"
                elif another_command is not None:
                    # Handle nested command returns (rare case)
                    click.echo(click.style(f"Executing nested command: {another_command}", fg="blue"))
                    # For complex commands with nested quotes, use proper escaping
                    execute_command(another_command)
                    return True, f"Executed nested command: {another_command}"
                else:
                    return True, "Command handled by built-in plugin"
        # If command was fully handled by a built-in, do nothing more
        elif handled:
            return True, "Command handled by built-in plugin"
        # Check if the command contains && or ; for command chaining
        elif '&&' in command or ';' in command:
            execute_chained_commands(command, 0)
            return True, f"Executed chained command: {command}"
        else:
            # we will execute the command in the case of a non-built-in command
            execute_command(command)
            return True, f"Executed command: {command}"
            
    except Exception as e:
        error_msg = f"ERROR: Failed to execute command '{command}': {str(e)}"
        return False, error_msg

def is_debug_enabled():
    """
    Check if debug output is enabled via JIBBERISH_DEBUG environment variable.
    
    This controls whether the application shows verbose output like environment
    variable loading and plugin registration messages.
    
    Users can set JIBBERISH_DEBUG=true in their .jbrsh file to see all messages,
    or leave it unset/false for clean output.
    """
    debug_value = os.environ.get('JIBBERISH_DEBUG', 'false').lower()
    return debug_value in ['true', 'yes', 'y', '1']

@contextmanager
def silence_stdout():
    """
    Context manager to silence stdout if debug mode is not enabled.
    
    This function respects the JIBBERISH_DEBUG environment variable.
    If JIBBERISH_DEBUG=true, output will not be silenced, regardless of standalone mode.
    """
    if not is_debug_enabled():
        original_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            yield
        finally:
            sys.stdout = original_stdout
    else:
        yield

def generate_tool_context_message():
    """
    Generate a system message describing available tools and their parameters.
    
    This function checks if tools are available, iterates through registered tools,
    and creates a formatted system message that tells the AI about available tools
    including their names, descriptions, parameter schemas, and usage examples.
    
    Returns:
        dict or None: System message dict for AI context, or None if no tools available
    """
    try:
        from app.tools import ToolRegistry
        TOOLS_AVAILABLE = True
    except ImportError:
        return None
    
    if not TOOLS_AVAILABLE:
        return None
        
    available_tools = ToolRegistry.get_all_tools()
    if not available_tools:
        return None
    
    tool_descriptions = []
    for tool_name, tool in available_tools.items():
        function_def = tool.to_function_definition()
        
        # Format the tool information with parameter details
        tool_info = f"- {function_def['name']}: {function_def['description']}"
        
        # Add parameter information
        if 'parameters' in function_def and 'properties' in function_def['parameters']:
            params_info = []
            properties = function_def['parameters']['properties']
            required = function_def['parameters'].get('required', [])
            
            for param_name, param_info in properties.items():
                param_type = param_info.get('type', 'any')
                param_desc = param_info.get('description', '')
                is_required = param_name in required
                
                req_indicator = " (required)" if is_required else " (optional)"
                params_info.append(f"    • {param_name} ({param_type}){req_indicator}: {param_desc}")
            
            if params_info:
                tool_info += "\n" + "\n".join(params_info)
        
        tool_descriptions.append(tool_info)
    
    return {
        "role": "system", 
        "content": """You have access to the following tools to help answer questions:

""" + chr(10).join(tool_descriptions) + """

MANDATORY: You MUST use tools to complete requests that require reading files, writing files, or accessing external information. Do not explain what you will do - immediately use the tools.

REQUIRED FORMAT: When using tools, you MUST respond with this exact JSON format and nothing else:

```json
{
  "tool_calls": [
    {
      "name": "tool_name",
      "arguments": {
        "param1": "value1",
        "param2": "value2"
      }
    }
  ]
}
```

CRITICAL: Always use the EXACT parameter names specified in the tool schema above. For example, write_file uses 'filepath', not 'path' or 'file_path'.

TOOL CHAINING: When a user's request requires multiple tools or actions (like "read X and write Y"), include ALL required tools in a single JSON block.

Use tools when you need additional information to provide a complete answer. Pay attention to parameter types and requirements."""
    }
