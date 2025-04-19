"""
Directory stack commands (pushd/popd) plugin.
"""
import os
import click
from plugin_system import BuiltinCommand, BuiltinCommandRegistry


class DirStackCommand(BuiltinCommand):
    """Plugin for directory stack commands (pushd/popd)"""
    
    # Directory stack (shared state)
    _dir_stack = []
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.startswith("pushd") or command.startswith("popd")
    
    def execute(self, command):
        """Execute pushd or popd command"""
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
            
        return True
    
    def _pushd(self, directory):
        """Push current directory to stack and change to new directory"""
        current_directory = os.getcwd()
        self._dir_stack.append(current_directory)
        
        # Expand tilde to home directory
        expanded_dir = os.path.expanduser(directory)
        os.chdir(expanded_dir)

        # Join the directories in reverse order
        dirs = ' '.join(map(str, self._dir_stack[::-1]))
        click.echo(f"{os.getcwd()} {dirs}")
    
    def _popd(self):
        """Pop directory from stack and change to that directory"""
        if self._dir_stack:
            directory = self._dir_stack.pop()
            os.chdir(directory)
             
            dirs = ' '.join(map(str, self._dir_stack[::-1]))
            click.echo(f"{os.getcwd()} {dirs}")
        else:
            click.echo(click.style("Directory stack is empty", fg="red"))


# Register the plugin with the registry
BuiltinCommandRegistry.register(DirStackCommand())
