import os
import subprocess
import click

# Import the plugin system
from plugin_system import BuiltinCommandRegistry, load_plugins


# Load all plugins when this module is imported
load_plugins()


def is_built_in(command):
    """
    Check if the command is a built-in command using the plugin system
    
    Args:
        command (str): The command to check
        
    Returns:
        tuple: (bool, str or None)
            - First element is True if the command was handled, False otherwise
            - Second element is a new command to process if returned by the plugin, or None
    """
    handler = BuiltinCommandRegistry.find_handler(command)
    if handler:
        result = handler.execute(command)
        
        # Check if the plugin returned a tuple with a new command
        if isinstance(result, tuple) and len(result) == 2:
            handled, new_command = result
            return handled, new_command
        
        # Standard case: just return the boolean result and None
        return result, None
    
    # No handler found
    return False, None
