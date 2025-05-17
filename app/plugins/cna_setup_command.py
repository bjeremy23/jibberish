"""
Plugin for running CNA commands in Jibberish.
This plugin specifically handles the 'cna-setup' command (with any arguments) and
the 'cna enter-build' command. Other 'cna' commands are handled by the executor.
The scripts and functions are designed to be sourced from the
.vm-tools directory.
"""
import os
import sys
import subprocess
import click
import shutil

# Add the parent directory to sys.path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.plugin_system import BuiltinCommand, BuiltinCommandRegistry
from app.utils import is_debug_enabled

class CNASetupPlugin(BuiltinCommand):
    """Command plugin for running CNA commands and functionality."""
    
    # Plugin attributes
    plugin_name = "cna_setup_command"  # Name of the plugin
    is_required = False  # This is an optional plugin
    is_enabled = True  # Enabled by default, can be overridden by environment variable
    
    # Path to the cna-setup script
    # Check both common locations with both naming conventions
    # Use the current user's username instead of hardcoding
    def __get_script_paths(self):
        """Get script paths with the current username instead of hardcoded values"""
        username = os.getenv('USER', 'user')
        return [
            f"/localdata/{username}/.vm-tools/interface/bin/cna-setup.sh",
        ]
    
    # These will be populated in __init__
    SCRIPT_PATHS = []
    
    def __init__(self):
        """Initialize the plugin and find the script."""
        super().__init__()
        
        # Get the script paths with the current username
        self.SCRIPT_PATHS = self.__get_script_paths()
        
        # Find the actual script path
        self.script_path = None
        for path in self.SCRIPT_PATHS:
            if os.path.exists(path):
                self.script_path = path
                break
        
        if is_debug_enabled():
            if self.script_path:
                print(f"Found CNA setup script at: {self.script_path}")
            else:
                print("Warning: Could not locate CNA setup script")
        
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        command = command.strip().split()
        # Handle only cna-setup (any arguments) and cna enter-build
        if len(command) == 0:
            return False
        
        # Accept any cna-setup command
        if command[0] == "cna-setup":
            return True
            
        # For cna, only accept "cna enter-build" specifically
        if command[0] == "cna" and len(command) >= 2 and command[1] == "enter-build":
            return True
            
        return False
    
    def execute(self, command):
        """Execute the cna-setup command."""
        # Parse arguments (everything after "cna-setup")
        args = command.strip().split()
        cmd_name = args[0]  # This will be "cna-setup"
        if len(args) > 1:
            script_args = args[1:]
        else:
            script_args = []
            
        # Special handling for interactive commands like 'cna enter-build'
        is_interactive_command = False
        
        # Check if this is a 'cna' command (not cna-setup)
        is_cna_command = cmd_name == "cna"
        
        # For 'cna' commands, the first arg is the subcommand (like 'enter-build')
        if is_cna_command and len(script_args) > 0:
            if script_args[0] == "enter-build":
                is_interactive_command = True
                click.echo(click.style("Interactive command detected: 'cna enter-build'", fg="yellow"))
                click.echo(click.style("Setting up interactive terminal environment...", fg="blue"))
                
                # Set environment variables that will be needed for the container session
                os.environ["DOCKER_INTERACTIVE"] = "1"
                os.environ["DOCKER_USE_TTY"] = "1"
                os.environ["TERM"] = "xterm-256color"
                
        try:
            # Create a temporary script that runs cna-setup properly
            temp_script = f"""#!/bin/bash
# Setup the environment for cna-setup
export PATH=$PATH:/localdata/$USER/.vm-tools/interface/bin

# Source the user's bash profile to get any custom settings
if [ -f ~/.bash_profile ]; then
    source ~/.bash_profile
elif [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# For interactive commands, make sure TERM is set properly
{"export TERM=xterm-256color" if is_interactive_command else ""}
{"export DOCKER_INTERACTIVE=1" if is_interactive_command else ""}
{"export DOCKER_USE_TTY=1" if is_interactive_command else ""}

# If this is cna enter-build, we need special handling
if [ "{cmd_name}" = "cna" ] && [ "{' '.join(script_args)}" = "enter-build" ]; then
    # Set appropriate environment variables for interactive sessions
    export DOCKER_INTERACTIVE=1
    export DOCKER_USE_TTY=1
    export TERM=xterm-256color
    
    # Trap exit signals to ensure clean exit from container
    trap 'exit 0' SIGINT SIGTERM
    
    # Check if the function exists first
    if type -t cna >/dev/null; then
        echo "Found cna function in bash environment, executing cna enter-build..."
        cna enter-build
        # The exit code doesn't matter for interactive containers
        exit 0
    else
        # If no cna function, try to find the script
        if [ -f "$CNA_TOOLS/interface/bin/cna" ]; then
            echo "Found cna script, executing cna enter-build..."
            bash "$CNA_TOOLS/interface/bin/cna" enter-build
            # The exit code doesn't matter for interactive containers
            exit 0
        fi
    fi
fi

# First check if a bash function exists for cna-setup
if type -t cna-setup >/dev/null; then
    echo "Found cna-setup function in bash environment, executing..."
    cna-setup {' '.join(script_args)}
    exit $?
fi

# If we get here, the function wasn't found, so try executing the script directly
# But the script is meant to be sourced, not executed, so we need to be careful

# Ensure CNA_TOOLS is set correctly to match bash behavior
if [ -z "$CNA_TOOLS" ]; then
    vm_tools_path="/localdata/$USER/.vm-tools"
    if [ ! -d "$vm_tools_path" ]; then
        echo "Cloning latest vm-tools..."
        git clone --branch main_int https://msazuredev@dev.azure.com/msazuredev/AzureForOperators/_git/vm-tools "$vm_tools_path"
    else
        echo "Using existing vm-tools directory at $vm_tools_path"
    fi
    export CNA_TOOLS="$vm_tools_path"
fi

# Handle different command types
if [ "{cmd_name}" = "cna" ] && [ "{' '.join(script_args)}" = "enter-build" ]; then
    # For cna enter-build, we need to source the cna-setup script first, then run cna enter-build
    if [ -f "{self.script_path}" ]; then
        echo "Sourcing cna-setup script..."
        source "{self.script_path}"
        
        # Now execute cna enter-build command
        echo "Executing cna enter-build..."
        if [ -f "$CNA_TOOLS/interface/bin/cna" ]; then
            # Extra environment variables for interactive docker sessions
            export DOCKER_USE_TTY=1
            export DOCKER_INTERACTIVE=1
            export TERM=xterm-256color
            
            # Trap exit signals to handle container exit gracefully
            trap 'exit 0' SIGINT SIGTERM
            
            # Execute the cna script with enter-build argument
            bash "$CNA_TOOLS/interface/bin/cna" enter-build
            
            # Container has exited - always return success
            exit 0
        else
            echo "ERROR: Could not find cna script at $CNA_TOOLS/interface/bin/cna"
            return 1
        fi
    else
        echo "ERROR: Could not find {self.script_path}"
        return 1
    fi
else
    # Create a proper setup function that matches the bash version for standard cna-setup
    cna_setup() {{
        # Source the script after setting CNA_TOOLS
        if [ -f "{self.script_path}" ]; then
            # The script is designed to be sourced not executed
            source "{self.script_path}"
        else
            echo "ERROR: Could not find {self.script_path}"
            return 1
        fi
    }}
    
    # Now execute the function we just created for regular cna-setup
    cna_setup {' '.join(script_args)}
fi
exit_code=$?

# Return the exit code from the command
exit $exit_code
"""
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
                temp.write(temp_script)
                temp_path = temp.name
            
            # Make it executable
            os.chmod(temp_path, 0o755)
            
            # Execute the temporary script and display output in real-time
            click.echo(click.style(f"Running {cmd_name}...", fg="yellow"))
            
            # Since we can't create a TTY inside this process, let's run this in a terminal
            # We'll display a message explaining the approach
            click.echo(click.style("Note: For best results with docker login, run cna-setup directly in your bash shell", fg="cyan"))
            
            # Make the script more readable for debugging
            if is_debug_enabled():
                click.echo(click.style("Debug: Temp script contents:", fg="blue"))
                click.echo(temp_script)
            
            # Different execution approaches based on whether it's an interactive command
            if is_interactive_command:
                # For interactive commands (like cna enter-build), use the 'script' command
                # This creates a proper TTY environment that can handle complex terminal interactions
                import tempfile
                import time
                
                # Create a script command that will run our temp script
                script_log = os.path.join(tempfile.gettempdir(), f"cna_interactive_{int(time.time())}.log")
                click.echo(click.style(f"Creating TTY session (output will be logged to {script_log})...", fg="blue"))
                
                # Check if we're in a graphical environment
                has_display = "DISPLAY" in os.environ and os.environ["DISPLAY"]
                terminal_cmd = None
                term_args = None
                
                # Only try graphical terminals if we have a display
                if has_display:
                    # First try gnome-terminal (most common in GNOME environments)
                    if shutil.which("gnome-terminal"):
                        terminal_cmd = "gnome-terminal"
                        term_args = [
                            terminal_cmd,
                            "--title", "CNA Enter-Build Container",
                            "--", "bash", temp_path
                        ]
                    # Then try xterm with proper syntax (different from gnome-terminal)
                    elif shutil.which("xterm"):
                        terminal_cmd = "xterm"
                        term_args = [
                            terminal_cmd,
                            "-title", "CNA Enter-Build Container",
                            "-fa", "Monospace",  # Font family
                            "-fs", "12",         # Font size (medium)
                            "-bg", "black",      # Background color
                            "-fg", "white",      # Foreground color
                            "-e", "bash", temp_path
                        ]
                    # Try konsole (KDE terminal)
                    elif shutil.which("konsole"):
                        terminal_cmd = "konsole"
                        term_args = [
                            terminal_cmd,
                            "--title", "CNA Enter-Build Container",
                            "--profile", "Shell",  # Use the Shell profile if available
                            "--hide-menubar",      # For cleaner look
                            "--hide-tabbar",       # For cleaner look
                            "-e", "bash", temp_path
                        ]
                
                # Only try to use a graphical terminal if we have a display and found a valid terminal
                if has_display and terminal_cmd and term_args and is_cna_command and len(script_args) > 0 and script_args[0] == "enter-build":
                    # For cna enter-build specifically, try to launch in a proper terminal window
                    try:
                        # Launch in a terminal window for best interactive experience
                        click.echo(click.style(f"Launching cna enter-build in a new {terminal_cmd} window...", fg="green"))
                        result = subprocess.run(term_args, check=False)
                    except Exception as e:
                        click.echo(click.style(f"Failed to launch terminal: {str(e)}", fg="red"))
                        # Fall back to script command if terminal launch fails
                        click.echo(click.style("Falling back to script command...", fg="yellow"))
                        terminal_cmd = None  # Reset to trigger the fallback path
                
                # Fall back to script command if we couldn't launch a graphical terminal
                if not terminal_cmd or not has_display:
                    # For other interactive commands or if no terminal is available, use the script command
                    if not has_display:
                        click.echo(click.style("No display available. Using script command instead of graphical terminal.", fg="blue"))
                    # Set up the script command
                    script_cmd = [
                        "script",
                        "-e",  # Return exit code of the command
                        "-c", f"bash {temp_path}",  # The command to run
                        script_log  # Log file
                    ]
                    
                    # Run it
                    click.echo(click.style("Using script command for interactive session...", fg="blue"))
                    click.echo(click.style("Entering interactive mode. Press Ctrl+D or type 'exit' when finished.", fg="yellow"))
                    result = subprocess.run(script_cmd, check=False)
                
                # After command completes, show additional info
                click.echo(click.style(f"\nInteractive session completed.", fg="green"))
                
                # Check if the log has useful output to show
                try:
                    log_size = os.path.getsize(script_log)
                    
                    # For cna enter-build, don't show the log on success as it's confusing
                    if is_cna_command and len(script_args) > 0 and script_args[0] == "enter-build":
                        # Only show log if there was an unexpected error (not a normal exit)
                        if result.returncode != 0 and result.returncode != 130:  # 130 is Ctrl+C
                            click.echo(click.style("Error log:", fg="red"))
                            with open(script_log, 'r') as f:
                                log_content = f.read()
                            click.echo(log_content)
                    elif log_size > 0 and log_size < 10000:  # Only show if it's not too large
                        click.echo(click.style("Command output log:", fg="blue"))
                        with open(script_log, 'r') as f:
                            log_content = f.read()
                        click.echo(log_content)
                        
                    os.unlink(script_log)  # Clean up
                except Exception:
                    pass  # Ignore errors with log handling
                    
            else:
                # For non-interactive commands, use standard execution
                result = subprocess.run(
                    temp_path,
                    check=False,
                    text=True,
                    shell=True
                )
            
            # Clean up
            os.unlink(temp_path)
            
            # Since we displayed output in real-time, no need to display it again
                
            # Return success/failure based on script exit code
            # Special handling for interactive container sessions
            if is_interactive_command and is_cna_command and script_args and script_args[0] == "enter-build":
                # Exit codes from interactive containers can be non-zero (e.g., 130 from Ctrl+C)
                # but we should still consider this a success as the user intended to exit
                click.echo(click.style(f"Container session ended.", fg="green"))
                return True
            elif result.returncode == 0:
                click.echo(click.style(f"{cmd_name} completed successfully.", fg="green"))
                return True
            else:
                click.echo(click.style(f"{cmd_name} finished with exit code {result.returncode}.", fg="yellow"))
                # For interactive commands, don't report as failure even with non-zero exit
                return True if is_interactive_command else False
            
        except Exception as e:
            click.echo(click.style(f"Error executing {cmd_name}: {str(e)}", fg="red"))
            return False

# Register the plugin
BuiltinCommandRegistry.register(CNASetupPlugin())
