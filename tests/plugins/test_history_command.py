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
from app.plugins import history_command
from tests.utils.test_utils import CaptureOutput, mock_click_echo
from tests import test_helper

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
        self.list_history_patcher = patch('app.history.list_history')
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
    
    def test_can_handle_with_pipe(self):
        """Test can_handle method with piped command."""
        # Should handle 'history | grep command' format
        self.assertTrue(self.history_cmd.can_handle("history | grep test"), 
                      "Should handle 'history | grep test'")
        
        self.assertTrue(self.history_cmd.can_handle("h | grep test"), 
                      "Should handle 'h | grep test'")
        
        # Should not handle other piped commands
        self.assertFalse(self.history_cmd.can_handle("ls | grep test"), 
                       "Should not handle 'ls | grep test'")
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    def test_execute_history_with_pipe(self, mock_unlink, mock_tempfile, mock_subprocess_run):
        """Test executing history command with pipe."""
        # Set up the mocks
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/test_history_file"
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file
        
        # Mock list_history to return a test string
        self.mock_list_history.return_value = "1: command1\n2: command2\n3: command3"
        
        # Execute the command with a pipe
        result = self.history_cmd.execute("history | grep command")
        
        # Verify that the command was handled properly
        self.assertTrue(result, "Should return True to indicate command was handled")
        
        # Check that list_history was called with return_output=True
        self.mock_list_history.assert_called_once_with(return_output=True)
        
        # Check that the temporary file was created and written to
        mock_temp_file.write.assert_called_once_with("1: command1\n2: command2\n3: command3")
        
        # Check that subprocess.run was called with the correct command
        expected_command = f"cat {mock_temp_file.name} | grep command"
        mock_subprocess_run.assert_called_once()
        self.assertEqual(mock_subprocess_run.call_args[0][0], expected_command)
        
        # Check that the temporary file was cleaned up
        mock_unlink.assert_called_once_with(mock_temp_file.name)

if __name__ == '__main__':
    # Run the test
    unittest.main()
