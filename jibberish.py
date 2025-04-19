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
    click.echo(click.style("  !<index> - Get the command from the history", fg="blue"))
    click.echo(click.style("  #<command> - Ask the AI to generate a command based on the user input", fg="blue"))
    click.echo(click.style("  ?<question> - ask a general question", fg="blue")) 
    click.echo(click.style("  cd <directory> - Change the current directory", fg="blue"))
    click.echo(click.style("  pushd <directory> - Push the current directory to the stack and change to the new directory", fg="blue"))
    click.echo(click.style("  popd - Pop the directory from the stack and change to that directory", fg="blue"))
    click.echo(click.style("  history, h - List the command history", fg="blue"))
    click.echo(click.style("  exit, quit, q - Exit the shell", fg="blue"))
    click.echo(click.style("  help - help menu", fg="blue"))

@click.command()
def cli():
    """
    Jibberish CLI
    """
    click.echo(click.style("Welcome to Jibber Shell", fg="blue"))
    click.echo(click.style("Type '<command>' to execute the command", fg="blue"))
    click.echo(click.style("Type '#<command description>' to execute the command your looking for", fg="blue"))
    click.echo(click.style("Type '?<question>' to ask a general question", fg="blue"))
    click.echo(click.style("Type 'help' for a list of commands", fg="blue"))
    click.echo(click.style("Type 'exit, quit, q' to exit", fg="blue"))
    
    # get the warn environment variable
    while True:
        # find the current directory
        current_directory = os.getcwd()

        prompt_text = click.style(f"{current_directory}# ", fg="green")
        command = input(prompt_text).strip()
        if command.lower() in ["exit", "quit", "q"]:
            break
        elif command.lower() in ["help"]:
            help()
            continue

        # if the command starts with '!', get the command from the history
        # The history could return a command starting with '#' or '?'
        if command.startswith("!"):
            command = history.get_history(command)
            if command is None:
                continue
        
        # if the command starts with '#', ask the AI to generate a command
        # or if the command starts with '?', ask a general question
        if command.startswith("#"):
            #remove the leading '#' from the command
            command = chat.ask_ai(command[1:])
            # print the command
            click.echo(click.style(f"{command}", fg="blue"))
            execute_command(command)
        elif command.startswith("?"):
            #remove the leading '?' from the command
            response = chat.ask_question(command[1:])
            # print the response
            click.echo(click.style(f"{response}", fg="blue"))
        elif command.startswith(":)"):
            #remove the leading ':)' from the command
            chat.change_partner(command[2:])
            # print who you are talking with
            click.echo(click.style(f"Now talking with {command[2:]}", fg="blue"))
        # Check if the command contains && for command chaining
        elif '&&' in command:
            execute_chained_commands(command)
        # check if the command is a built-in command
        elif is_built_in(command):
            pass
        else:
            # we will execute the command in the case of a non-built-in command or
            execute_command(command)

if __name__ == "__main__":
    cli()