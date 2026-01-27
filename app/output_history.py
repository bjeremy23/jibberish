"""
Output History Module for Jibberish Shell

This module stores command outputs to enable referencing previous command results
in subsequent AI queries. Users can reference previous outputs using:
- $_ or @0 - the most recent command output
- @1, @2, etc. - older outputs (1 = second most recent, etc.)

The history is stored in memory and resets when the shell exits.
"""

from collections import deque
from datetime import datetime

# Maximum number of command outputs to store
MAX_OUTPUT_HISTORY = 10

# Store outputs as a deque for efficient append/pop operations
# Each entry is a dict with: command, output, timestamp, return_code
_output_history = deque(maxlen=MAX_OUTPUT_HISTORY)


def store_output(command: str, output: str, return_code: int = 0):
    """
    Store a command's output in the history.
    
    Args:
        command: The command that was executed
        output: The stdout output from the command
        return_code: The return code (0 = success)
    """
    # Skip empty outputs or failed commands with no useful output
    if not output or not output.strip():
        return
    
    # Truncate very long outputs to avoid memory issues
    max_output_length = 50000  # ~50KB max per output
    if len(output) > max_output_length:
        output = output[:max_output_length] + "\n... [output truncated]"
    
    entry = {
        "command": command,
        "output": output.strip(),
        "timestamp": datetime.now().isoformat(),
        "return_code": return_code
    }
    
    _output_history.appendleft(entry)  # Most recent first


def get_output(index: int = 0) -> dict | None:
    """
    Get a specific output from history by index.
    
    Args:
        index: 0 = most recent, 1 = second most recent, etc.
        
    Returns:
        dict with command, output, timestamp, return_code or None if not found
    """
    if 0 <= index < len(_output_history):
        return _output_history[index]
    return None


def get_last_output() -> str | None:
    """
    Get the most recent command output (convenience function for $_).
    
    Returns:
        The output string or None if no history
    """
    entry = get_output(0)
    return entry["output"] if entry else None


def get_last_command() -> str | None:
    """
    Get the most recent command that was executed.
    
    Returns:
        The command string or None if no history
    """
    entry = get_output(0)
    return entry["command"] if entry else None


def get_output_context_for_ai(max_entries: int = 3) -> str | None:
    """
    Generate a context string for the AI containing recent command outputs.
    
    This provides the AI with context about what commands have run and their
    outputs, enabling it to reference this information when generating new commands.
    
    Args:
        max_entries: Maximum number of recent outputs to include
        
    Returns:
        Formatted context string or None if no history
    """
    if not _output_history:
        return None
    
    entries = list(_output_history)[:max_entries]
    
    context_parts = ["Recent command outputs (available via @0, @1, etc.):"]
    
    for i, entry in enumerate(entries):
        # Limit output preview to avoid huge context
        output_preview = entry["output"]
        if len(output_preview) > 500:
            output_preview = output_preview[:500] + "... [truncated]"
        
        context_parts.append(
            f"\n@{i} (command: {entry['command']}):\n{output_preview}"
        )
    
    return "\n".join(context_parts)


def parse_output_reference(text: str) -> tuple[bool, str]:
    """
    Check if text contains output references like $_ or @n and expand them.
    
    Args:
        text: The user input text
        
    Returns:
        tuple of (has_reference: bool, expanded_text: str)
    """
    import re
    
    has_reference = False
    result = text
    
    # Pattern for @n references (e.g., @0, @1, @2)
    at_pattern = r'@(\d+)'
    
    # Pattern for $_ reference (bash-like last output)
    underscore_pattern = r'\$_'
    
    # Check for $_ and replace with @0 equivalent
    if re.search(underscore_pattern, result):
        output = get_last_output()
        if output:
            result = re.sub(underscore_pattern, f"[Previous output: {output[:200]}...]" if len(output) > 200 else f"[Previous output: {output}]", result)
            has_reference = True
    
    # Check for @n references
    matches = re.findall(at_pattern, result)
    for match in matches:
        index = int(match)
        entry = get_output(index)
        if entry:
            output = entry["output"]
            preview = f"[Output from '{entry['command']}': {output[:200]}...]" if len(output) > 200 else f"[Output from '{entry['command']}': {output}]"
            result = re.sub(f'@{index}\\b', preview, result, count=1)
            has_reference = True
    
    return has_reference, result


def has_output_reference(text: str) -> bool:
    """
    Quick check if text contains any output references.
    
    Args:
        text: The user input text
        
    Returns:
        True if contains $_ or @n references
    """
    import re
    return bool(re.search(r'\$_|@\d+', text))


def clear_history():
    """Clear all stored output history."""
    _output_history.clear()


def get_history_size() -> int:
    """Get the current number of stored outputs."""
    return len(_output_history)


def list_available_outputs() -> list[dict]:
    """
    List all available outputs with their indices.
    
    Returns:
        List of dicts with index, command preview, and output preview
    """
    result = []
    for i, entry in enumerate(_output_history):
        cmd_preview = entry["command"][:50] + "..." if len(entry["command"]) > 50 else entry["command"]
        out_preview = entry["output"][:100] + "..." if len(entry["output"]) > 100 else entry["output"]
        result.append({
            "index": i,
            "reference": f"@{i}" if i > 0 else "@0 or $_",
            "command": cmd_preview,
            "output_preview": out_preview
        })
    return result
