"""
Export command plugin for setting environment variables.
"""
import os
import click
from plugin_system import BuiltinCommand, BuiltinCommandRegistry


class ExportCommand(BuiltinCommand):
    """Plugin for the 'export' command to set environment variables"""
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.startswith("export ")
    
    def execute(self, command):
        """Set an environment variable"""
        try:
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
                click.echo(click.style(f"Error: Invalid export format. Use export NAME=VALUE", fg="red"))
        except Exception as e:
            click.echo(click.style(f"Error setting environment variable: {str(e)}", fg="red"))
        
        return True


# Register the plugin with the registry
BuiltinCommandRegistry.register(ExportCommand())
