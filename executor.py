import os
import sys
import subprocess
import click
import chat
import history
import threading
import io
from built_ins import is_built_in


def transform_multiline(command_chain):
    """
    Transform multiline commands into proper single-line commands when appropriate
    """
    # Split the command chain into lines
    lines = command_chain.strip().split('\n')
    if len(lines) < 2:
        return command_chain
    
    # Check for SSH followed by a command pattern
    for i in range(len(lines) - 1):
        current_line = lines[i].strip()
        next_line = lines[i + 1].strip()
        
        # Detect SSH command pattern
        if current_line.startswith('ssh ') and not current_line.endswith('"') and not current_line.endswith("'"):
            # Get the SSH destination part
            ssh_parts = current_line.split()
            if len(ssh_parts) >= 2:
                # Combine the SSH command with the next command in quotes
                combined_command = f"{current_line} \"{next_line}\""
                
                # Replace the two lines with the combined command
                lines[i] = combined_command
                lines[i + 1] = ""  # Empty the second line
    
    # Remove empty lines and join the lines back
    return '\n'.join(line for line in lines if line)

def execute_shell_command(command):
    """
    Execute a shell command and return the output
    """

    # Check if the command is empty
    if not command.strip():
        return 0, "", ""
    
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
            # Use the simplest and most reliable approach: communicate() with a separate thread
            # for outputting lines as they come in
            from queue import Queue, Empty
            from threading import Thread
            
            # Queue for collecting output
            stdout_queue = Queue()
            stderr_queue = Queue()
            
            # Start process with pipes
            process = subprocess.Popen(
                command,
                shell=True,
                executable='/bin/bash',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                text=True
            )
            
            # Function to read from pipes and put lines into queues
            def reader(pipe, queue):
                try:
                    with pipe:
                        for line in iter(pipe.readline, ''):
                            queue.put(line)
                finally:
                    queue.put(None)  # Signal that reading is done
                    
            # Start reader threads
            Thread(target=reader, args=[process.stdout, stdout_queue], daemon=True).start()
            Thread(target=reader, args=[process.stderr, stderr_queue], daemon=True).start()
            
            # Collect all output
            collected_stdout = []
            collected_stderr = []
            
            # Process output from both queues until both are done
            stdout_done = False
            stderr_done = False
            
            while not (stdout_done and stderr_done):
                # Check stdout
                try:
                    stdout_line = stdout_queue.get(block=False)
                    if stdout_line is None:
                        stdout_done = True
                    else:
                        click.echo(stdout_line, nl=False)
                        sys.stdout.flush()
                        collected_stdout.append(stdout_line)
                except Empty:
                    pass
                
                # Check stderr
                try:
                    stderr_line = stderr_queue.get(block=False)
                    if stderr_line is None:
                        stderr_done = True
                    else:
                        click.echo(click.style(stderr_line, fg="red"), nl=False)
                        sys.stdout.flush()
                        collected_stderr.append(stderr_line)
                except Empty:
                    pass
                
                # If either queue is waiting for more output, give the process some time to produce it
                if not (stdout_done and stderr_done):
                    # Sleep a tiny bit to avoid busy waiting
                    import time
                    time.sleep(0.01)
                    
                    # Check if process is done and both queues are empty
                    if process.poll() is not None and stdout_queue.empty() and stderr_queue.empty():
                        # Double check by calling communicate() to get any remaining output
                        final_stdout, final_stderr = process.communicate()
                        
                        if final_stdout:
                            click.echo(final_stdout, nl=False)
                            collected_stdout.append(final_stdout)
                        if final_stderr:
                            click.echo(click.style(final_stderr, fg="red"), nl=False)
                            collected_stderr.append(final_stderr)
                        
                        break
            
            # Wait for process to finish and get return code
            return_code = process.wait()
            
            # Join all the output
            stdout_content = ''.join(collected_stdout)
            stderr_content = ''.join(collected_stderr)
            
            return return_code, stdout_content, stderr_content
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
    if warn:
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
                # if IGNORE_ERROR is set, ignore the error
                ignore_errors = os.environ.get("IGNORE_ERRORS", "").lower()
                if ignore_errors not in ["true", "yes", "1"]:
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

def split_commands_respect_quotes(command_chain):
    """
    Split command chain on '&&' while respecting quotes.
    This ensures that '&&' inside quotes won't be treated as command separators.
    """
    commands = []
    current_cmd = ""
    in_single_quote = False
    in_double_quote = False
    i = 0
    
    while i < len(command_chain):
        char = command_chain[i]
        
        # Handle quotes
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current_cmd += char
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current_cmd += char
        # Handle potential command separator
        elif char == '&' and not in_single_quote and not in_double_quote and i + 1 < len(command_chain) and command_chain[i + 1] == '&':
            # Found '&&' outside quotes - split the command
            commands.append(current_cmd.strip())
            current_cmd = ""
            i += 1  # Skip the second &
        else:
            current_cmd += char
        
        i += 1
    
    # Add the last command
    if current_cmd.strip():
        commands.append(current_cmd.strip())
    
    return commands

def execute_chained_commands(command_chain):
    """
    Execute multiple commands separated by &&
    """
    # First transform any multiline commands into proper format
    command_chain = transform_multiline(command_chain)
    
    # Split commands respecting quotes
    commands = split_commands_respect_quotes(command_chain)
    
    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue
    
        # Check if this is a built-in command
        handled, new_command = is_built_in(cmd)
        
        if handled:
            # Built-in command was executed, continue to next command
            pass  # Don't return, let the next command execute
        elif new_command is not None:
            # A new command was returned (e.g., from history or AI), execute it
            if '&&' in new_command:
                # If the new command itself contains chains, process them
                execute_chained_commands(new_command)
            else:
                # Execute the new command
                execute_command(new_command)
        else:
            # Execute external command
            execute_command(cmd)
