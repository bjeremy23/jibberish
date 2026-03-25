"""
Outputs Command Plugin

Displays the list of available command outputs that can be referenced
using @0, @1, @2, etc. or $_ syntax in AI commands.

Usage:
    outputs      - Show all available outputs
    outputs -v   - Show outputs with full content preview
"""

import re
import click
from app.plugin_system import BuiltinCommand, BuiltinCommandRegistry

# Matches ANSI/VT escape sequences (CSI, OSC, single-char escapes, etc.)
_ANSI_ESCAPE = re.compile(
    r'\x1b(?:'
    r'\[[0-9;:<=>?]*[ -/]*[@-~]'   # CSI sequences
    r'|\][^\x07\x1b]*(?:\x07|\x1b\\)'  # OSC sequences
    r'|[PX^_][^\x1b]*\x1b\\'       # DCS/PM/APC/SOS
    r'|[^[\]PX^_]'                 # other Esc+single-char (e.g. \x1b= \x1b>)
    r')'
)


class OutputsPlugin(BuiltinCommand):
    """Plugin to display available command output history."""
    
    # Plugin attributes
    plugin_name = "outputs_command"
    is_required = False
    is_enabled = True
    
    def can_handle(self, command: str) -> bool:
        """Check if this plugin should handle the command."""
        cmd = command.strip().lower()
        return cmd in ['outputs', 'output', '@'] or cmd.startswith('outputs ')
    
    def execute(self, command: str) -> tuple:
        """
        Display available command outputs.
        
        Returns:
            tuple: (handled: bool, new_command: str or None)
        """
        from app.output_history import list_available_outputs, get_output
        
        # Check for verbose flag
        verbose = '-v' in command or '--verbose' in command
        
        outputs = list_available_outputs()
        
        if not outputs:
            click.echo(click.style("No command outputs stored yet.", fg="yellow"))
            click.echo("Run some commands and their outputs will be available for reference.")
            return (True, None)
        
        click.echo(click.style(f"\nAvailable Command Outputs ({len(outputs)} stored):", fg="blue", bold=True))
        click.echo(click.style("-" * 50, fg="blue"))
        
        for item in outputs:
            idx = item['index']
            ref = item['reference']
            cmd = item['command']
            
            # Color code: @0 is green (most recent), others are cyan
            ref_color = "green" if idx == 0 else "cyan"
            
            click.echo(
                click.style(f"  {ref:12}", fg=ref_color, bold=True) + 
                click.style(f" → ", fg="white") +
                click.style(f"{cmd}", fg="white")
            )
            
            if verbose:
                # Show more of the output in verbose mode
                entry = get_output(idx)
                if entry:
                    # Strip terminal control sequences so TUI output (vi, htop, etc.)
                    # doesn't corrupt the display
                    clean = _ANSI_ESCAPE.sub('', entry['output']).replace('\r', '')
                    output_preview = clean if len(clean) <= 300 else clean[:300] + "..."
                    # Indent the output preview
                    for line in output_preview.split('\n')[:5]:
                        click.echo(click.style(f"               {line}", fg="white", dim=True))
                    if clean.count('\n') >= 5:
                        click.echo(click.style(f"               ... (more lines)", fg="white", dim=True))
                click.echo()
        
        click.echo()
        click.echo(click.style("Usage: ", fg="yellow") + "Reference these in commands with #compress @0 or ?analyze those files")
        click.echo(click.style("Tip: ", fg="yellow") + "Use 'outputs -v' for verbose output preview")
        
        return (True, None)


# Register the plugin
BuiltinCommandRegistry.register(OutputsPlugin())
