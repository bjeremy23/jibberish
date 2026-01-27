"""
Explain Command Plugin

Provides a lightweight command to explain any Linux command without executing it.
Uses a focused AI prompt to explain command syntax, flags, and usage.

Usage:
    explain <command>     - Explain the command and its flags
    explain tar -xzvf     - Explain tar with those specific flags
"""

import click
import os
from app.plugin_system import BuiltinCommand, BuiltinCommandRegistry


class ExplainCommandPlugin(BuiltinCommand):
    """Plugin to explain Linux commands using AI."""
    
    # Plugin attributes
    plugin_name = "explain_command"
    is_required = False
    is_enabled = True
    
    def can_handle(self, command: str) -> bool:
        """Check if this plugin should handle the command."""
        cmd = command.strip().lower()
        return cmd.startswith('explain ') or cmd == 'explain'
    
    def execute(self, command: str) -> tuple:
        """
        Explain a Linux command.
        
        Returns:
            tuple: (handled: bool, new_command: str or None)
        """
        # Extract the command to explain (remove 'explain ' prefix)
        parts = command.strip().split(maxsplit=1)
        
        if len(parts) < 2:
            click.echo(click.style("Usage: explain <command>", fg="yellow"))
            click.echo("Example: explain tar -xzvf archive.tar.gz")
            return (True, None)
        
        cmd_to_explain = parts[1].strip()
        
        if not cmd_to_explain:
            click.echo(click.style("Usage: explain <command>", fg="yellow"))
            return (True, None)
        
        # Call the explain AI function
        explanation = explain_command_ai(cmd_to_explain)
        
        if explanation:
            click.echo()
            click.echo(click.style(f"Command: ", fg="blue", bold=True) + click.style(cmd_to_explain, fg="white", bold=True))
            click.echo(click.style("-" * 50, fg="blue"))
            click.echo(explanation)
            click.echo()
        else:
            click.echo(click.style("Unable to explain command. Please try again.", fg="red"))
        
        return (True, None)


def explain_command_ai(command: str) -> str:
    """
    Use AI to explain a Linux command in a lightweight, focused way.
    
    This is a simpler call than ask_question - no tools, no chat history,
    just a focused explanation of the command syntax.
    
    Args:
        command: The Linux command to explain
        
    Returns:
        str: The explanation of the command
    """
    from app import api
    from app.utils import is_debug_enabled
    
    # Focused system prompt for command explanation
    system_prompt = """You are a Linux command explainer. Given a command, explain it concisely:

1. First, briefly describe what the base command does (one line)
2. Then list each flag/option with a short explanation
3. If there are arguments (like filenames), explain their role

Format the output like this:
<base command> - <brief description>

Flags:
  -x  Extract files
  -z  Filter through gzip
  -v  Verbose output

Arguments:
  <filename>  The archive file to process

Keep explanations brief and practical. Focus on what the command DOES, not theory."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Explain this command: {command}"}
    ]
    
    try:
        # Use a low temperature for factual, consistent responses
        response = api.client.chat.completions.create(
            model=api.model,
            messages=messages,
            temperature=0.2,
            max_tokens=500  # Keep responses concise
        )
        
        if response and response.choices:
            return response.choices[0].message.content.strip()
        return None
        
    except Exception as e:
        if is_debug_enabled():
            click.echo(click.style(f"Error explaining command: {e}", fg="red"))
        return None


# Register the plugin
BuiltinCommandRegistry.register(ExplainCommandPlugin())
