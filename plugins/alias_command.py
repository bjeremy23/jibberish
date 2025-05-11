"""
Alias command plugin with persistence between shell sessions.
"""
import os
import re
import json
import click
from plugin_system import BuiltinCommand, BuiltinCommandRegistry

# File to store aliases
ALIASES_FILE = os.path.expanduser("~/.jbrsh_aliases")

# Dictionary to store aliases
# Format: {'alias_name': 'replacement_command'}
aliases = {}

# Load aliases from file if it exists
def load_aliases():
    if os.path.exists(ALIASES_FILE):
        try:
            with open(ALIASES_FILE, 'r') as f:
                loaded_aliases = json.load(f)
                aliases.update(loaded_aliases)
            return True
        except Exception as e:
            click.echo(click.style(f"Failed to load aliases: {str(e)}", fg="red"))
    return False

# Function to get all aliases - used by executor.py for alias expansion
def get_aliases():
    # Make sure aliases are loaded
    load_aliases()
    return aliases

# Save aliases to file
def save_aliases():
    try:
        with open(ALIASES_FILE, 'w') as f:
            json.dump(aliases, f, indent=2)
        return True
    except Exception as e:
        click.echo(click.style(f"Failed to save aliases: {str(e)}", fg="red"))
        return False

# Load aliases at module initialization
load_aliases()

class AliasCommand(BuiltinCommand):
    """Plugin for managing command aliases using the 'alias' command"""
    
    # Plugin attributes
    plugin_name = "alias_command"  # Name of the plugin
    is_required = True  # Alias command is optional
    is_enabled = True  # Enabled by default, can be overridden by environment variable
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        command = command.strip()
        return command == "alias" or command.startswith("alias ") or command.startswith("alias |") or command in aliases
    
    def execute(self, command):
        """Handle alias commands or replace with aliased command"""
        # If command matches an existing alias, replace it with the aliased command
        if command.strip() in aliases:
            aliased_command = aliases[command.strip()]
            return False, aliased_command
        
        # Parse and handle alias commands
        cmd = command.strip()
        if cmd == "alias" or cmd.startswith("alias |"):
            # Check if this is a piped command
            if '|' in cmd:
                # Get the part after the pipe
                pipe_command = cmd[cmd.index('|')+1:].strip()
                
                # Generate alias output as a string
                alias_output = []
                if not aliases:
                    alias_output.append("No aliases defined")
                else:
                    for alias_name, alias_value in aliases.items():
                        alias_output.append(f"alias {alias_name}='{alias_value}'")
                
                # Create a temporary file to store the alias output
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
                    temp.write('\n'.join(alias_output))
                    temp_path = temp.name
                
                # Execute the pipe command with alias output as input
                import subprocess
                full_command = f"cat {temp_path} | {pipe_command}"
                
                # Execute the command
                result = subprocess.run(full_command, shell=True, text=True)
                
                # Clean up the temporary file
                import os
                os.unlink(temp_path)
                
                return True
            else:
                # Display all aliases
                if not aliases:
                    click.echo("No aliases defined")
                else:
                    click.echo(click.style("Current aliases:", fg="blue"))
                    for alias_name, alias_value in aliases.items():
                        click.echo(f"alias {alias_name}='{alias_value}'")
                return True
        
        # For alias setting commands, parse and store the alias
        command = command.strip()
        if command.startswith("alias "):
            # Remove the 'alias ' prefix
            alias_def = command[6:].strip()
            
            # Check if this is attempting to remove an alias
            if alias_def.startswith("unalias "):
                alias_to_remove = alias_def[8:].strip()
                if alias_to_remove in aliases:
                    del aliases[alias_to_remove]
                    save_aliases()  # Save to file after removing an alias
                    click.echo(click.style(f"Removed alias: {alias_to_remove}", fg="green"))
                else:
                    click.echo(click.style(f"Alias not found: {alias_to_remove}", fg="red"))
                return True
            
            # Parse alias definition (format: name='value' or name="value")
            pattern = r"^([a-zA-Z0-9_-]+)=(?:'([^']*)'|\"([^\"]*)\")$"
            match = re.match(pattern, alias_def)
            
            if match:
                alias_name = match.group(1)
                # Check which quote style was used
                alias_value = match.group(2) if match.group(2) is not None else match.group(3)
                aliases[alias_name] = alias_value
                save_aliases()  # Save to file after adding new alias
                click.echo(click.style(f"Alias set: {alias_name} -> {alias_value}", fg="green"))
                return True
            else:
                click.echo(click.style("Invalid alias format. Use: alias name='command'", fg="red"))
                return True
        
        return False


class UnaliasCommand(BuiltinCommand):
    """Plugin for removing aliases using the 'unalias' command"""
    
    # Plugin attributes
    plugin_name = "unalias_command"  # Name of the plugin
    is_required = True  # Unalias command is optional
    is_enabled = True  # Enabled by default, can be overridden by environment variable
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.strip().startswith("unalias")
    
    def execute(self, command):
        """Remove an alias"""
        command = command.strip()
        if command == "unalias":
            click.echo(click.style("Usage: unalias alias_name", fg="red"))
            return True
        
        # Parse the alias name to remove
        alias_name = command[8:].strip()
        if alias_name in aliases:
            del aliases[alias_name]
            save_aliases()  # Save to file after removing an alias
            click.echo(click.style(f"Removed alias: {alias_name}", fg="green"))
        else:
            click.echo(click.style(f"Alias not found: {alias_name}", fg="red"))
        
        return True


# Register the plugins with the registry
BuiltinCommandRegistry.register(AliasCommand())
BuiltinCommandRegistry.register(UnaliasCommand())
