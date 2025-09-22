#!/usr/bin/env python3

import sys
import os
import socket


# Get command-line arguments - but these won't matter for pip installation
# as Click handles the args then
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
    -q, --question TEXT  Ask a question or perform tasks using tools - more tokens, less concise
    -c, --command TEXT   Ask to generate a command - less tokens, more concise
    -h, --help           Show this message and exit

  EXAMPLES:
    jibberish                      # Start interactive shell
    jibberish -v                   # Show version info
    jibberish -q "What is Linux?"  # Ask a question
    jibberish -c "list large files" # Generate and execute a command

Options:
  -v, --version        Display version information
  -q, --question TEXT  Ask a general question
  -c, --command TEXT   Generate and execute a command
  -h, --help           Show this message and exit.
"""
    print(click_help_text)
    sys.exit(0)

# Add the parent directory to sys.path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import app modules with absolute imports
from app import chat
import click
from app import history
import readline
from contextlib import redirect_stdout
from app.executor import (
    execute_command,
    execute_chained_commands,
    is_built_in
)
from app.utils import execute_command_with_built_ins, clear_readline_buffer

# Function to format the prompt string based on user configuration
def format_prompt(prompt_template, user, hostname, path):
    """
    Format the prompt string by replacing placeholders with actual values:
    %u: username
    %h: hostname
    %p: current path
    """
    formatted_prompt = prompt_template
    formatted_prompt = formatted_prompt.replace('%u', user)
    formatted_prompt = formatted_prompt.replace('%h', hostname)
    formatted_prompt = formatted_prompt.replace('%p', path)
    return formatted_prompt

def help():
    """
    Display help information for interactive mode
    """
    click.echo(click.style("Commands:", fg="blue"))
    click.echo(click.style("  <command>         - Execute the command", fg="blue"))
    click.echo(click.style("  #<command desc>   - Ask to generate a command - less tokens, more concise", fg="blue"))
    click.echo(click.style("  ?<question>       - Ask a question or perform tasks using tools - more tokens, less concise", fg="blue"))
    click.echo(click.style("  exit, quit, q     - Exit the shell", fg="blue"))
    click.echo(click.style("  help              - help menu", fg="blue"))

def version_standalone():
    """Run the version command in standalone mode"""
    # Import the version plugin
    from app.plugins.version_command import VersionPlugin
    version_plugin = VersionPlugin()
    
    # Execute the version command without silencing output
    version_plugin.execute("version")
    return True

def question_standalone(query):
    """Run the question command in standalone mode"""
    # Import the question plugin
    from app.plugins.question_command import QuestionPlugin
    question_cmd = QuestionPlugin()
    # Prepend the ? character
    formatted_query = f"?{query}"
    
    question_cmd.execute(formatted_query)
    return True

def ai_command_standalone(query):
    """Run the AI command plugin in standalone mode"""
    # Import the AI command plugin
    from app.plugins.ai_command import AICommandPlugin
    ai_cmd = AICommandPlugin()
    # Prepend the # character
    formatted_query = f"#{query}"
    
    # Generate the command - do not silence this part
    result = ai_cmd.execute(formatted_query)
    
    # If the plugin returned a command to execute, run it
    if isinstance(result, tuple) and result[0] is False:
        command_to_execute = result[1]
        execute_command(command_to_execute)
    
    return True

class CustomContext(click.Context):
    """
    Custom context to override the default help formatter
    and set a maximum content width for the help text.
    """

    def make_formatter(self):
        from click import formatting
        return formatting.HelpFormatter(width=180)

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
      jibberish                      # Start interactive shell 
      jibberish -v                   # Show version info
      jibberish -q "What is Linux?"  # Ask a question
      jibberish -c "list large files" # Generate and execute a command
    """
    # Determine if we're in standalone mode based on command-line arguments
    is_standalone = bool(version or question or command)
    
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

    while True:
        try:
            # find the current directory - handle stale file handle
            try:
                current_directory = os.getcwd()
            except (FileNotFoundError, OSError):
                # Current directory is stale/deleted - switch to HOME
                home_dir = os.getenv('HOME', os.path.expanduser('~'))
                click.echo(click.style(f"Warning: Current directory is invalid (stale file handle). Switching to home directory.", fg="yellow"))
                try:
                    os.chdir(home_dir)
                    current_directory = home_dir
                    click.echo(click.style(f"Changed working directory to: {home_dir}", fg="yellow"))
                except Exception as e:
                    # If we can't change to HOME, use HOME string for display
                    current_directory = home_dir
                    click.echo(click.style(f"Could not change to home directory: {e}", fg="red"))
            
            # get the $USER variable
            user = os.getenv('USER', 'user')
            # get the $HOSTNAME variable
            hostname = socket.gethostname()  # Use socket.gethostname() to retrieve the hostname

            homedir = os.getenv('HOME', current_directory)
            if homedir in current_directory:
                # Replace the home directory with ~
                current_directory = current_directory.replace(homedir, "~")
            
            # Get the configured prompt format or use the default
            default_prompt = "[jbrsh] %u@%h:%p$ "
            prompt_format = os.getenv('JIBBERISH_PROMPT', default_prompt)
            
            # Format the prompt using the template
            prompt_text = format_prompt(prompt_format, user, hostname, current_directory)
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

        # Use the centralized command execution logic that handles built-ins and chained commands
        success, result = execute_command_with_built_ins(command, original_command=command, add_to_history=True)

        # Always clear the readline buffer before the next prompt
        clear_readline_buffer()

def main():
    """Entry point for the package when installed via pip."""
    cli()

if __name__ == "__main__":
    main()