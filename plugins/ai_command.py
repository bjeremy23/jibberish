"""
AI command generation plugin.
"""
import click
import chat
import importlib
from plugin_system import BuiltinCommand, BuiltinCommandRegistry


class AICommandPlugin(BuiltinCommand):
    """Plugin for AI command generation with '#' prefix"""
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.startswith("#")
    
    def execute(self, command):
        """Generate and execute a command using AI"""
        # Remove the leading '#' from the command
        query = command[1:]
        
        # Ask the AI to generate a command
        generated_response = chat.ask_ai(query)
        
        # Display the full response
        click.echo(click.style(f"{generated_response}", fg="blue"))
        
        # Check if the response has multiple lines (comment + command structure)
        if '\n' in generated_response:
            lines = generated_response.strip().split('\n')
            # Extract the last line as the actual command to execute
            # (assuming comment lines come first and the actual command is last)
            actual_command = lines[-1].strip()
            
            # Only execute if the line doesn't start with a comment
            if not actual_command.startswith('#'):
                click.echo(click.style(f"Executing: {actual_command}", fg="green"))
                return False, actual_command
            else:
                # If the last line is also a comment, don't execute anything
                click.echo(click.style("No executable command found in AI response", fg="yellow"))
                return True
        
        # If it's a single-line response, check if it's an actual command or just a comment
        elif not generated_response.strip().startswith('#'):
            # It's a single line command, return it for execution
            return False, generated_response
        else:
            # It's just a comment, don't execute
            click.echo(click.style("AI response was a comment, not executing", fg="yellow"))
            return True


# Register the plugin with the registry
BuiltinCommandRegistry.register(AICommandPlugin())
