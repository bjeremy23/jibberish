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
        bool: True if the command was handled by a built-in plugin, False otherwise
    """
    handler = BuiltinCommandRegistry.find_handler(command)
    if handler:
        return handler.execute(command)
    return False
