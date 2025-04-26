"""
History retrieval plugin.
"""
import click
import history
from plugin_system import BuiltinCommand, BuiltinCommandRegistry


class HistoryRetrievalPlugin(BuiltinCommand):
    """Plugin for retrieving commands from history with '!' prefix"""
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.startswith("!")
    
    def execute(self, command):
        """Retrieve a command from history"""
        # Get the command from history
        retrieved_command = history.get_history(command)
        
        # If no command was found, return True to indicate that we handled it
        if retrieved_command is None:
            return True
        
        # Check if the retrieved command is an AI command request (starts with '#')
        if retrieved_command.startswith("#"):
            # This is a request for AI command generation
            # We need to invoke the AI command plugin directly rather than returning the raw command
            
            # Import and use the AI command plugin directly from the registry
            from plugin_system import BuiltinCommandRegistry
            try:
                # Get all registered plugins from the registry
                for plugin in BuiltinCommandRegistry._plugins:
                    # Find the plugin that handles commands starting with '#'
                    if plugin.can_handle(retrieved_command):
                        # Execute the AI plugin directly
                        return plugin.execute(retrieved_command)
            except Exception as e:
                click.echo(click.style(f"Error processing AI command: {str(e)}", fg="red"))
                return True
                
        # Otherwise, return False to let the main loop process the retrieved command
        # This is a special case where we actually want to return False even though
        # we handled the request because we want the main loop to process the retrieved command
        return False, retrieved_command


# Register the plugin with the registry
BuiltinCommandRegistry.register(HistoryRetrievalPlugin())
