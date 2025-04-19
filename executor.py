import os
import subprocess
import click
import chat
import history
from built_ins import is_built_in

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
        return -1, "", "Aborted by user"
    except Exception as e:
        return -1, "", str(e)

def execute_command(command):
    """
    Execute a command and handle warnings and errors
    """
    # check to see if the command starts with anything in the WARNLIST env variable
    # if it does, ask the user if they want to execute the command
    warn_list = os.environ.get("WARN_LIST", "").split(",")
    warn = False
    for item in warn_list:
        if command.startswith(item.strip()) or item.strip() == "all":
            # if the command is in the warn_list,  or 'all' exists
            # set warn to True
            warn = True
            break
    
    # if the command is in the warn_list and the command does not contain '-f', 
    # ask the user if they want to execute the command
    if warn and '-f' not in command:
        choice = input(click.style(f"Are you sure you want to execute this command? [y/n]: ", fg="blue"))
        if choice.lower() != "y":
            click.echo(click.style(f"Command not executed", fg="red"))
            return
    
    # Check if this is an SSH-related command
    ssh_commands = ["ssh", "ssh-keygen", "ssh-copy-id", "ssh-add", "scp", "sftp", "rsync"]
    is_ssh_command = any(command.strip().startswith(cmd) for cmd in ssh_commands)
        
    # execute the command. if it is not successful print the error message
    try:
        returncode, output, error = execute_shell_command(command)
        if returncode == -1:
            click.echo(click.style(f"{error}", fg="red"))
        elif error:
            # For SSH commands with successful return code, treat stderr as normal output 
            # since they often output informational messages to stderr
            if is_ssh_command and returncode == 0:
                click.echo(error)
            # For other commands with stderr output, show as error and offer to explain
            elif "command not found" not in error:
                click.echo(click.style(error, fg="red"), nl=False)
                # have the user choose to explain why the command failed
                choice = input(click.style(f"\nMore information about error? [y/n]: ", fg="blue"))
                if choice.lower() == "y":
                    why_failed = chat.ask_why_failed(command, error)
                    if why_failed is not None:
                        click.echo(click.style(f"{why_failed}", fg="red"))
                    else:
                        click.echo(click.style(f"No explanation provided.", fg="red"))
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))

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
