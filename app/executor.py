import os
import sys
import subprocess
import click

# Add the parent directory to sys.path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import chat
from app.built_ins import is_built_in

# Forward declaration for circular reference

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

def split_commands_respect_semicolons(command_chain):
    """
    Split command chain on ';' while respecting quotes and escapes.
    This ensures that ';' inside quotes or escaped with '\;' won't be treated as command separators.
    """
    commands = []
    current_cmd = ""
    in_single_quote = False
    in_double_quote = False
    i = 0
    
    while i < len(command_chain):
        char = command_chain[i]
        
        # Handle escape sequences
        if char == '\\' and i + 1 < len(command_chain):
            # Include both the backslash and the next character
            current_cmd += char  # Add the backslash
            i += 1  # Move to next character
            if i < len(command_chain):
                current_cmd += command_chain[i]  # Add the escaped character
        # Handle quotes
        elif char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current_cmd += char
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current_cmd += char
        # Handle semicolon separator
        elif char == ';' and not in_single_quote and not in_double_quote:
            # Found ';' outside quotes - split the command
            commands.append(current_cmd.strip())
            current_cmd = ""
        else:
            current_cmd += char
        
        i += 1
    
    # Add the last command
    if current_cmd.strip():
        commands.append(current_cmd.strip())
    
    return commands

def transform_multiline(command_chain):
    """
    Transform multiline commands into proper single-line commands when appropriate
    """
    # Guard against potentially problematic inputs
    if not isinstance(command_chain, str):
        return str(command_chain)
        
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

def is_cmd_interactive(command):
    """
    Check if the command is interactive based on the INTERACTIVE_LIST environment variable
    """

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
    
    return is_interactive

def expand_aliases(command):
    """ Expand aliases if present"""
    try:
        # First try to import the alias plugin
        from app.plugins.alias_command import get_aliases
        
        # Get all currently defined aliases
        aliases = get_aliases()
        
        # Check if the command contains pipes
        if '|' in command:
            # For piped commands, handle each part separately
            pipe_parts = [part.strip() for part in command.split('|')]
            expanded_parts = []
            
            # Process each command in the pipeline
            for part in pipe_parts:
                part_expanded = False
                part_parts = part.strip().split()
                
                if part_parts and part_parts[0] in aliases:
                    # Replace the alias with its definition
                    alias_value = aliases[part_parts[0]]
                    
                    # Check for recursive alias expansion - avoid expanding if alias value starts with same name
                    if alias_value.startswith(f"{part_parts[0]} "):
                        # This is a problematic pattern like "ls='ls -CF --color=always'"
                        # Only use the options part of the alias to avoid recursive expansion
                        alias_options = alias_value[len(part_parts[0]):].strip()
                        if len(part_parts) > 1:
                            # Alias with arguments
                            expanded_part = f"{part_parts[0]} {alias_options} {' '.join(part_parts[1:])}"
                        else:
                            # Alias with no arguments
                            expanded_part = f"{part_parts[0]} {alias_options}"
                    else:
                        # Normal alias that doesn't cause recursive expansion
                        if len(part_parts) > 1:
                            # Alias with arguments
                            expanded_part = f"{alias_value} {' '.join(part_parts[1:])}"
                        else:
                            # Alias with no arguments
                            expanded_part = alias_value
                    
                    expanded_parts.append(expanded_part)
                    part_expanded = True
                
                if not part_expanded:
                    # If no alias was found, keep the original part
                    expanded_parts.append(part)
            
            # Join the expanded parts back with pipe symbols
            expanded_command = ' | '.join(expanded_parts)
            
            # Update the command with the expanded alias
            if expanded_command != command:
                command = expanded_command
        else:
            # For non-piped commands, check if it starts with an alias
            command_parts = command.strip().split()
            if command_parts and command_parts[0] in aliases:
                # Replace the alias with its definition
                alias_value = aliases[command_parts[0]]
                
                # Replace only the first word (the command) with the alias value
                if len(command_parts) > 1:
                    # Alias with arguments
                    expanded_command = f"{alias_value} {' '.join(command_parts[1:])}"
                else:
                    # Alias with no arguments
                    expanded_command = alias_value
                
                # Update the command with the expanded alias
                command = expanded_command
    except (ImportError, AttributeError):
        # If there's an error importing the plugin or getting aliases, just continue
        pass

    return command

