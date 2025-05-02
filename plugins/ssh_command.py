"""
SSH command plugin.
"""
import subprocess
import sys
import click
from plugin_system import BuiltinCommand, BuiltinCommandRegistry


class SSHCommand(BuiltinCommand):
    """Plugin for SSH command with enhanced handling of remote execution"""
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.startswith("ssh ")
    
    def execute(self, command):
        """Execute an SSH command"""
        try:
            # Check for aliases first
            try:
                from plugins.alias_command import get_aliases
                aliases = get_aliases()
                # Check if 'ssh' is an alias
                if 'ssh' in aliases:
                    # Get the alias value
                    ssh_alias = aliases['ssh']
                    # Build the expanded command - replace just the 'ssh' part
                    parts = command.split(None, 1)
                    if len(parts) > 1:
                        expanded_command = f"{ssh_alias} {parts[1]}"
                    else:
                        expanded_command = ssh_alias
                    
                    command = expanded_command
            except (ImportError, AttributeError):
                # If there's an error importing the plugin or getting aliases, just continue
                pass
            
            # For standard SSH commands, check for the case of "ssh host && command1 && command2"
            # which should be converted to "ssh host "command1 && command2""
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
                
            # Check if this is a properly formatted SSH command before continuing
            parts = command.split(None, 2)  # Split into max 3 parts: 'ssh', 'host', 'commands'
            
            if len(parts) < 2:
                click.echo(click.style("Usage: ssh <host> [\"command1 && command2 ...\"]", fg="red"))
                return True
            
            # If command already has options like -o, execute it directly without further processing
            if ' -o ' in command:
                # Execute SSH command with options
                # Only import signal when actually executing a command
                import signal
                
                # Check if we're running in a test environment
                in_test_mode = 'unittest' in sys.modules or 'pytest' in sys.modules
                
                if in_test_mode:
                    # In test mode, don't use custom signal handling
                    result = subprocess.run(command, shell=True, text=True)
                else:
                    # Define signal handling in a function to avoid module-level effects
                    def execute_ssh_with_signal_handling(cmd):
                        # Store the original SIGINT (CTRL+C) handler
                        original_sigint = signal.getsignal(signal.SIGINT)
                        
                        # Custom handler for CTRL+C
                        def custom_sigint_handler(sig, frame):
                            # Restore original handler immediately
                            signal.signal(signal.SIGINT, original_sigint)
                            click.echo(click.style("\nSSH connection interrupted by user (Ctrl+C)", fg="yellow"))
                            # The process will be killed automatically
                            return
                        
                        try:
                            # Install our custom handler
                            signal.signal(signal.SIGINT, custom_sigint_handler)
                            
                            # Run the command with subprocess
                            process = subprocess.Popen(cmd, shell=True, text=True)
                            process.wait()
                        except KeyboardInterrupt:
                            # This will be caught if CTRL+C is pressed during subprocess execution
                            click.echo(click.style("\nSSH connection interrupted by user (Ctrl+C)", fg="yellow"))
                        finally:
                            # Always restore the original handler
                            signal.signal(signal.SIGINT, original_sigint)
                    
                    # Execute with signal handling
                    execute_ssh_with_signal_handling(command)
                
                return True
                
            # Process the command for normal SSH usage
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
                
            # Execute the SSH command with signal handling
            # Only import signal when actually executing a command
            import signal
            
            # Check if we're running in a test environment
            in_test_mode = 'unittest' in sys.modules or 'pytest' in sys.modules
            
            if in_test_mode:
                # In test mode, don't use custom signal handling
                result = subprocess.run(full_command, shell=True, text=True)
            else:
                # Define signal handling in a function to avoid module-level effects
                def execute_ssh_with_signal_handling(cmd):
                    # Store the original SIGINT (CTRL+C) handler
                    original_sigint = signal.getsignal(signal.SIGINT)
                    
                    # Custom handler for CTRL+C
                    def custom_sigint_handler(sig, frame):
                        # Restore original handler immediately
                        signal.signal(signal.SIGINT, original_sigint)
                        click.echo(click.style("\nSSH connection interrupted by user (Ctrl+C)", fg="yellow"))
                        # The process will be killed automatically
                        return
                    
                    try:
                        # Install our custom handler
                        signal.signal(signal.SIGINT, custom_sigint_handler)
                        
                        # Run the command with subprocess
                        process = subprocess.Popen(cmd, shell=True, text=True)
                        process.wait()
                    except KeyboardInterrupt:
                        # This will be caught if CTRL+C is pressed during subprocess execution
                        click.echo(click.style("\nSSH connection interrupted by user (Ctrl+C)", fg="yellow"))
                    finally:
                        # Always restore the original handler
                        signal.signal(signal.SIGINT, original_sigint)
                
                # Execute with signal handling
                execute_ssh_with_signal_handling(full_command)
            
            return True
        except Exception as e:
            click.echo(click.style(f"SSH error: {str(e)}", fg="red"))
            return True


# Register the plugin with the registry
BuiltinCommandRegistry.register(SSHCommand())
