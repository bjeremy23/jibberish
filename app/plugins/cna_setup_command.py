"""
Plugin for running the cna-setup command in Jibberish.
This plugin executes the cna-setup.sh script from the .vm-tools directory.
The script is designed to be sourced, not executed directly.
"""
import os
import sys
import subprocess
import click

# Add the parent directory to sys.path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.plugin_system import BuiltinCommand, BuiltinCommandRegistry
from app.utils import is_debug_enabled

class CNASetupPlugin(BuiltinCommand):
    """Command plugin for running cna-setup functionality."""
    
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
        return len(command) > 0 and command[0] in ["cna-setup", "cna_setup"]
    
    def execute(self, command):
        """Execute the cna-setup command."""
        # Parse arguments (everything after "cna-setup")
        args = command.strip().split()
        cmd_name = args[0]  # This will be "cna-setup"
        if len(args) > 1:
            script_args = args[1:]
        else:
            script_args = []
        
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

# First check if a bash function exists for cna-setup
if type -t cna-setup >/dev/null || type -t cna_setup >/dev/null; then
    echo "Found cna-setup function in bash environment, executing..."
    if type -t cna-setup >/dev/null; then
        cna-setup {' '.join(script_args)}
    else
        cna_setup {' '.join(script_args)}
    fi
    exit $?
fi

# If we get here, the function wasn't found, so try executing the script directly
# But the script is meant to be sourced, not executed, so we need to be careful

# Create a proper setup function that matches the bash version
cna_setup() {{
    # Ensure CNA_TOOLS is set correctly to match bash behavior
    if [ -z "$CNA_TOOLS" ]; then
        echo "Cloning latest vm-tools..."
        git clone --branch main_int https://msazuredev@dev.azure.com/msazuredev/AzureForOperators/_git/vm-tools /localdata/$USER/.vm-tools
        export CNA_TOOLS=/localdata/$USER/.vm-tools
    fi
    
    # Source the script after setting CNA_TOOLS
    if [ -f "{self.script_path}" ]; then
        # The script is designed to be sourced not executed
        source "{self.script_path}"
    else
        echo "ERROR: Could not find {self.script_path}"
        return 1
    fi
}}

# Now execute the function we just created
cna_setup {' '.join(script_args)}
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
            
            # Run with stdout and stderr not captured to show output in real-time
            # shell=True helps with certain bash expansions and TTY handling
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
            if result.returncode == 0:
                click.echo(click.style(f"{cmd_name} completed successfully.", fg="green"))
                return True
            else:
                click.echo(click.style(f"{cmd_name} failed with exit code {result.returncode}.", fg="red"))
                return False
            
        except Exception as e:
            click.echo(click.style(f"Error executing {cmd_name}: {str(e)}", fg="red"))
            return False

# Register the plugin
BuiltinCommandRegistry.register(CNASetupPlugin())