def run_in_background(command):
    """
    Run a command in the background
    """
    # Remove the & at the end - we'll handle backgrounding ourselves
    actual_command = command.rstrip('&').strip()
    
    # Import the job control module to register the background process
    try:
        from app.plugins.job_control_command import register_background_job
        
        # Create output files in temporary directory for this background process
        import tempfile
        stdout_file = tempfile.NamedTemporaryFile(delete=False, prefix="jbrsh_bg_stdout_", suffix=".log")
        stderr_file = tempfile.NamedTemporaryFile(delete=False, prefix="jbrsh_bg_stderr_", suffix=".log")
        stdout_path = stdout_file.name
        stderr_path = stderr_file.name
        stdout_file.close()
        stderr_file.close()
        
        # Launch the process without & and use proper flags to run in background
        # Use nohup to ensure the process continues even if the terminal closes
        # Redirect output to our temporary files instead of /dev/null
        try:
            process = subprocess.Popen(
                f"nohup {actual_command} > {stdout_path} 2> {stderr_path} & echo $!",
                shell=True,
                executable='/bin/bash',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except (OSError, FileNotFoundError) as e:
            # Handle stale file handle - current directory is invalid
            click.echo(click.style(f"Warning: Current directory is invalid (stale file handle). Switching to home directory.", fg="yellow"))
            try:
                home_dir = os.path.expanduser("~")
                os.chdir(home_dir)
                click.echo(click.style(f"Changed working directory to: {home_dir}", fg="yellow"))
                # Retry the command in the home directory
                process = subprocess.Popen(
                    f"nohup {actual_command} > {stdout_path} 2> {stderr_path} & echo $!",
                    shell=True,
                    executable='/bin/bash',
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            except Exception as retry_error:
                # Clean up temp files before returning
                try:
                    os.unlink(stdout_path)
                    os.unlink(stderr_path)
                except OSError:
                    pass
                return -1, "", f"Failed to execute background command even after changing to home directory: {retry_error}"
        
        # Get the actual PID of the background process
        output, _ = process.communicate()
        try:
            # Extract the PID from the output
            pid = int(output.strip())
            
            # Register the job with our job control system, passing the output file paths
            job_id = register_background_job(pid, actual_command, stdout_path, stderr_path)
            click.echo(click.style(f"[{job_id}] Running in background: {actual_command} (PID: {pid})", fg="blue"))
        except (ValueError, TypeError):
            click.echo(click.style(f"Running in background: {actual_command} (unable to track PID)", fg="blue"))
        
        # Let the process run independently
        return 0, "", ""
    except ImportError:
        # Fall back to the old behavior if job_control isn't available
        click.echo(click.style(f"Running in background: {actual_command}", fg="blue"))
        bg_command = f"nohup {actual_command} > /dev/null 2>&1 &"
        return_code = os.system(bg_command)
        return return_code, "", ""
    except Exception as e:
        click.echo(click.style(f"Error running command in background: {e}", fg="red"))
        return -1, "", str(e)

def run_in_interactive(command):
    """
    Run a command in interactive mode
    """
    # Use subprocess for interactive applications instead of os.system
    # This gives us more control over the process execution
    import signal
    
    # Store original SIGINT handler
    original_sigint = signal.getsignal(signal.SIGINT)
    
    def custom_sigint_handler(sig, frame):
        # Restore original SIGINT handler
        signal.signal(signal.SIGINT, original_sigint)
        click.echo(click.style("\nInteractive command interrupted by user (Ctrl+C)", fg="yellow"))
        return
    
    try:
        # Set our custom interrupt handler
        signal.signal(signal.SIGINT, custom_sigint_handler)
        
        # Run the interactive command with subprocess
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                executable='/bin/bash'
            )
        except (OSError, FileNotFoundError) as e:
            # Handle stale file handle - current directory is invalid
            click.echo(click.style(f"Warning: Current directory is invalid (stale file handle). Switching to home directory.", fg="yellow"))
            try:
                home_dir = os.path.expanduser("~")
                os.chdir(home_dir)
                click.echo(click.style(f"Changed working directory to: {home_dir}", fg="yellow"))
                # Retry the command in the home directory
                process = subprocess.Popen(
                    command,
                    shell=True,
                    executable='/bin/bash'
                )
            except Exception as retry_error:
                # Restore original handler before returning
                signal.signal(signal.SIGINT, original_sigint)
                return -1, "", f"Failed to execute command even after changing to home directory: {retry_error}"
        
        # Wait for command to complete
        return_code = process.wait()
        
        # Restore the original signal handler
        signal.signal(signal.SIGINT, original_sigint)
        
        return return_code, "", ""
    except KeyboardInterrupt:
        # This will be caught if CTRL+C is pressed while not in subprocess
        click.echo(click.style("\nInteractive command interrupted by user (Ctrl+C)", fg="yellow"))
        # Restore original handler
        signal.signal(signal.SIGINT, original_sigint)
        return -1, "", "Aborted by user"
    except Exception as e:
        # Restore original handler before propagating
        signal.signal(signal.SIGINT, original_sigint)
        raise e

def run_in_non_interactive(command):
    """
    Run a command in non-interactive mode
    """
    # Use the simplest and most reliable approach: communicate() with a separate thread
    # for outputting lines as they come in
    from queue import Queue, Empty
    from threading import Thread
    
    # Queue for collecting output
    stdout_queue = Queue()
    stderr_queue = Queue()
    
    # Set environment variables to force color output
    env = os.environ.copy()
    
    # Check if FORCE_COLOR_OUTPUT is set in .jbrsh
    force_colors = os.environ.get("FORCE_COLOR_OUTPUT", "true").lower() in ["true", "yes", "1"]
    
    # Only apply color forcing if enabled (default is true)
    if force_colors:
        # Apply color forcing variables if not already set in .jbrsh
        color_vars = {
            'FORCE_COLOR': os.environ.get('FORCE_COLOR', '1'),
            'CLICOLOR_FORCE': os.environ.get('CLICOLOR_FORCE', '1'),
            'CLICOLOR': os.environ.get('CLICOLOR', '1'),
            'COLORTERM': os.environ.get('COLORTERM', 'truecolor'),
            'TERM': os.environ.get('TERM', 'xterm-256color'),
            'GIT_PAGER': os.environ.get('GIT_PAGER', 'cat'),
            'GIT_CONFIG_PARAMETERS': os.environ.get('GIT_CONFIG_PARAMETERS', "'color.ui=always'"),
            'GREP_OPTIONS': os.environ.get('GREP_OPTIONS', '--color=always'),
            'LS_COLORS': os.environ.get('LS_COLORS', 'rs=0:di=01;34:ln=01;36:mh=00:pi=40;33')
        }
        
        # Apply the color variables to the environment
        for var, value in color_vars.items():
            if value:  # Only set if there's a value
                env[var] = value
    
    # Start process with pipes and the enhanced environment
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            executable='/bin/bash',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            text=True,
            env=env
        )
    except (OSError, FileNotFoundError) as e:
        # Handle stale file handle - current directory is invalid
        click.echo(click.style(f"Warning: Current directory is invalid (stale file handle). Switching to home directory.", fg="yellow"))
        try:
            home_dir = os.path.expanduser("~")
            os.chdir(home_dir)
            click.echo(click.style(f"Changed working directory to: {home_dir}", fg="yellow"))
            # Retry the command in the home directory
            process = subprocess.Popen(
                command,
                shell=True,
                executable='/bin/bash',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                text=True,
                env=env
            )
        except Exception as retry_error:
            # If we still can't execute, return an error
            return -1, "", f"Failed to execute command even after changing to home directory: {retry_error}"
    
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
    
    try:
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
                    # Just collect stderr lines without printing immediately
                    # (we'll print them later to avoid duplication)
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
    except KeyboardInterrupt:
        # User pressed Ctrl+C - clean up the subprocess
        click.echo()  # Print newline after ^C
        try:
            process.terminate()
            # Give it a moment to terminate gracefully
            import time
            time.sleep(0.1)
            if process.poll() is None:
                # If still running, force kill
                process.kill()
        except:
            pass  # Process may already be dead
        
        # Return interrupted status
        return 130, ''.join(collected_stdout), ''.join(collected_stderr) + "\nCommand interrupted by user"
    
    # Wait for process to finish and get return code
    return_code = process.wait()
    
    # Join all the output
    stdout_content = ''.join(collected_stdout)
    stderr_content = ''.join(collected_stderr)
    
    return return_code, stdout_content, stderr_content

