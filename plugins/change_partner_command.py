"""
Change chat partner plugin.
"""
import click
import chat
from plugin_system import BuiltinCommand, BuiltinCommandRegistry


class ChangePartnerPlugin(BuiltinCommand):
    """Plugin for changing chat partners with ':)' prefix"""
    
    # Plugin attributes
    plugin_name = "change_partner_command"  # Name of the plugin
    is_required = True  # Change partner command is optional
    is_enabled = True  # Enabled by default, can be overridden by environment variable
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.startswith(":)")
    
    def execute(self, command):
        """Change the chat partner"""
        # Remove the leading ':)' from the command
        partner_name = command[2:]
        
        # Change the partner
        chat.change_partner(partner_name)
        
        # Print confirmation
        click.echo(click.style(f"Now talking with {partner_name}", fg="blue"))
        
        return True


# Register the plugin with the registry
BuiltinCommandRegistry.register(ChangePartnerPlugin())
