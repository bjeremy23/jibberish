import readline, click, os, glob

def complete_path(text, state):
    if text.startswith('~'):
        # Expand '~' to the user's home directory and remove the '~' from the beginning of the text 
        text = os.path.expanduser(text)

    # Get all matching paths (both files and directories)
    matches = glob.glob(text + '*')
    
    #if a match is a directory, add a '/' to the end of the match if one does not already exist
    matches = [f"{match}/" if os.path.isdir(match) and not match.endswith('/') else match for match in matches]

    return (matches + [None])[state]

def custom_completer(text, state):
    buffer = readline.get_line_buffer()
    line = buffer[:readline.get_endidx()]
    # Extract the part of the line after the command
    if ' ' in line:
        text = line.split(' ', 1)[1]
    return complete_path(text, state)

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
    Get the command from the history
    """
    try:
        history_index = int(command[1:])
        command = get_history_item(history_index).strip()
        if command is None:
            click.echo(click.style(f"No command found at history index {history_index}", fg="red"))
            return None
        click.echo(click.style(command, fg="blue"))
        return command
    except:
        click.echo(click.style("Invalid history index", fg="red"))
        return None

