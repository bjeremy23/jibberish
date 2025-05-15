"""
History command plugin.
"""
import click
from app import history
from ..plugin_system import BuiltinCommand, BuiltinCommandRegistry


class HistoryCommand(BuiltinCommand):
    """Plugin for the 'history' and 'h' commands to display command history"""
    
    # Plugin attributes
    plugin_name = "history_command"  # Name of the plugin
    is_required = True  # History command is a required plugin
    is_enabled = True  # Always enabled since it's required
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        # Strip command and check if it starts with history or h
        command_lower = command.lower().strip()
        return command_lower == "history" or command_lower == "h" or command_lower.startswith("history |") or command_lower.startswith("h |")
    
    def execute(self, command):
        """Show the command history"""
        # Check if the command contains a pipe
        if '|' in command:
            # Get the history as a string
            history_output = history.list_history(return_output=True)
            
            # Get the part after the first pipe
            pipe_command = command[command.index('|')+1:].strip()
            
            # Create a temporary file to store the history output
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
                temp.write(history_output)
                temp_path = temp.name
            
            # Execute the pipe command with history as input
            import subprocess
            full_command = f"cat {temp_path} | {pipe_command}"
            
            # Execute the command
            result = subprocess.run(full_command, shell=True, text=True)
            
            # Clean up the temporary file
            import os
            os.unlink(temp_path)
            
            return True
        else:
            # Regular execution, print directly
            history.list_history()
            return True


# Register the plugin with the registry
BuiltinCommandRegistry.register(HistoryCommand())