"""
History command plugin.
"""
import history
from plugin_system import BuiltinCommand, BuiltinCommandRegistry


class HistoryCommand(BuiltinCommand):
    """Plugin for the 'history' and 'h' commands to display command history"""
    
    def can_handle(self, command):
        """Check if this plugin can handle the command"""
        return command.lower() in ["history", "h"]
    
    def execute(self, command):
        """Show the command history"""
        history.list_history()
        return True


# Register the plugin with the registry
BuiltinCommandRegistry.register(HistoryCommand())
