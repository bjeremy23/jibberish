#!/usr/bin/env python
"""
Unittest-based test script for testing the history_retrieval_command plugin of Jibberish shell.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the plugin to test
from plugins import history_retrieval_command
from tests.utils.test_utils import CaptureOutput, mock_click_echo

class TestHistoryRetrievalCommand(unittest.TestCase):
    """Tests for the HistoryRetrievalPlugin plugin."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Create an instance of the plugin
        self.history_retrieval_cmd = history_retrieval_command.HistoryRetrievalPlugin()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Mock history module's get_history function
        # Return mock commands for different history retrievals
        self.history_patcher = patch('history.get_history', side_effect=lambda cmd: 
            "ls -la" if cmd == "!3" else 
            "cd /tmp" if cmd == "!cd" else
            None)
        self.mock_history = self.history_patcher.start()
        
        # Mock the BuiltinCommandRegistry
        self.registry_patcher = patch.object(
            history_retrieval_command.BuiltinCommandRegistry, 
            '_plugins', 
            [MagicMock(can_handle=lambda cmd: cmd.startswith('#'), execute=lambda cmd: True)]
        )
        self.mock_registry = self.registry_patcher.start()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Stop the patchers
        self.click_echo_patcher.stop()
        self.history_patcher.stop()
        self.registry_patcher.stop()
    
    def test_can_handle(self):
        """Test the can_handle method."""
        # Should handle '!' commands
        self.assertTrue(self.history_retrieval_cmd.can_handle("!3"), 
                      "Should handle '!3'")
        self.assertTrue(self.history_retrieval_cmd.can_handle("!ls"), 
                      "Should handle '!ls'")
        
        # Should not handle other commands
        self.assertFalse(self.history_retrieval_cmd.can_handle("ls"), 
                       "Should not handle 'ls'")
        self.assertFalse(self.history_retrieval_cmd.can_handle("history"), 
                       "Should not handle 'history'")
    
    def test_execute_with_numeric_index(self):
        """Test retrieving a command by numeric index."""
        # Get command by index
        result, command = self.history_retrieval_cmd.execute("!3")
        
        # Check that history.get_history was called
        self.mock_history.assert_called_once_with("!3")
        
        # Check the result
        self.assertFalse(result, "Expected False to let the main loop process the command")
        self.assertEqual(command, "ls -la", f"Expected 'ls -la' but got '{command}'")
    
    def test_execute_with_text_search(self):
        """Test retrieving a command by text search."""
        # Get command by text
        result, command = self.history_retrieval_cmd.execute("!cd")
        
        # Check that history.get_history was called
        self.mock_history.assert_called_once_with("!cd")
        
        # Check the result
        self.assertFalse(result, "Expected False to let the main loop process the command")
        self.assertEqual(command, "cd /tmp", f"Expected 'cd /tmp' but got '{command}'")
    
    def test_execute_with_not_found(self):
        """Test retrieving a command that doesn't exist."""
        # Try to get a nonexistent command
        result = self.history_retrieval_cmd.execute("!nonexistent")
        
        # Check that history.get_history was called
        self.mock_history.assert_called_once_with("!nonexistent")
        
        # When the command is not found, result should be True to indicate it was handled
        self.assertTrue(result, "Expected True to indicate the command was handled")
    
    def test_execute_ai_command_from_history(self):
        """Test retrieving an AI command from history."""
        # Mock get_history to return an AI command
        self.history_patcher.stop()
        self.history_patcher = patch('history.get_history', 
                                   side_effect=lambda cmd: "#find large files" if cmd == "!4" else None)
        self.mock_history = self.history_patcher.start()
        
        # Get AI command from history
        result = self.history_retrieval_cmd.execute("!4")
        
        # Check that history.get_history was called
        self.mock_history.assert_called_once_with("!4")
        
        # The AI command plugin should have handled it
        self.assertTrue(result, "Expected True from the AI command plugin")

if __name__ == '__main__':
    # Run the test
    unittest.main()