def execute_shell_command(command):
    """
    Execute a shell command and return the output
    """
    # Check if the command is empty
    if not command.strip():
        return 0, "", ""
        
    # Expand alias if present
    command = expand_aliases(command)

    # Check if the command is interactive
    is_interactive = is_cmd_interactive(command)

    try:
        # First check if command explicitly requests background execution with &
        force_background = command.strip().endswith('&')
        
        # If command ends with &, always run in background regardless of type
        if force_background:
            return run_in_background(command)
        elif is_interactive:
            return run_in_interactive(command)
        else:
            return run_in_non_interactive(command)
    except KeyboardInterrupt:
        return -1, "", "Aborted by user"
    except Exception as e:
        return -1, "", str(e)

def execute_command(command):
    """
    Execute a command and handle warnings and errors
    """
    # Check if AI commands are being prompted - if so, skip WARN_LIST prompting
    # to avoid double prompting (AI prompt + security prompt)
    prompt_ai_commands = os.environ.get('PROMPT_AI_COMMANDS', '').lower() in ('true', 'always', 'yes', '1')
    
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
    # BUT skip this if AI commands are already being prompted to avoid double prompting
    if warn and not prompt_ai_commands:
        choice = input(click.style("Are you sure you want to execute this command? [y/n]: ", fg="blue"))
        if choice.lower() != "y":
            click.echo(click.style("Command not executed", fg="red"))
            return -1, f"Command '{command}' not executed by user choice"
    
    # Check if this is an SSH-related command
    ssh_commands = ["ssh", "ssh-keygen", "ssh-copy-id", "ssh-add", "scp", "sftp", "rsync"]
    is_ssh_command = any(command.strip().startswith(cmd) for cmd in ssh_commands)
        
    # execute the command. if it is not successful print the error message
    try:
        returncode, output, error = execute_shell_command(command)
        
        # Check if we need to display error information based on IGNORE_ERRORS setting
        ignore_errors = os.environ.get("IGNORE_ERRORS", "").lower() in ["true", "yes", "1"]
        
        if returncode == -1:
            # Check specifically for keyboard interrupt
            if error == "Aborted by user":
                click.echo(click.style("\nCommand interrupted by user (Ctrl+C)", fg="yellow"))
            else:
                click.echo(click.style(f"{error}", fg="red"))

            return -1, f"Error: {error}"
        elif error:
            # The command produced error output, handle specific error types
            
            # For SSH commands with successful return code, treat stderr as normal output 
            # since they often output informational messages to stderr
            if is_ssh_command:
                if returncode == 0:
                    click.echo(error)
                    return 0, output
                else:
                    # For SSH commands with errors, display the original error message
                    # rather than trying to interpret it
                    click.echo(click.style(error.rstrip(), fg="red"))
                    return -1, f"{error.rstrip()}" # Return after displaying the error
                
            # Check for different types of errors (process each error only once)
            if "command not found" in error:
                # This is specifically when the command itself doesn't exist
                cmd_name = command.strip().split()[0] if command.strip() else "Command"
                click.echo(click.style(f"{cmd_name}: command not found", fg="red"))
                
                # Try to find a similar command
                similar_cmd = chat.find_similar_command(cmd_name)
                if similar_cmd:
                    # Create the full corrected command by replacing just the command name
                    corrected_command = command.replace(cmd_name, similar_cmd, 1)
                    
                    # Ask user if they want to execute the suggested command (showing the full corrected command)
                    choice = input(click.style(f"Did you mean '{corrected_command}'? Run this command instead? [y/n]: ", fg="yellow"))
                    if choice.lower() == "y":
                        # Execute the suggested command, but check if it's a built-in first
                        handled, new_command = is_built_in(corrected_command)
                        
                        if handled:
                            # The built-in command was handled directly
                            return 0, "Built-in command executed successfully"
                        elif new_command is not None:
                            # A new command was returned (e.g., from history or AI)
                            ret, msg = execute_command(new_command)
                        else:
                            # Execute external command
                            ret, msg = execute_command(corrected_command)

                        return ret, msg
                    else:
                        # User chose not to execute the suggested command
                        return -1, f"{cmd_name}: command not found"
                else:
                    # No similar command found
                    return -1, f"{cmd_name}: command not found"
                        
            elif "No such file or directory" in error:
                # When the file/directory path doesn't exist, echo the original error
                # This preserves the error message for cases like "ls /nonexistent/path"
                click.echo(click.style(error.rstrip(), fg="red"))
                return -1, f"{error.rstrip()}"
            else:
                # For all other errors, echo the error message and offer to explain
                click.echo(click.style(error.rstrip(), fg="red"))
                
                # Prompt for more information if IGNORE_ERRORS is not set to true and the command failed
                if not ignore_errors and returncode != 0:
                    choice = input(click.style("\nMore information about error? [y/n]: ", fg="blue"))
                    if choice.lower() == "y":
                        why_failed = chat.ask_why_failed(command, error)
                        if why_failed is not None:
                            click.echo(click.style(f"{why_failed}", fg="red"))
                        else:
                            click.echo(click.style("No explanation provided.", fg="red"))

                return -1, f"{error.rstrip()}"
        elif returncode != 0:
            # Handle case where return code is non-zero but there's no error message
            # This should only happen if we really have no error output at all
            # For SSH/SCP commands, we should have already displayed the error and returned
            
            # Double-check if this is an SSH-related command (shouldn't reach here if is_ssh_command was true)
            if is_ssh_command:
                # This is a failsafe in case the SSH error handling above missed something
                # Simply return without showing the "command failed with no error output" message
                return -1, "SSH command failed with no error output"
            
            cmd_name = command.strip().split()[0] if command.strip() else "Command" 

            # Prompt for more information if IGNORE_ERRORS is not set to true
            if not ignore_errors:
                choice = input(click.style("\nMore information about this error? [y/n]: ", fg="blue"))
                if choice.lower() == "y":
                    why_failed = chat.ask_why_failed(command, "Command failed with non-zero exit code but no error output")
                    if why_failed is not None:
                        click.echo(click.style(f"{why_failed}", fg="red"))
                    else:
                        click.echo(click.style("No explanation provided.", fg="red"))
            return -1, "Command failed with non-zero exit code but no error output"
        else:
            # Command succeeded with no error - return success
            return 0, output

    except KeyboardInterrupt:
        # Handle keyboard interrupt in this function as well
        click.echo(click.style("\nCommand execution interrupted by user (Ctrl+C)", fg="yellow"))
        return -1, "Command execution interrupted by user (Ctrl+C)"
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        return -1, f"Error: {e}"

