#!/usr/bin/env python3

import sys
import io
import os
import time

# Get command-line arguments
args = sys.argv[1:] if len(sys.argv) > 1 else []

# Process the help flag specially if present (before any imports)
if args and args[0] in ['-h', '--help']:
    # For help command, we need to replace the actual Python code execution
    # with a direct call to the help text, bypassing all the module loading
    click_help_text = """
Usage: jibberish.py [OPTIONS]

  Jibberish - An AI-powered Linux Shell

  This shell can be run in two modes:

  1. Interactive Mode - Launch the full interactive shell (default)

  2. Standalone Mode - Execute a single command using one of the options below

  STANDALONE MODE OPTIONS:
    -v, --version        Display version information
    -q, --question TEXT  Ask a general question (without needing the '?' prefix)
    -c, --command TEXT   Generate and execute a command (without needing the '#' prefix)
    -h, --help           Show this message and exit

  EXAMPLES:
    python jibberish.py                       # Start interactive shell
    python jibberish.py -v                    # Show version info
    python jibberish.py -q "What is Linux?"   # Ask a question
    python jibberish.py -c "list large files" # Generate and execute a command

Options:
  -v, --version        Display version information
  -q, --question TEXT  Ask a general question
  -c, --command TEXT   Generate and execute a command
  -h, --help           Show this message and exit.
"""
    print(click_help_text)
    sys.exit(0)
    
# Check if we're running in standalone mode with command line args
is_standalone_mode = len(sys.argv) > 1 and sys.argv[1] in ['-v', '--version', '-q', '--question', '-c', '--command']

# Redirect stdout before any other imports for regular standalone commands
if is_standalone_mode:
    # Redirect stdout before any other imports
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()  # Redirect to a string buffer

# Now do the rest of the imports
import builtins
builtins.JIBBERISH_STANDALONE_MODE = len(sys.argv) > 1 and sys.argv[1] in ['-v', '--version', '-q', '--question', '-c', '--command', '-h', '--help']

import chat
import click
import history
import readline
from contextlib import redirect_stdout
from executor import (
    execute_command,
    execute_chained_commands,
    is_built_in
)

def help():
    """
    Display help information for interactive mode
    """
    click.echo(click.style("Commands:", fg="blue"))
    click.echo(click.style("  <command>         - Execute the command", fg="blue"))
    click.echo(click.style("  #<command desc>   - Ask the AI to generate a command based on the user input", fg="blue"))
    click.echo(click.style("  ## <command desc> - Ask the AI to generate a commented command based on the user input", fg="blue"))
    click.echo(click.style("  ?<question>       - ask a general question", fg="blue")) 
    click.echo(click.style("  exit, quit, q     - Exit the shell", fg="blue"))
    click.echo(click.style("  help              - help menu", fg="blue"))

def version_standalone():
    """Run the version command in standalone mode"""
    # Import the version plugin
    from plugins.version_command import VersionPlugin
    version_plugin = VersionPlugin()
    version_plugin.execute("version")
    return True

def question_standalone(query):
    """Run the question command in standalone mode"""
    # Import the question plugin
    from plugins.question_command import QuestionPlugin
    question_cmd = QuestionPlugin()
    # Prepend the ? character
    formatted_query = f"?{query}"
    question_cmd.execute(formatted_query)
    return True

def ai_command_standalone(query):
    """Run the AI command plugin in standalone mode"""
    # Import the AI command plugin
    from plugins.ai_command import AICommandPlugin
    ai_cmd = AICommandPlugin()
    # Prepend the # character
    formatted_query = f"#{query}"
    result = ai_cmd.execute(formatted_query)
    
    # If the plugin returned a command to execute, run it
    if isinstance(result, tuple) and result[0] is False:
        command_to_execute = result[1]
        click.echo(click.style(f"\nExecuting generated command: {command_to_execute}", fg="green"))
        execute_command(command_to_execute)
    
    return True

class CustomContext(click.Context):
    """
    Custom context to override the default help formatter
    and set a maximum content width for the help text.
    """

    def make_formatter(self):
        from click import formatting
        return formatting.HelpFormatter(width=120)

