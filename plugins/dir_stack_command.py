"""
Directory stack commands (pushd/popd) plugin.
"""
import os
import click
from plugin_system import BuiltinCommand, BuiltinCommandRegistry
# Import the aliases dictionary to check for aliases in command chains
from plugins.alias_command import aliases

# Directory stack (shared state at module level)
dir_stack = []


class DirStackCommand(BuiltinCommand):
    """Plugin for directory stack commands (pushd/popd)"""
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.startswith("pushd") or command.startswith("popd") or command.startswith("dirs")
    
    def execute(self, command):
        """Execute pushd, popd, or dirs command"""
        # Check if command contains a chain
        has_chain = '&&' in command
        rest_of_chain = None
        
        if command.startswith("pushd"):
            try:
                # Extract directory argument
                parts = command.split(None, 1)
                if len(parts) < 2:
                    click.echo(click.style("Usage: pushd <directory>", fg="red"))
                    return True
                
                if has_chain:
                    # Split the command to get directory and rest of chain
                    cmd_parts = parts[1].split('&&', 1)
                    directory = cmd_parts[0].strip()
                    if len(cmd_parts) > 1:
                        rest_of_chain = cmd_parts[1].strip()
                else:
                    # No command chaining
                    directory = parts[1].strip()
                
                self._pushd(directory)
            except IndexError:
                click.echo(click.style("Usage: pushd <directory>", fg="red"))
        elif command.startswith("popd"):
            self._popd()
            if has_chain:
                # Get everything after the "popd" command and &&
                rest_of_chain = command.split('&&', 1)[1].strip()
        elif command.startswith("dirs"):
            self._dirs()
            if has_chain:
                # Get everything after the "dirs" command and &&
                rest_of_chain = command.split('&&', 1)[1].strip()
        
        # If there's a command chain, check for aliases before returning
        if rest_of_chain:
            # Check if the chained command is a simple command (no pipes, redirects, etc.)
            # that could match an alias
            first_cmd = rest_of_chain.split()[0] if rest_of_chain.split() else ""
            
            # If the first word in the rest of chain matches an alias, replace it
            if first_cmd in aliases:
                # Replace the first command with its alias
                aliased_cmd = aliases[first_cmd]
                # Replace only the first word, preserving any arguments
                if len(first_cmd) == len(rest_of_chain):
                    # Simple command with no args
                    rest_of_chain = aliased_cmd
                else:
                    # Command with args - replace only the command part
                    args = rest_of_chain[len(first_cmd):].strip()
                    rest_of_chain = f"{aliased_cmd} {args}"
                    
            # Return False to continue processing with the new chain
            return False, rest_of_chain
        
        return True
    
    def _pushd(self, directory):
        """Push current directory to stack and change to new directory"""
        current_directory = os.getcwd()
        
        # Check if the path contains command substitution $(...) or backticks
        if ('$(' in directory and ')' in directory) or ('`' in directory):
            # Execute the command using shell to evaluate the substitution
            import subprocess
            try:
                # Evaluate the command to get the actual directory path
                process = subprocess.run(
                    f"echo {directory}",
                    shell=True,
                    executable='/bin/bash',
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Get the evaluated path from the command output
                evaluated_path = process.stdout.strip()
                click.echo(f"Resolved path: {evaluated_path}")
                
                # Change to the evaluated directory
                if os.path.isdir(evaluated_path):
                    # Insert at the beginning of the stack (most recent)
                    dir_stack.insert(0, current_directory)
                    os.chdir(evaluated_path)
                    
                    # Join the directories
                    dirs = ' '.join(map(str, dir_stack))
                    click.echo(f"{os.getcwd()} {dirs}")
                else:
                    click.echo(click.style(f"Directory not found after command evaluation: {evaluated_path}", fg="red"))
            except subprocess.CalledProcessError as e:
                click.echo(click.style(f"Error evaluating command: {e}", fg="red"))
            except Exception as e:
                click.echo(click.style(f"Error: {str(e)}", fg="red"))
        else:
            # Normal path handling with tilde expansion
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
