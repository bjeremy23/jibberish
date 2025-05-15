"""
AI command generation plugin.
"""
import click
import os
from app import chat
from ..plugin_system import BuiltinCommand, BuiltinCommandRegistry


class AICommandPlugin(BuiltinCommand):
    """Plugin for AI command generation with '#' prefix"""
    
    # Plugin attributes
    plugin_name = "ai_command"  # Name of the plugin
    is_required = True  # AI command is a required plugin
    is_enabled = True  # Always enabled since it's required
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.startswith("#")
    
    def execute(self, command):
        """Generate and execute a command using AI"""
        # Remove the leading '#' from the command
        query = command[1:]
        
        # if the query starts with another '#', call ask_ai on the rest of the string, 
        # but add a comment to the generated response and return the response without executing it
        if query.startswith("#"):
            # Remove the leading '#' from the query
            query = query[1:]
            # Call ask_ai on the rest of the string
            generated_response = chat.ask_ai(query)
            # Add a comment to the generated response
            click.echo(click.style(f"# {generated_response}", fg="blue"))
            return True
        # Check if the command is a chai
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
            
            # Only consider it executable if the line doesn't start with a comment
            if not actual_command.startswith('#'):
                to_execute = actual_command
            else:
                # If the last line is also a comment, don't execute anything
                click.echo(click.style("No executable command found in AI response", fg="yellow"))
                return True
        
        # If it's a single-line response, check if it's an actual command or just a comment
        elif not generated_response.strip().startswith('#'):
            # It's a single line command
            to_execute = generated_response.strip()
        else:
            # It's just a comment, don't execute
            click.echo(click.style("AI response was a comment, not executing", fg="yellow"))
            return True
            
        # Check if we should prompt before executing
        prompt_setting = os.environ.get('PROMPT_AI_COMMANDS', '').lower()
        if prompt_setting in ('true', 'always', 'yes', '1'):
            choice = input(click.style("Execute this command? [y/n]: ", fg="blue"))
            if choice.lower() != 'y':
                click.echo(click.style("Command execution cancelled", fg="yellow"))
                return True
        
        # Execute the command
        if to_execute:
            click.echo(click.style(f"Executing: {to_execute}", fg="green"))
            return False, to_execute
            
        return True


# Register the plugin with the registry
BuiltinCommandRegistry.register(AICommandPlugin())