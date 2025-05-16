"""
Plugin for displaying Jibberish version information.
This is a fresh implementation to avoid any caching issues.
"""
import os
import sys
import click

# Add the parent directory to sys.path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import api
from app.plugin_system import BuiltinCommand, BuiltinCommandRegistry
from app.utils import silence_stdout

# Use a uniquely named class to force reloading
class VersionPlugin(BuiltinCommand):
    """Command plugin for displaying version information."""
    
    # Plugin attributes
    plugin_name = "version_command"  # Name of the plugin
    is_required = True  # Version command is an optional plugin
    is_enabled = True  # Enabled by default, can be overridden by environment variable
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        command = command.strip()
        return command in ["version"]
        
    def execute(self, command):
        """Execute the version command."""
        # In standalone mode, we only want to display the version number
        # Skip all other output when running with -v option
        # Display version details - don't silence this as it's the main output
        print(click.style(f"Jibberish v{api.__version__}", fg="green", bold=True))
        print(click.style(f"{api.VERSION_NAME}", fg="green"))
        
        print("\nFor more information, visit: https://github.com/bjeremy23/jibberish")
        return True


# Register with a try-except to catch any errors
BuiltinCommandRegistry.register(VersionPlugin())