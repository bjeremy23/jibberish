import readline, click, os, glob

def complete_path(text, state):
    if text.startswith('~'):
        # Expand '~' to the user's home directory and remove the '~' from the beginning of the text 
        text = os.path.expanduser(text)

    # Get all matching paths (both files and directories)
    matches = glob.glob(text + '*')
    
    #if a match is a directory, add a '/' to the end of the match if one does not already exist
    matches = [f"{match}/" if os.path.isdir(match) and not match.endswith('/') else match for match in matches]

    #remove duplicates an list in order sorted by the length of the command
    # the smallest command length being last
    matches = sorted(list(set(matches)), key=len)

    return (matches + [None])[state]

def complete_command(text, state):
    # Get all executables in the PATH
    paths = os.environ.get('PATH', '').split(os.pathsep)
    commands = []
    for path in paths:
        if os.path.isdir(path):
            commands.extend(os.listdir(path))

    # Filter commands based on the input text
    matches = [cmd for cmd in commands if cmd.startswith(text)]

    # remove duplicates an list in order sorted by the length of the command
    # the smallest command length being last
    matches = sorted(list(set(matches)), key=len)

    return (matches + [None])[state]

# Global variables for display completion
_completion_matches = []
_display_hooks_set = False

# Custom display function for completions
def _display_completions_hook(substitution, matches, longest_match_length):
    # Get the current line content
    line_buffer = readline.get_line_buffer()
    
    # Print a newline to move away from the prompt
    print("\n", end="")
    
    # Get the basenames for display
    display_matches = []
    for match in matches:
        if os.path.isdir(match.rstrip('/')):  # Check if it's a directory (remove trailing slash for checking)
            # It's a directory
            basename = os.path.basename(match.rstrip('/')) + '/'
            display_matches.append(basename)
        else:
            # It's a file or command
            if '/' in match:
                # It's a file, show just the basename
                basename = os.path.basename(match)
                display_matches.append(basename)
            else:
                # It's a command or other non-path
                display_matches.append(match)
    
    # Determine column width for nice display
    col_width = max(len(m) for m in display_matches) + 2
    term_width = os.get_terminal_size().columns
    cols_per_line = max(1, term_width // col_width)
    
    # Print matches in columns
    for i, name in enumerate(display_matches):
        if i > 0 and i % cols_per_line == 0:
            print()  # Start a new line after every 'cols_per_line' items
        print(f"{name:<{col_width}}", end="")
    
    # Get the current directory for the prompt
    try:
        current_directory = os.getcwd()
        # Print two newlines and the prompt with the original input
        print(f"\n\n{current_directory}# {line_buffer}", end="")
    except:
        # Fallback if we can't get the current directory
        print(f"\n\n# {line_buffer}", end="")
    
    # Return True to tell readline we've handled the display completely
    return True

def custom_completer(text, state):
    global _completion_matches, _display_hooks_set
    buffer = readline.get_line_buffer()
    line = buffer[:readline.get_endidx()]
    
    # Set up display hook if not already done
    if not _display_hooks_set:
        # This line will only work on some platforms with readline support
        # On some systems it might require alternative approach
        try:
            readline.set_completion_display_matches_hook(_display_completions_hook)
            _display_hooks_set = True
        except (AttributeError, RuntimeError):
            # If the hook isn't available, we'll just use the default display
            pass
    
    # Only regenerate matches when state is 0 (first call for this text)
    if state == 0:
        _completion_matches = []
        # Check if we're completing a cd command
        cmd_prefix = buffer[:buffer.find(text)].strip()
        completing_cd = cmd_prefix in ['cd', 'cd ', 'pushd', 'pushd ']
        
        # First check if it matches any files or directories
        expanded_text = os.path.expanduser(text)
        
        # Handle directories correctly
        if '/' in expanded_text:
            # For paths with directories, split into directory and filename parts
            dirname, basename = os.path.split(expanded_text)
            if not dirname:  # Handle case where path starts with /
                dirname = "/"
            
            # Normalize dirname (remove trailing slash if it exists)
            if dirname != "/" and dirname.endswith('/'):
                dirname = dirname[:-1]
                
            # Check if dirname exists and is a directory
            if os.path.isdir(dirname):
                # Get files within the directory that match the basename prefix
                search_path = os.path.join(dirname, basename + '*')
                path_matches = glob.glob(search_path)
            else:
                path_matches = []
        else:
            # Simple path completion
            path_matches = glob.glob(expanded_text + '*')
            
        path_matches = sorted(list(set(path_matches)), key=len)
        
        if path_matches:
            for match in path_matches:
                if os.path.isdir(match):
                    _completion_matches.append(match + '/')  # Add trailing slash for directories
                elif not completing_cd:  # Only add non-directories if not completing a cd command
                    _completion_matches.append(match)        # Use as is for files
        elif not (completing_cd or '/' in text):
            # Only show command completions if:
            # 1. Not completing a path (doesn't contain '/')
            # 2. Not explicitly doing a cd/pushd command
            paths = os.environ.get('PATH', '').split(os.pathsep)
            commands = set()
            for path in paths:
                if os.path.isdir(path):
                    try:
                        for cmd in os.listdir(path):
                            full_path = os.path.join(path, cmd)
                            if os.access(full_path, os.X_OK) and not os.path.isdir(full_path):
                                commands.add(cmd)
                    except (PermissionError, OSError):
                        pass
            _completion_matches.extend(sorted([cmd for cmd in commands if cmd.startswith(text)], key=len))
    
    # Return the result based on state
    if state < len(_completion_matches):
        return _completion_matches[state]  # Return the full match
    else:
        return None
    
def word_break_hook():
    return ' \t\n`!@#$%^&*()=+[{]}\\|;:\'",<>?'

# Set up the readline completer
readline.set_completer(custom_completer)
readline.set_completer_delims(word_break_hook())
readline.parse_and_bind('tab: complete')

# Enable command history
histfile = os.path.join(os.path.expanduser("~"), ".cli_history")
try:
    readline.read_history_file(histfile)
except FileNotFoundError:
    pass

import atexit
atexit.register(readline.write_history_file, histfile)

# Function to list command history
def list_history():
    """
    List the command history
    """
    history_length = readline.get_current_history_length()
    for i in range(1, history_length + 1):
       print(f"{i}: {readline.get_history_item(i)}")

def get_history_item(index):
    """
    Get the command from the history list
    """
    return readline.get_history_item(index)

def get_history(command):
    """
    Get the command from the history.
    Handles both numeric indices (e.g., !3) and partial text searches (e.g., !cd).
    """
    search_term = command[1:]  # Remove the '!' prefix
    
    try:
        # First try to interpret as a numeric index
        if search_term.isdigit():
            history_index = int(search_term)
            history_command = get_history_item(history_index)
            if history_command is None:
                click.echo(click.style(f"No command found at history index {history_index}", fg="red"))
                return None
            click.echo(click.style(f"{history_command}", fg="blue"))
            return history_command
        
        # If not a number, search for the most recent command starting with the search term
        else:
            history_length = readline.get_current_history_length()
            # Search through history from most recent to oldest
            for i in range(history_length, 0, -1):
                history_item = get_history_item(i)
                if history_item and history_item.startswith(search_term):
                    click.echo(click.style(f"{history_item}", fg="blue"))
                    return history_item
            
            # If no match found
            click.echo(click.style(f"No command starting with '{search_term}' found in history", fg="red"))
            return None
    except Exception as e:
        click.echo(click.style(f"Error accessing history: {str(e)}", fg="red"))
        return None

