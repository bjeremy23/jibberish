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
        # Only handle cd commands that don't contain && (those should go to execute_chained_commands)
        return command.startswith("cd") and "&&" not in command
    
    def execute(self, command):
        """Change the current directory"""
        # Extract the path part after 'cd'
        path_part = command[2:].strip()
        
        # If no path provided (just 'cd'), go to home directory
        if not path_part:
            home_dir = os.path.expanduser("~")
            os.chdir(home_dir)
        else:
            # Check if the path contains command substitution $(...) or backticks
            if ('$(' in path_part and ')' in path_part) or ('`' in path_part):
                # Execute the command using shell to evaluate the substitution
                import subprocess
                try:
                    # Evaluate the command to get the actual directory path
                    process = subprocess.run(
                        f"echo {path_part}",
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
                    os.chdir(evaluated_path)
                except subprocess.CalledProcessError as e:
                    click.echo(click.style(f"Error evaluating command: {e}", fg="red"))
                except FileNotFoundError:
                    click.echo(click.style(f"Error: Directory not found after command evaluation", fg="red"))
                except PermissionError:
                    click.echo(click.style(f"Error: Permission denied after command evaluation", fg="red"))
                except Exception as e:
                    click.echo(click.style(f"Error: {str(e)}", fg="red"))
            else:
                # Normal path handling
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