@click.command(context_settings=dict(
    help_option_names=['-h', '--help'],
    max_content_width=120
))
@click.option('-v', '--version', is_flag=True, help='Display version information')
@click.option('-q', '--question', help='Ask a general question')
@click.option('-c', '--command', help='Generate and execute a command')
def cli(version, question, command):
    """
    Jibberish - An AI-powered Linux Shell

    This shell can be run in two modes:

    1. Interactive Mode - Launch the full interactive shell (default)

    2. Standalone Mode - Execute a single command using one of the options below

    \b
    STANDALONE MODE OPTIONS:
      -v, --version        Display version information
      -q, --question TEXT  Ask a general question (without needing the '?' prefix)
      -c, --command TEXT   Generate and execute a command (without needing the '#' prefix)
      -h, --help           Show this message and exit

    \b
    EXAMPLES:
      python jibberish.py                       # Start interactive shell
      python jibberish.py -v                    # Show version info
      python jibberish.py -q "What is Linux?"   # Ask a question
      python jibberish.py -c "list large files" # Generate and execute a command
    """
    # Restore stdout for any commands - we want to see the output from this point forward
    if 'original_stdout' in globals():
        sys.stdout = original_stdout
        
    # For help option, Click will automatically display the help text and exit
    # so we don't need additional handling for it
    
    # Check if we're running in standalone mode with command-line options
    if version or question or command:
        
        # Now execute the requested standalone command
        if version:
            return version_standalone()
        
        if question:
            return question_standalone(question)
        
        if command:
            return ai_command_standalone(command)
    
    # If no command-line options were provided, run in interactive mode
    help()

    # use a high temperature for the welcome message
    sentence = chat.ask_question("Give me only one short sentence Welcoming the user to Jibberish and introduce yourself and say your here to help.", 1.0)
    click.echo(click.style(f"\n{sentence}", fg="red", bold=True))

    # get the warn environment variable
    while True:
        try:
            # find the current directory
            current_directory = os.getcwd()

            prompt_text = click.style(f"{current_directory}# ", fg="green")
            command = input(prompt_text).strip()
            if command.lower() in ["exit", "quit", "q"]:
                # prompt the user to confirm exit
                choice = input(click.style("Are you sure you want to exit? [y/n]: ", fg="blue"))
                if choice.lower() == "y":
                    click.echo(click.style("Exiting Jibber Shell...", fg="blue"))
                    break
                else:
                    click.echo(click.style("Continuing in Jibber Shell...", fg="blue"))
                    continue
            elif command.lower() in ["help"]:
                help()
                continue
        except KeyboardInterrupt:
            # User pressed Ctrl+C
            print()  # Print a newline for better formatting
            click.echo(click.style("\nPress Ctrl+D or type 'exit' to exit the shell.", fg="yellow"))
            continue  # Continue the loop instead of exiting

        # Check if the command is a built-in command or requires special handling
        handled, new_command = is_built_in(command)
        
        # If a plugin returned a new command to process, update the command
        if not handled and new_command is not None:
            # Add the generated command to history as well (for AI-generated commands)
            # This ensures both the original request and the generated command are in history
            if command.startswith('#'):
                readline.add_history(new_command)
                # Apply history limit after adding a new command
                history.limit_history_size()
            
            command = new_command
            
            # Process the new command
            if '&&' in command or ';' in command:
                execute_chained_commands(command)
            else:
                # Check if the new command is a built-in
                new_handled, another_command = is_built_in(command)
                if not new_handled:
                    # Just execute the command directly
                    execute_command(command)
                elif another_command is not None:
                    # Handle nested command returns (rare case)
                    click.echo(click.style(f"Executing nested command: {another_command}", fg="blue"))
                    # For complex commands with nested quotes, use proper escaping
                    execute_command(another_command)
        # If command was fully handled by a built-in, do nothing more
        elif handled:
            pass
        # Check if the command contains && or ; for command chaining
        elif '&&' in command or ';' in command:
            execute_chained_commands(command)
        else:
            # we will execute the command in the case of a non-built-in command or
            execute_command(command)

if __name__ == "__main__":
    cli()