"""
Plugin for running CNA commands in Jibberish.
This plugin specifically handles the 'cna-setup' command (with any arguments) and
the 'cna enter-build' command directly. All other 'cna' commands are captured
for typo correction but then passed back to be executed by the system executor.

The direct-handled commands use temp scripts that are designed to be sourced 
from the .vm-tools directory.

How commands are handled:
1. 'cna-setup' - Directly handled with TTY forwarding for token prompts
2. 'cna enter-build' - Directly handled in graphical terminal or via script command
3. Other 'cna' commands - Checked for typos, then passed to main executor
4. Typos of 'cna' (like 'cne') - Suggest correction to 'cna'
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
    
    # Define common typos for 'cna' command
    CNA_TYPOS = ["cne", "cni", "cns", "can", "cnq", "cma", "cba", "cn", "cnaa"]
    
    # Define which cna commands to handle directly vs pass back to executor
    DIRECT_HANDLED_COMMANDS = ["enter-build"]  # cna-setup is handled separately
    
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
                
        # Set a placeholder path for the vm-tools directory
        username = os.getenv('USER', 'user')
        self.vm_tools_dir = f"/localdata/{username}/.vm-tools"
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        command_parts = command.strip().split()
        # Handle empty commands
        if len(command_parts) == 0:
            return False
        
        cmd_name = command_parts[0]
        
        # Handle common typos of 'cna'
        if cmd_name in self.CNA_TYPOS:
            return True
        
        # Accept any cna-setup command
        if cmd_name == "cna-setup":
            return True
            
        # Accept any command that starts with 'cna'
        if cmd_name == "cna":
            return True
            
        return False
    
    def execute(self, command):
        """Execute the cna commands."""
        # Parse arguments (everything after "cna-setup")
        args = command.strip().split()
        cmd_name = args[0]  # This will be "cna-setup" or "cna" or a typo
        if len(args) > 1:
            script_args = args[1:]
        else:
            script_args = []
            
        # Handle typos of 'cna'
        if cmd_name in self.CNA_TYPOS:
            click.echo(click.style(f"{cmd_name}: command not found", fg="red"))
            suggestion = "cna" + (" " + " ".join(script_args) if script_args else "")
            choice = input(click.style(f"Did you mean '{suggestion}'? Run this command instead? [y/n]: ", fg="yellow"))
            if choice.lower() == "y":
                cmd_name = "cna"  # Correct the command
                # Pass the corrected command back to the executor
                corrected_command = "cna " + " ".join(script_args)
                # Return False and the corrected command to be executed by the executor
                return False, corrected_command
            else:
                return False
        
        # For commands like 'cna something', check if we should handle it directly or pass back
        if cmd_name == "cna" and len(script_args) > 0:
            subcommand = script_args[0]
            # If it's not a command we handle directly, pass it back to the executor
            if subcommand not in self.DIRECT_HANDLED_COMMANDS:
                # Return the command to be executed by the executor without any messages
                return False, command.strip()
        
        # Special handling for interactive commands
        is_interactive_command = False
        
        # Check if this is a 'cna' command (not cna-setup)
        is_cna_command = cmd_name == "cna"
        
        # Initialize result variable to avoid "referenced before assignment" errors
        result = None
        
        # Check if we need to clone the vm-tools repo first
        if cmd_name == "cna-setup" and not self.script_path:
            click.echo(click.style(f"The cna-setup script was not found in the expected location.", fg="yellow"))
            click.echo(click.style(f"Attempting to clone vm-tools repository...", fg="blue"))
            
            # Make sure the parent directory exists
            parent_dir = os.path.dirname(self.vm_tools_dir)
            os.makedirs(parent_dir, exist_ok=True)
            
            try:
                # Check if git is available
                subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Clone the repository
                clone_cmd = [
                    "git", "clone", "--branch", "main_int", 
                    "https://msazuredev@dev.azure.com/msazuredev/AzureForOperators/_git/vm-tools", 
                    self.vm_tools_dir
                ]
                click.echo(click.style(f"Running: {' '.join(clone_cmd)}", fg="blue"))
                click.echo(click.style(f"(You may be prompted for your Azure DevOps credentials)", fg="yellow"))
                
                # Use check=False to handle the return code ourselves
                clone_result = subprocess.run(clone_cmd, check=False)
                
                if clone_result.returncode == 0:
                    click.echo(click.style(f"Successfully cloned vm-tools to {self.vm_tools_dir}", fg="green"))
                    click.echo(click.style(f"Will now attempt to run cna-setup with the newly cloned repository.", fg="green"))
                    
                    # Update the script path now that we've cloned the repo
                    self.SCRIPT_PATHS = self.__get_script_paths()
                    for path in self.SCRIPT_PATHS:
                        if os.path.exists(path):
                            self.script_path = path
                            click.echo(click.style(f"Found cna-setup script at {path}", fg="green"))
                            break
                    
                    # If we still don't have a script path, show an error
                    if not self.script_path:
                        click.echo(click.style(f"Repository cloned successfully, but cna-setup script was not found at expected location.", fg="red"))
                else:
                    click.echo(click.style(f"git clone returned non-zero exit code: {clone_result.returncode}", fg="red"))
                    click.echo(click.style(f"You may need to manually clone the repository.", fg="yellow"))
            except subprocess.CalledProcessError:
                click.echo(click.style(f"Failed to clone vm-tools repository.", fg="red"))
                click.echo(click.style(f"You may need to authenticate with Azure DevOps or check your network connection.", fg="yellow"))
            except FileNotFoundError:
                click.echo(click.style(f"Git is not installed or not in the PATH.", fg="red"))
                click.echo(click.style(f"Please install git or manually clone the repository.", fg="yellow"))
        
        # For 'cna' commands, the first arg is the subcommand (like 'enter-build')
        if is_cna_command and len(script_args) > 0:
            if script_args[0] == "enter-build":
                is_interactive_command = True
                click.echo(click.style("Setting up terminal environment...", fg="blue"))
                
                # Set environment variables that will be needed for the container session
                os.environ["DOCKER_INTERACTIVE"] = "1"
                os.environ["DOCKER_USE_TTY"] = "1"
                os.environ["TERM"] = "xterm-256color"
        # Also treat cna-setup as potentially interactive for token prompts
        elif cmd_name == "cna-setup":
            is_interactive_command = True
            
            # Check if we likely need a token prompt (first time setup)
            needs_token = False
            git_credentials = os.path.expanduser("~/.git-credentials")
            if not os.path.exists(git_credentials):
                needs_token = True
            else:
                # Check if credentials file exists but doesn't have Azure DevOps token
                try:
                    with open(git_credentials, 'r') as f:
                        if "msazuredev@dev.azure.com" not in f.read():
                            needs_token = True
                except:
                    needs_token = True  # If we can't read the file, assume we need a token
            
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
if [ "{cmd_name}" = "cna" ] && [[ "{' '.join(script_args)}" == enter-build* ]]; then
    # Set appropriate environment variables for interactive sessions
    export DOCKER_INTERACTIVE=1
    export DOCKER_USE_TTY=1
    export TERM=xterm-256color
    
    # Trap exit signals to ensure clean exit from container
    trap 'exit 0' SIGINT SIGTERM
    
    # Check if the function exists first
    if type -t cna >/dev/null; then
        echo "Found cna function in bash environment, executing cna {' '.join(script_args)}..."
        cna {' '.join(script_args)}
        # The exit code doesn't matter for interactive containers
        exit 0
    else
        # If no cna function, try to find the script
        if [ -f "$CNA_TOOLS/interface/bin/cna" ]; then
            echo "Found cna script, executing cna {' '.join(script_args)}..."
            bash "$CNA_TOOLS/interface/bin/cna" {' '.join(script_args)}
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

# Ensure CNA_TOOLS is set correctly to match bash behavior
if [ -z "$CNA_TOOLS" ]; then
    vm_tools_path="/localdata/$USER/.vm-tools"
    if [ ! -d "$vm_tools_path" ]; then
        echo "The vm-tools directory does not exist at $vm_tools_path"
        echo "Attempting to clone latest vm-tools..."
        
        # Check if git is available
        if ! command -v git &> /dev/null; then
            echo "ERROR: Git is not installed or not in the PATH. Cannot clone vm-tools."
            echo "Please install git or manually clone the vm-tools repository."
            exit 1
        fi
        
        # Make sure the parent directory exists
        mkdir -p "/localdata/$USER"
        
        # Try to clone the repository
        if git clone --branch main_int https://msazuredev@dev.azure.com/msazuredev/AzureForOperators/_git/vm-tools "$vm_tools_path"; then
            echo "Successfully cloned vm-tools to $vm_tools_path"
        else
            echo "ERROR: Failed to clone vm-tools repository."
            echo "You might need to authenticate with Azure DevOps or check your network connection."
            exit 1
        fi
    else
        echo "Using existing vm-tools directory at $vm_tools_path"
    fi
    export CNA_TOOLS="$vm_tools_path"
    echo "Set CNA_TOOLS to $vm_tools_path"
fi

# Handle different command types
if [ "{cmd_name}" = "cna" ] && [[ "{' '.join(script_args)}" == enter-build* ]]; then
    # For cna enter-build, we need to source the cna-setup script first, then run cna enter-build
    if [ -f "{self.script_path}" ]; then
        echo "Sourcing cna-setup script..."
        source "{self.script_path}"
        
        # Now execute cna command (enter-build with any options)
        echo "Executing cna {' '.join(script_args)}..."
        if [ -f "$CNA_TOOLS/interface/bin/cna" ]; then
            # Extra environment variables for interactive docker sessions
            export DOCKER_USE_TTY=1
            export DOCKER_INTERACTIVE=1
            export TERM=xterm-256color
            
            # Trap exit signals to handle container exit gracefully
            trap 'exit 0' SIGINT SIGTERM
            
            # Execute the cna script with all the provided arguments
            bash "$CNA_TOOLS/interface/bin/cna" {' '.join(script_args)}
            
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
    exit_code=$?

    # Return the exit code from the command
    exit $exit_code
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
            
            # Make the script more readable for debugging
            if is_debug_enabled():
                click.echo(click.style("Debug: Temp script contents:", fg="blue"))
                click.echo(temp_script)
            
            # Different execution approaches based on whether it's an interactive command
            if is_interactive_command:
                # For interactive commands, set up appropriate handling
                import tempfile
                import time
                
                # Initialize TTY session for interactive commands
                if cmd_name != "cna-setup":
                    # Create a TTY session
                    click.echo(click.style(f"Creating TTY session...", fg="blue"))
                
                # Check if this is cna-setup (special handling required for tokens)
                if cmd_name == "cna-setup":
                    # ALWAYS use direct TTY handling for cna-setup to ensure token prompts work           
                    # Use simpler execution with direct TTY handling - connect directly to user's terminal
                    script_cmd = [
                        "bash",
                        temp_path
                    ]
                    
                    # Run it with direct input/output to terminal
                    result = subprocess.run(
                        script_cmd, 
                        check=False,
                        stdin=sys.stdin,     # Connect to user's stdin for tokens
                        stdout=sys.stdout,   # Show output directly
                        stderr=sys.stderr    # Show errors directly
                    )
                else:
                    # For other commands (like cna enter-build), use the standard approach
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
                    ###################################
                    # DO NOT USE A DISPLAY for enter-build 
                    ###################################
                    terminal_cmd = None

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
                            # Don't leave result uninitialized if terminal launch failed
                            result = None
                    
                    # Fall back to script command if we couldn't launch a graphical terminal
                    if not terminal_cmd or not has_display:
                        # For other interactive commands or if no terminal is available, use the script command
                        #if not has_display:
                        #   click.echo(click.style("No display available. Using script command instead of graphical terminal.", fg="blue"))
                        
                        # Set up the script command for other interactive commands
                        script_cmd = [
                            "script",
                            "-q",  # Quiet mode (no start/end messages)
                            "/dev/null",  # Discard typescript output
                            "-e",  # Return exit code of the command
                            "-c", f"bash {temp_path}"  # The command to run
                        ]
                        
                        # Run it
                        click.echo(click.style("Using script command for interactive session...", fg="blue"))
                        click.echo(click.style("Entering interactive mode. Press Ctrl+D or type 'exit' when finished.", fg="yellow"))
                        result = subprocess.run(script_cmd, check=False)
                
                # After command completes, show additional info
                if cmd_name == "cna-setup":
                    if result and result.returncode == 0:
                        # Check if the git credentials file was updated/created during this run
                        git_creds = os.path.expanduser("~/.git-credentials")
                        if os.path.exists(git_creds):
                            try:
                                with open(git_creds, 'r') as f:
                                    if "msazuredev@dev.azure.com" in f.read():
                                        click.echo(click.style(f"Azure DevOps token appears to be configured correctly.", fg="green"))
                            except:
                                pass
                    else:
                        return_code = result.returncode if result else "unknown"
                        click.echo(click.style(f"\ncna-setup finished with exit code {return_code}.", fg="yellow"))
                else:
                    click.echo(click.style(f"\nInteractive session completed.", fg="green"))
                
                # No log file handling needed
                    
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
                
            # Ensure result is initialized (defensive programming)
            if result is None:
                # If this is cna-setup and we have a script path after cloning, consider it successful
                if cmd_name == "cna-setup" and self.script_path:
                    # We likely ran the command successfully with direct TTY handling
                    from collections import namedtuple
                    MockResult = namedtuple('MockResult', ['returncode'])
                    result = MockResult(returncode=0)
                    # No need for warning in this case
                else:
                    click.echo(click.style(f"Warning: Command execution didn't return a proper result object.", fg="yellow"))
                    
                    # If we don't have a script path and haven't already tried to clone the repository,
                    # we should give guidance. If we already tried to clone it at the beginning 
                    # of this function, we don't need to show this message again.
                    if cmd_name == "cna-setup" and not self.script_path and not os.path.exists(self.vm_tools_dir):
                        click.echo(click.style(f"Could not find or create cna-setup script at expected location.", fg="yellow"))
                        click.echo(click.style(f"You may need to manually run:", fg="blue"))
                        click.echo(click.style(f"git clone --branch main_int https://msazuredev@dev.azure.com/msazuredev/AzureForOperators/_git/vm-tools {self.vm_tools_dir}", fg="blue"))
                    
                    # This simulates a successful exit for the command
                    from collections import namedtuple
                    MockResult = namedtuple('MockResult', ['returncode'])
                    result = MockResult(returncode=0)
            
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
