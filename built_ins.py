import os
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

    return False