def execute_chained_commands(command_chain, recursion_depth=0):
    """
    Execute multiple commands separated by && or ;
    
    Args:
        command_chain (str): The command or chain of commands to execute
        recursion_depth (int): Current recursion depth to prevent infinite recursion
    """
    # Prevent infinite recursion
    max_recursion_depth = 10
    if recursion_depth >= max_recursion_depth:
        click.echo(click.style(f"Error: Maximum command chain depth ({max_recursion_depth}) exceeded. This could be due to a circular reference or extremely complex command.", fg="red"))
        return -1, f"Maximum command chain depth ({max_recursion_depth}) exceeded"
    
    # Guard against non-string inputs that could cause recursion
    if not isinstance(command_chain, str):
        click.echo(click.style(f"Error: Invalid command type: {type(command_chain)}", fg="red"))
        return -1, f"Invalid command type: {type(command_chain)}"
        
    # First transform any multiline commands into proper format
    try:
        command_chain = transform_multiline(command_chain)
    except RecursionError:
        click.echo(click.style("Error: Command is too complex or recursive", fg="red"))
        return -1, "Command is too complex or recursive"
    
    # Process semicolons first, then &&
    # Check if there are semicolons in the command
    ret = 0  # Initialize with success
    msg = "Commands executed successfully"  # Initialize with success message
    
    if ';' in command_chain:
        # Split command by semicolons first
        semicolon_parts = split_commands_respect_semicolons(command_chain)
        
        # Process each part separately
        for part in semicolon_parts:
            part = part.strip()
            if not part:
                continue
                
            # If a part contains &&, process as chained commands
            if '&&' in part:
                ret, msg = execute_chained_commands(part, recursion_depth + 1)
            else:
                # Execute as a single command
                handled, new_command = is_built_in(part)
                
                if handled:
                    # Built-in command was executed, continue to next command
                    ret, msg = 0, "Built-in command executed successfully"
                elif new_command is not None:
                    # A new command was returned (e.g., from history or AI), execute it
                    # Don't recursively process here to avoid recursion issues
                    ret, msg = execute_command(new_command)
                    if ret == -1:
                        return ret, msg
                else:
                    # Execute external command
                    ret, msg = execute_command(part)
                    if ret == -1:
                        return -1, msg
        
        # Return the result of the last command in semicolon chain
        return ret, msg
    else:
        # No semicolons, check if there are && chains (not pipes)
        if '&&' in command_chain and '|' not in command_chain:
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
                    ret, msg = 0, "Built-in command executed successfully"
                elif new_command is not None:
                    # A new command was returned (e.g., from history or AI), execute it
                    ret, msg = execute_command(new_command)
                    if ret == -1:
                        return ret, msg
                else:
                    # Execute external command
                    ret, msg = execute_command(cmd)
                    if ret == -1:
                        return ret, msg
            
            # Return the result of the last command in && chain
            return ret, msg
        else:
            # No complex chaining, just execute the command directly
            # This handles pipes (|) and simple commands
            handled, new_command = is_built_in(command_chain)
            
            if handled:
                # Built-in command was executed, nothing else to do
                return 0, "Built-in command executed successfully"
            elif new_command is not None:
                # A new command was returned (e.g., from history or AI), execute it
                return execute_command(new_command)
            else:
                # Execute external command
                return execute_command(command_chain)
