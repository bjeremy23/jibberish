#!/usr/bin/env python3

import chat
import click
import history
import os
from executor import (
    execute_command,
    execute_chained_commands,
    is_built_in
)

def help():
    """
    Display help information
    """
    click.echo(click.style("Commands:", fg="blue"))
    click.echo(click.style("  <command>         - Execute the command", fg="blue"))
    click.echo(click.style("  #<command desc>   - Ask the AI to generate a command based on the user input", fg="blue"))
    click.echo(click.style("  ## <command desc> - Ask the AI to generate a commented command based on the user input", fg="blue"))
    click.echo(click.style("  ?<question>       - ask a general question", fg="blue")) 
    click.echo(click.style("  exit, quit, q     - Exit the shell", fg="blue"))
    click.echo(click.style("  help              - help menu", fg="blue"))

@click.command()
def cli():
    """
    Jibberish CLI
    """
    click.echo(click.style("\n##############################################################################################", fg="blue"))
    sentence = chat.ask_question("give me only one sentence Welcoming the user to Jibberish shell")
    click.echo(click.style(f"# {sentence}", fg="red"))
    click.echo(click.style("# Type '<command>' to execute the command", fg="blue"))
    click.echo(click.style("# Type '#<command description>' to execute the command your looking for", fg="blue"))
    click.echo(click.style("# Type '## <command desc>' to generate a commented command based on the user input", fg="blue"))
    click.echo(click.style("# Type '?<question>' to ask a general question", fg="blue"))
    click.echo(click.style("# Type 'help' for a list of commands", fg="blue"))
    click.echo(click.style("# Type 'exit, quit, q' to exit", fg="blue"))
    click.echo(click.style("\n##############################################################################################", fg="blue"))
    # get the warn environment variable
    while True:
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

        # Check if the command is a built-in command or requires special handling
        handled, new_command = is_built_in(command)
        
        # If a plugin returned a new command to process, update the command
        if not handled and new_command is not None:
            command = new_command
            
            # Process the new command
            if '&&' in command:
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
        # Check if the command contains && for command chaining
        elif '&&' in command:
            execute_chained_commands(command)
        else:
            # we will execute the command in the case of a non-built-in command or
            execute_command(command)

if __name__ == "__main__":
    cli()