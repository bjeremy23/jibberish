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
from app.output_history import store_output

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



def expand_parameterized_alias(alias_value, args):
    """
    Expand parameterized placeholders in an alias value.
    
    Supports:
    - {1}, {2}, etc. - Positional arguments
    - {1:-default} - Default value if argument not provided
    - {*} or {@} - All remaining arguments
    
    Args:
        alias_value: The alias definition possibly containing {n} placeholders
        args: List of arguments provided when the alias was invoked
        
    Returns:
        str: The expanded alias with placeholders replaced
    """
    import re
    
    result = alias_value
    
    # Check if alias has any parameterized placeholders
    if '{' not in alias_value:
        # No placeholders, append all args at the end (traditional behavior)
        if args:
            return f"{alias_value} {' '.join(args)}"
        return alias_value
    
    # Handle {*} or {@} - all arguments
    if '{*}' in result or '{@}' in result:
        all_args = ' '.join(args) if args else ''
        result = result.replace('{*}', all_args).replace('{@}', all_args)
    
    # Handle {n:-default} patterns (with default values)
    pattern_with_default = r'\{(\d+):-([^}]*)\}'
    for match in re.finditer(pattern_with_default, alias_value):
        placeholder = match.group(0)
        index = int(match.group(1)) - 1  # Convert to 0-based index
        default = match.group(2)
        
        if index < len(args):
            result = result.replace(placeholder, args[index])
        else:
            result = result.replace(placeholder, default)
    
    # Handle {n} patterns (without default values)
    pattern_simple = r'\{(\d+)\}'
    for match in re.finditer(pattern_simple, result):
        placeholder = match.group(0)
        index = int(match.group(1)) - 1  # Convert to 0-based index
        
        if index < len(args):
            result = result.replace(placeholder, args[index])
        else:
            # No argument provided and no default - leave empty or show warning
            result = result.replace(placeholder, '')
    
    return result.strip()


def expand_aliases(command):
    """ Expand aliases if present, including parameterized aliases with {1}, {2}, etc."""
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
                    args = part_parts[1:] if len(part_parts) > 1 else []
                    
                    # Check for recursive alias expansion - avoid expanding if alias value starts with same name
                    if alias_value.startswith(f"{part_parts[0]} "):
                        # This is a problematic pattern like "ls='ls -CF --color=always'"
                        # Only use the options part of the alias to avoid recursive expansion
                        alias_options = alias_value[len(part_parts[0]):].strip()
                        if args:
                            expanded_part = f"{part_parts[0]} {alias_options} {' '.join(args)}"
                        else:
                            expanded_part = f"{part_parts[0]} {alias_options}"
                    else:
                        # Use parameterized expansion
                        expanded_part = expand_parameterized_alias(alias_value, args)
                    
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
                args = command_parts[1:] if len(command_parts) > 1 else []
                
                # Check for recursive alias expansion - avoid expanding if alias value starts with same name
                if alias_value.startswith(f"{command_parts[0]} "):
                    # This is a problematic pattern like "ls='ls -CF --color=always'"
                    # Only use the options part of the alias to avoid recursive expansion
                    alias_options = alias_value[len(command_parts[0]):].strip()
                    if args:
                        expanded_command = f"{command_parts[0]} {alias_options} {' '.join(args)}"
                    else:
                        expanded_command = f"{command_parts[0]} {alias_options}"
                else:
                    # Use parameterized expansion
                    expanded_command = expand_parameterized_alias(alias_value, args)
                
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

