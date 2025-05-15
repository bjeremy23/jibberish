# Import the plugin system
import os
import sys

# Add the parent directory to sys.path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.plugin_system import BuiltinCommandRegistry, load_plugins
from app.utils import silence_stdout, is_standalone_mode


# Load all plugins when this module is imported
with silence_stdout():
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
