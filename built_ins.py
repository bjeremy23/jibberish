import os
import subprocess
import click
import history

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

def cd(command):
    """
    Change the current directory
    """
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

def export(command):
    """
    Export an environment variable
    """
    # Handle environment variable setting
    try:
        # Strip the 'export ' prefix
        var_assignment = command[7:].strip()
        
        # Check if there's an assignment
        if '=' in var_assignment:
            # Split at the first equals sign
            var_name, var_value = var_assignment.split('=', 1)
            var_name = var_name.strip()
            
            # Handle quoted values
            if var_value.startswith('"') and var_value.endswith('"'):
                var_value = var_value[1:-1]
            elif var_value.startswith("'") and var_value.endswith("'"):
                var_value = var_value[1:-1]
            
            # Set the environment variable
            os.environ[var_name] = var_value
                    
            # Print the variable name and value
            click.echo(click.style(f"Environment variable {var_name}={var_value}", fg="green"))
        else:
            click.echo(click.style(f"Error: Invalid export format. Use export NAME=VALUE", fg="red"))
    except Exception as e:
        click.echo(click.style(f"Error setting environment variable: {str(e)}", fg="red"))

def ssh_command(command):
    """
    Execute an SSH command with proper handling of remote command execution.
    Supports the format: ssh host "remote_command1 && remote_command2"
    """
    try:
        # Check for the case of "ssh host && command1 && command2" which should be converted to "ssh host "command1 && command2""
        if " && " in command:
            # Split at the first occurrence of && to separate SSH part from commands
            parts = command.split(" && ")
            first_part = parts[0].strip()
            first_part_split = first_part.split(None, 1)  # Split SSH command into ['ssh', 'host']
            
            if len(first_part_split) >= 2 and first_part_split[0] == 'ssh':
                # This is the pattern "ssh host && command1 && command2", convert to correct format
                host = first_part_split[1]
                
                # Join all commands after the SSH part
                all_commands = " && ".join(parts[1:])
                
                click.echo(click.style("Converting command to proper SSH remote execution format", fg="yellow"))
                click.echo(click.style(f"Host: {host}, Commands: {all_commands}", fg="yellow"))
                command = f"ssh {host} \"{all_commands}\""
        
        # Now parse the SSH command normally
        parts = command.split(None, 2)  # Split into max 3 parts: 'ssh', 'host', 'commands'
        
        if len(parts) < 2:
            click.echo(click.style("Usage: ssh <host> [\"command1 && command2 ...\"]", fg="red"))
            return
            
        # Check if this is an interactive SSH session or a command execution
        interactive = True  # Default to interactive mode
        host_part = parts[1]
        remote_cmd = None
        
        # If there are commands specified after the host
        if len(parts) >= 3:
            remote_cmd = parts[2]
            interactive = False  # There's a command, so not interactive
            
            # If the command isn't already quoted, quote it
            if not (remote_cmd.startswith('"') and remote_cmd.endswith('"')) and not (remote_cmd.startswith("'") and remote_cmd.endswith("'")):
                remote_cmd = f'"{remote_cmd}"'
        
        # Handle the command differently based on interactive mode
        if interactive:
            # Interactive SSH session - just connect to the host
            full_command = f"{parts[0]} {host_part}"
            click.echo(click.style(f"Starting SSH session to {host_part}...", fg="blue"))
        else:
            # Remote command execution - run the command on the host
            full_command = f"{parts[0]} {host_part} {remote_cmd}"
            click.echo(click.style(f"Executing on {host_part}: {remote_cmd}", fg="blue"))
            
        # Execute the SSH command
        result = subprocess.run(
            full_command,
            shell=True,
            text=True
        )
        
        return result.returncode == 0
    except Exception as e:
        click.echo(click.style(f"SSH error: {str(e)}", fg="red"))
        return False

def is_built_in(command):
    """
    Check if the command is a built-in command
    """
    if command.lower() in ["history", "h"]:
        history.list_history()
        return True
    elif command.startswith("cd"):
        cd(command)
        return True
    elif command.startswith("export "):
        export(command)
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
    elif command.startswith("ssh "):
        ssh_command(command)
        return True

    return False