def run_with_pty(command):
    """
    Run a command using a pseudo-terminal (PTY) for stdout/stdin so that
    TUI and curses programs (vim, htop, less, etc.) work correctly without
    needing an INTERACTIVE_LIST.  stderr is captured via a pipe and returned
    to the caller so that execute_command can still perform error detection
    ("command not found", "did you mean …", etc.) unchanged.

    Falls back to pipe-based execution when stdin is not a real TTY (e.g.
    scripted / piped usage).
    """
    import pty
    import select
    import termios
    import tty
    import struct
    import fcntl
    import signal
    from threading import Thread

    # ------------------------------------------------------------------
    # Build the child environment (colour forcing, pager suppression)
    # ------------------------------------------------------------------
    env = os.environ.copy()
    force_colors = os.environ.get("FORCE_COLOR_OUTPUT", "true").lower() in ["true", "yes", "1"]
    if force_colors:
        color_vars = {
            'FORCE_COLOR': os.environ.get('FORCE_COLOR', '1'),
            'CLICOLOR_FORCE': os.environ.get('CLICOLOR_FORCE', '1'),
            'CLICOLOR': os.environ.get('CLICOLOR', '1'),
            'COLORTERM': os.environ.get('COLORTERM', 'truecolor'),
            'TERM': os.environ.get('TERM', 'xterm-256color'),
            # Prevent git (and similar tools) from opening a pager
            'GIT_PAGER': os.environ.get('GIT_PAGER', 'cat'),
            'GIT_CONFIG_PARAMETERS': os.environ.get('GIT_CONFIG_PARAMETERS', "'color.ui=always'"),
            'LS_COLORS': os.environ.get('LS_COLORS', 'rs=0:di=01;34:ln=01;36:mh=00:pi=40;33'),
        }
        for var, value in color_vars.items():
            if value:
                env[var] = value

    # ------------------------------------------------------------------
    # Non-TTY fallback – pipe-based, same as the old non-interactive path
    # ------------------------------------------------------------------
    if not sys.stdin.isatty():
        from queue import Queue, Empty
        stdout_queue: Queue = Queue()
        stderr_queue: Queue = Queue()

        def _make_process():
            return subprocess.Popen(
                command, shell=True, executable='/bin/bash',
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                bufsize=1, text=True, env=env,
            )

        try:
            process = _make_process()
        except (OSError, FileNotFoundError):
            click.echo(click.style("Warning: Current directory is invalid. Switching to home directory.", fg="yellow"))
            try:
                os.chdir(os.path.expanduser("~"))
                process = _make_process()
            except Exception as exc:
                return -1, "", f"Failed to execute command: {exc}"

        def _reader(pipe, queue):
            try:
                with pipe:
                    for line in iter(pipe.readline, ''):
                        queue.put(line)
            finally:
                queue.put(None)

        Thread(target=_reader, args=[process.stdout, stdout_queue], daemon=True).start()
        Thread(target=_reader, args=[process.stderr, stderr_queue], daemon=True).start()

        collected_stdout, collected_stderr = [], []
        stdout_done = stderr_done = False
        try:
            while not (stdout_done and stderr_done):
                try:
                    line = stdout_queue.get(block=False)
                    if line is None:
                        stdout_done = True
                    else:
                        click.echo(line, nl=False)
                        sys.stdout.flush()
                        collected_stdout.append(line)
                except Empty:
                    pass
                try:
                    line = stderr_queue.get(block=False)
                    if line is None:
                        stderr_done = True
                    else:
                        collected_stderr.append(line)
                except Empty:
                    pass
                if not (stdout_done and stderr_done):
                    import time
                    time.sleep(0.01)
                    if process.poll() is not None and stdout_queue.empty() and stderr_queue.empty():
                        final_out, final_err = process.communicate()
                        if final_out:
                            click.echo(final_out, nl=False)
                            collected_stdout.append(final_out)
                        if final_err:
                            collected_stderr.append(final_err)
                        break
        except KeyboardInterrupt:
            click.echo()
            try:
                process.terminate()
                import time
                time.sleep(0.1)
                if process.poll() is None:
                    process.kill()
            except Exception:
                pass
            return 130, ''.join(collected_stdout), ''.join(collected_stderr) + "\nCommand interrupted by user"

        return_code = process.wait()
        return return_code, ''.join(collected_stdout), ''.join(collected_stderr)

    # ------------------------------------------------------------------
    # PTY path – stdin IS a real TTY
    # ------------------------------------------------------------------
    def _open_pty_and_spawn():
        """Create a PTY pair and spawn the subprocess."""
        master_fd, slave_fd = pty.openpty()
        try:
            cols, rows = os.get_terminal_size()
            fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))
        except Exception:
            pass

        proc = subprocess.Popen(
            command,
            shell=True,
            executable='/bin/bash',
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=subprocess.PIPE,   # stderr captured separately
            close_fds=True,
            env=env,
            preexec_fn=os.setsid,     # own process group → Ctrl+C propagates correctly
        )
        os.close(slave_fd)            # parent doesn't need the slave end
        return master_fd, proc

    try:
        master_fd, process = _open_pty_and_spawn()
    except (OSError, FileNotFoundError):
        click.echo(click.style("Warning: Current directory is invalid. Switching to home directory.", fg="yellow"))
        try:
            os.chdir(os.path.expanduser("~"))
            master_fd, process = _open_pty_and_spawn()
        except Exception as exc:
            return -1, "", f"Failed to execute command: {exc}"

    stdin_fd = sys.stdin.fileno()

    # Capture stderr in a background thread without displaying it
    # (execute_command will handle display + error interpretation)
    collected_stderr: list = []

    def _read_stderr(pipe):
        try:
            with pipe:
                for line in iter(pipe.readline, b''):
                    collected_stderr.append(line.decode('utf-8', errors='replace'))
        except Exception:
            pass

    Thread(target=_read_stderr, args=[process.stderr], daemon=True).start()

    # Switch the real terminal to raw mode so every keypress goes straight
    # to the PTY (Ctrl+C, arrow keys, etc. all work as expected)
    old_settings = termios.tcgetattr(stdin_fd)
    tty.setraw(stdin_fd)

    # Propagate window-resize events to the child's PTY
    original_sigwinch = signal.getsignal(signal.SIGWINCH)

    def _handle_sigwinch(sig, frame):
        try:
            cols, rows = os.get_terminal_size()
            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))
        except Exception:
            pass

    signal.signal(signal.SIGWINCH, _handle_sigwinch)

    collected_stdout: list = []

    def _restore():
        try:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass
        signal.signal(signal.SIGWINCH, original_sigwinch)
        try:
            os.close(master_fd)
        except OSError:
            pass

    try:
        while True:
            try:
                r, _, _ = select.select([master_fd, stdin_fd], [], [], 0.05)
            except (ValueError, OSError):
                break

            for fd in r:
                if fd == master_fd:
                    try:
                        data = os.read(master_fd, 4096)
                        if data:
                            sys.stdout.buffer.write(data)
                            sys.stdout.buffer.flush()
                            collected_stdout.append(data.decode('utf-8', errors='replace'))
                    except OSError:
                        # EIO: slave side closed (process exited)
                        break
                elif fd == stdin_fd:
                    try:
                        data = os.read(stdin_fd, 1024)
                        if data:
                            os.write(master_fd, data)
                    except OSError:
                        break

            if process.poll() is not None:
                # Drain any output the process wrote just before exiting
                try:
                    while True:
                        r2, _, _ = select.select([master_fd], [], [], 0.1)
                        if not r2:
                            break
                        data = os.read(master_fd, 4096)
                        if not data:
                            break
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()
                        collected_stdout.append(data.decode('utf-8', errors='replace'))
                except OSError:
                    pass
                break
    finally:
        _restore()

    return_code = process.wait()
    return return_code, ''.join(collected_stdout), ''.join(collected_stderr)

def execute_shell_command(command):
    """
    Execute a shell command and return the output
    """
    # Check if the command is empty
    if not command.strip():
        return 0, "", ""
        
    # Expand alias if present
    command = expand_aliases(command)

    try:
        # First check if command explicitly requests background execution with &
        force_background = command.strip().endswith('&')

        if force_background:
            return run_in_background(command)
        else:
            return run_with_pty(command)
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
    
    # if the command is in the warn_list, ask the user if they want to execute the command
    # Skip WARN_LIST prompting if AI commands are being prompted to avoid double prompting
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
            # Command succeeded with no error - store output and return success
            if output and output.strip():
                store_output(command, output, returncode)
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
