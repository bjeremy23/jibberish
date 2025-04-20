"""
Directory stack commands (pushd/popd) plugin.
"""
import os
import click
from plugin_system import BuiltinCommand, BuiltinCommandRegistry

# Directory stack (shared state at module level)
dir_stack = []


class DirStackCommand(BuiltinCommand):
    """Plugin for directory stack commands (pushd/popd)"""
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.startswith("pushd") or command.startswith("popd") or command.startswith("dirs")
    
    def execute(self, command):
        """Execute pushd, popd, or dirs command"""
        if command.startswith("pushd"):
            try:
                # Extract directory argument
                parts = command.split(None, 1)
                if len(parts) < 2:
                    click.echo(click.style("Usage: pushd <directory>", fg="red"))
                    return True
                
                directory = parts[1]
                self._pushd(directory)
            except IndexError:
                click.echo(click.style("Usage: pushd <directory>", fg="red"))
        elif command.startswith("popd"):
            self._popd()
        elif command.startswith("dirs"):
            self._dirs()
            
        return True
    
    def _pushd(self, directory):
        """Push current directory to stack and change to new directory"""
        current_directory = os.getcwd()
        
        # Expand tilde to home directory
        expanded_dir = os.path.expanduser(directory)
        
        # Check if the directory exists before changing to it
        if os.path.isdir(expanded_dir):
            # Insert at the beginning of the stack (most recent)
            dir_stack.insert(0, current_directory)
            os.chdir(expanded_dir)

            # Join the directories
            dirs = ' '.join(map(str, dir_stack))
            click.echo(f"{os.getcwd()} {dirs}")
        else:
            click.echo(click.style(f"Directory not found: {expanded_dir}", fg="red"))
    
    def _popd(self):
        """Pop directory from stack and change to that directory"""
        if dir_stack:
            # Pop the most recently pushed directory (first in the stack)
            directory = dir_stack.pop(0)
            # Change to that directory
            os.chdir(directory)
             
            # Display the current directory and stack
            dirs = ' '.join(map(str, dir_stack))
            click.echo(f"{os.getcwd()} {dirs}")
        else:
            click.echo(click.style("Directory stack is empty", fg="red"))
            
    def _dirs(self):
        """Display the directory stack"""
        if dir_stack:
            dirs = ' '.join(map(str, dir_stack))
            click.echo(f"{os.getcwd()} {dirs}")
        else:
            click.echo(click.style("Directory stack is empty", fg="red"))


# Register the plugin with the registry
BuiltinCommandRegistry.register(DirStackCommand())
