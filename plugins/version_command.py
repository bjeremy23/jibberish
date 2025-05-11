"""
Plugin for displaying Jibberish version information.
This is a fresh implementation to avoid any caching issues.
"""
import click, api
from plugin_system import BuiltinCommand, BuiltinCommandRegistry

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
        # Display version details
        click.echo(click.style(f"Jibberish v{api.__version__}", fg="green", bold=True))
        click.echo(click.style(f"{api.VERSION_NAME}", fg="green"))
        
        # Print additional information if desired
        click.echo()
        click.echo("For more information, visit: https://github.com/bjeremy23/jibberish")
        return True


# Register with a try-except to catch any errors
BuiltinCommandRegistry.register(VersionPlugin())
