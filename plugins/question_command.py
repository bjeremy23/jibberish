"""
AI question answering plugin.
"""
import click
import chat
from plugin_system import BuiltinCommand, BuiltinCommandRegistry


class QuestionPlugin(BuiltinCommand):
    """Plugin for answering general questions with '?' prefix"""
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.startswith("?")
    
    def execute(self, command):
        """Ask the AI a general question"""
        # Remove the leading '?' from the command
        query = command[1:]
        
        # Ask the question
        response = chat.ask_question(query)
        
        # Print the response
        click.echo(click.style(f"{response}", fg="blue"))
        
        return True


# Register the plugin with the registry
BuiltinCommandRegistry.register(QuestionPlugin())
