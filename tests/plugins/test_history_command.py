#!/usr/bin/env python
"""
Unittest-based test script for testing the history_command plugin of Jibberish shell.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the plugin to test
from plugins import history_command
from tests.utils.test_utils import CaptureOutput, mock_click_echo

class TestHistoryCommand(unittest.TestCase):
    """Tests for the HistoryCommand plugin."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Create an instance of the plugin
        self.history_cmd = history_command.HistoryCommand()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Mock the history module's list_history function
        self.list_history_patcher = patch('history.list_history')
        self.mock_list_history = self.list_history_patcher.start()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Stop the patchers
        self.click_echo_patcher.stop()
        self.list_history_patcher.stop()
    
    def test_can_handle(self):
        """Test the can_handle method."""
        # Should handle 'history' command
        self.assertTrue(self.history_cmd.can_handle("history"), 
                      "Should handle 'history'")
        
        # Should not handle other commands
        self.assertFalse(self.history_cmd.can_handle("ls"), 
                       "Should not handle 'ls'")
        self.assertFalse(self.history_cmd.can_handle("!3"), 
                       "Should not handle '!3'")
    
    def test_execute_history(self):
        """Test executing history command."""
        with CaptureOutput() as output:
            result = self.history_cmd.execute("history")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that list_history was called
        self.mock_list_history.assert_called_once()

if __name__ == '__main__':
    # Run the test
    unittest.main()
