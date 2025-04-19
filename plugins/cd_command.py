"""
Change Directory (cd) command plugin.
"""
import os
import click
from plugin_system import BuiltinCommand, BuiltinCommandRegistry


class ChangeDirectoryCommand(BuiltinCommand):
    """Plugin for the 'cd' command to change directories"""
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.startswith("cd")
    
    def execute(self, command):
        """Change the current directory"""
        # Extract the path part after 'cd'
        path_part = command[2:].strip()
        
        # If no path provided (just 'cd'), go to home directory
        if not path_part:
            home_dir = os.path.expanduser("~")
            os.chdir(home_dir)
        else:
            path = os.path.expanduser(path_part)
            if os.path.isfile(path):
                click.echo(click.style(f"Error: '{path}' is a file, not a directory", fg="red"))
            else:
                try:
                    os.chdir(path)
                except FileNotFoundError:
                    click.echo(click.style(f"Error: No such directory: '{path}'", fg="red"))
                except PermissionError:
                    click.echo(click.style(f"Error: Permission denied: '{path}'", fg="red"))
                except Exception as e:
                    click.echo(click.style(f"Error: {str(e)}", fg="red"))
        
        return True


# Register the plugin with the registry
BuiltinCommandRegistry.register(ChangeDirectoryCommand())
