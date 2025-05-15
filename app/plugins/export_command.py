"""
Export command plugin for setting environment variables.
"""
import os
import click
from ..plugin_system import BuiltinCommand, BuiltinCommandRegistry


class ExportCommand(BuiltinCommand):
    """Plugin for the 'export' command to set environment variables"""
    
    # Plugin attributes
    plugin_name = "export_command"  # Name of the plugin
    is_required = True  # Export command is a required plugin
    is_enabled = True  # Always enabled since it's required
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command == "export" or command.startswith("export ")
    
    def execute(self, command):
        """Set an environment variable or list all environment variables"""
        try:
            # Check if it's just 'export' without arguments
            if command.strip() == 'export':
                # Return a tuple to signal that this command should be passed to the executor
                return False, command

            # Strip the 'export ' prefix
            var_assignment = command[7:].strip()
            
            # Check if there's an assignment
            if '=' in var_assignment:
                # Split at the first equals sign
                var_name, var_value = var_assignment.split('=', 1)
                var_name = var_name.strip()
                
                # Handle quoted values
                if var_value.startswith('"') and var_value.endswith('"'):
                    var_value = var_value[1:-1]
                elif var_value.startswith("'") and var_value.endswith("'"):
                    var_value = var_value[1:-1]
                
                # Set the environment variable
                os.environ[var_name] = var_value
                        
                # Print the variable name and value
                click.echo(click.style(f"Environment variable {var_name}={var_value}", fg="green"))
            else:
                click.echo(click.style(f"Invalid format: Use export NAME=VALUE", fg="red"))
        except Exception as e:
            click.echo(click.style(f"Error setting environment variable: {str(e)}", fg="red"))
        
        return True


# Register the plugin with the registry
BuiltinCommandRegistry.register(ExportCommand())