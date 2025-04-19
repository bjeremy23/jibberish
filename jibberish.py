import chat, click, os, subprocess, history

def help():
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

# Directory stack
dir_stack = []

def pushd(directory):
    """
    Push the current directory to the stack and change to the new directory
    """
    global dir_stack
    current_directory = os.getcwd()
    dir_stack.append(current_directory)
    
    # Expand tilde to home directory
    expanded_dir = os.path.expanduser(directory)
    os.chdir(expanded_dir)

    # join the directories in reverse order
    dirs = ' '.join(map(str, dir_stack[::-1]))
    click.echo(f"{os.getcwd()} {dirs}")

def popd():
    """
    Pop the directory from the stack and change to that directory
    """
    global dir_stack
    if dir_stack:
        directory = dir_stack.pop()
        os.chdir(directory)
         
        dirs = ' '.join(map(str, dir_stack[::-1]))
        click.echo(f"{os.getcwd()} {dirs}")
    else:
        click.echo(click.style("Directory stack is empty", fg="red"))

def execute_shell_command(command):
    """
    Execute a shell command and return the output
    """

    # Check if the command is empty
    if not command.strip():
        return 0, "", ""
    
    #transform the command
    command = transform(command)
    
    # Check if command is in the INTERACTIVE_LIST environment variable
    # Default list if not set: "vi,vim,nano,emacs,less,more,top,htop"
    default_interactive = "vi,vim,nano,emacs,less,more,top,htop,tail -f,watch"
    interactive_list = os.environ.get("INTERACTIVE_LIST", default_interactive)
    interactive_commands = [cmd.strip() for cmd in interactive_list.split(",") if cmd.strip()]  # Clean up the list
    
    # Check if the command is interactive - check for interactive commands anywhere in the pipeline
    # This handles cases like "cat file | more" where "more" is not the first command
    is_interactive = False
    
    # First check if the main command is interactive
    cmd_name = command.strip().split()[0] if command.strip().split() else ""
    if any(cmd_name == ic or cmd_name.endswith('/' + ic) for ic in interactive_commands):
        is_interactive = True
    
    # If not, check if any part of a pipeline is interactive
    if not is_interactive and '|' in command:
        pipeline_parts = command.split('|')
        for part in pipeline_parts:
            part_cmd = part.strip().split()[0] if part.strip().split() else ""
            if any(part_cmd == ic or part_cmd.endswith('/' + ic) for ic in interactive_commands):
                is_interactive = True
                break
    
    try:
        if is_interactive:
            # For interactive applications, don't capture output and use os.system
            # This gives the command direct access to the terminal
            return_code = os.system(command)
            return return_code, "", ""
        else:
            # For non-interactive commands, use subprocess.run as before
            result = subprocess.run(
                command,
                shell=True,
                executable='/bin/bash',
                text=True,
                capture_output=True
            )
            
            # Display stdout
            if result.stdout:
                click.echo(result.stdout, nl=False)
                
            # Display stderr
            if result.stderr:
                click.echo(click.style(result.stderr, fg="red"), nl=False)
                
            return result.returncode, result.stdout, result.stderr
    except KeyboardInterrupt:
        click.echo(click.style("\nCommand interrupted by user", fg="red"))
        return -1, "", "Aborted by user"
    except Exception as e:
        click.echo(click.style(f"\nError executing command: {str(e)}", fg="red"))
        return -1, "", str(e)

def execute_command(command):

    # check to see if the command starts with anything in the WARNLIST env variable
    # if it does, ask the user if they want to execute the command
    warn_list = os.environ.get("WARN_LIST", "").split(",")
    warn = False
    for item in warn_list:
        if command.startswith(item.strip()):
            warn = True
            break
    
    # if the command is in the warn_list and the command does not contain '-f', 
    # ask the user if they want to execute the command
    if warn and '-f' not in command:
        choice = input( click.style(f"Are you sure you want to execute this command? [y/n]: ", fg="blue") )
        if choice.lower() != "y":
            click.echo( click.style(f"Command not executed", fg="red") )
            return
        
    # execute the command. if it is not successful print the error message
    try:
        returncode, output, error = execute_shell_command(command)
        if returncode == -1:
            click.echo( click.style(f"{error}", fg="red") )
        elif error and "command not found" not in error:
            # have the user choose to explain why the command failed
            choice = input( click.style(f"more information? [y/n]: ", fg="blue") )
            if choice.lower() == "y":
                why_failed = chat.ask_why_failed(command, error)
                if why_failed is not None:
                    click.echo( click.style(f"{why_failed}", fg="red") )
                else:
                    click.echo( click.style(f"No explanation provided.", fg="red") )
    except Exception as e:
        click.echo( click.style(f"Error: {e}", fg="red") )

def execute_chained_commands(command_chain):
    """
    Execute multiple commands separated by &&
    """
    commands = command_chain.split('&&')
    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue
            
        # Check if this is a built-in command
        if is_built_in(cmd):
            # Built-in command was executed, continue to next command
            pass  # Don't return, let the next command execute
        else:
            # Execute external command
            execute_command(cmd)

def is_built_in(command):
    """
    Check if the command is a built-in command
    """
    if command.lower() in ["history", "h"]:
        history.list_history()
        return True
    elif command.startswith("cd"):
        # Extract the path part after 'cd'
        path_part = command[2:].strip()
        
        # If no path provided (just 'cd'), go to home directory
        if not path_part:
            home_dir = os.path.expanduser("~")
            os.chdir(home_dir)
        else:
            path = os.path.expanduser(path_part)
            if os.path.isfile(path):
                click.echo(click.style(f"Error: '{path}' is a file, not a directory", fg="red"))
            else:
                try:
                    os.chdir(path)
                except FileNotFoundError:
                    click.echo(click.style(f"Error: No such directory: '{path}'", fg="red"))
                except PermissionError:
                    click.echo(click.style(f"Error: Permission denied: '{path}'", fg="red"))
                except Exception as e:
                    click.echo(click.style(f"Error: {str(e)}", fg="red"))
        return True
    elif command.startswith("pushd"):
        try:
            directory = command.split()[1]
            pushd(directory)
        except IndexError:
            click.echo(click.style("Usage: pushd <directory>", fg="red"))
        return True
    elif command.startswith("popd"):
        popd()
        return True

    return False

def transform(command):
    """
    Transform the command
    """
    # Transformations
    if command.strip() == "ls" or command.strip().startswith("ls ") and not any(flag in command for flag in ["-l", "-1", "-C", "-x", "-m"]):
        # Add -C flag for columnar output
        command = command.replace("ls", "ls -CF", 1)
    elif command.startswith('rm ') and '-f' not in command:
        # For interactive commands, use subprocess.run instead of Popen to allow direct interaction
        # Add '-f' flag to rm commands to avoid interactive prompts
        command = command.replace('rm ', 'rm -f ', 1)
    
    return command

@click.command()
def cli():
    """
    Jibberish CLI
    """
    click.echo(click.style("Welcome to Jibber Shell", fg="blue"))
    click.echo(click.style("Type 'help' for a list of commands", fg="blue"))
    click.echo(click.style("Type 'exit, quit, q' to exit", fg="blue"))
    click.echo(click.style("Type 'h' to see the command history", fg="blue"))
    click.echo(click.style("Type '#<command description>' to execute the command your looking for", fg="blue"))
    click.echo(click.style("Type '?<question>' to ask a general question", fg="blue"))
    click.echo(click.style("Type '!' to get the command from the history", fg="blue"))
    
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