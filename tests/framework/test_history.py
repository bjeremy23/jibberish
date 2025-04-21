#!/usr/bin/env python
"""
Unittest-based test script for testing the history module of Jibberish shell.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the module to test
import history
from tests.utils.test_utils import create_mock_environment, cleanup_mock_environment

class TestHistory(unittest.TestCase):
    """Tests for the history module."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Create a mock environment
        self.env = create_mock_environment()
        
        # Mock readline related functions
        self.readline_patcher = patch.multiple(
            history.readline,
            get_current_history_length=MagicMock(return_value=3),
            get_history_item=MagicMock(side_effect=lambda i: [None, "ls -la", "cd /tmp", "echo test"][i]),
            parse_and_bind=MagicMock(),
            set_completer=MagicMock(),
            set_completer_delims=MagicMock()
        )
        self.mock_readline = self.readline_patcher.start()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Stop the patchers and clean up
        self.readline_patcher.stop()
        cleanup_mock_environment(self.env)
    
    def test_list_history(self):
        """Test the list_history function."""
        with patch('builtins.print') as mock_print:
            history.list_history()
            # Check that print was called for each history item
            self.assertGreaterEqual(mock_print.call_count, 3, 
                                  f"Expected at least 3 calls but got {mock_print.call_count}")
    
    def test_get_history_item(self):
        """Test the get_history_item function."""
        item = history.get_history_item(1)
        self.assertEqual(item, "ls -la", f"Expected 'ls -la' but got '{item}'")
        
        item = history.get_history_item(2)
        self.assertEqual(item, "cd /tmp", f"Expected 'cd /tmp' but got '{item}'")
        
        item = history.get_history_item(3)
        self.assertEqual(item, "echo test", f"Expected 'echo test' but got '{item}'")
    
    def test_get_history_by_number(self):
        """Test the get_history function with a numeric index."""
        with patch('click.echo'):
            cmd = history.get_history("!2")
            self.assertEqual(cmd, "cd /tmp", f"Expected 'cd /tmp' but got '{cmd}'")
    
    def test_get_history_invalid_index(self):
        """Test the get_history function with an invalid index."""
        with patch('click.echo'):
            cmd = history.get_history("!99")
            self.assertIsNone(cmd, f"Expected None but got '{cmd}'")
    
    def test_get_history_invalid_format(self):
        """Test the get_history function with an invalid format."""
        with patch('click.echo'):
            cmd = history.get_history("!abc")
            self.assertIsNone(cmd, f"Expected None but got '{cmd}'")

if __name__ == '__main__':
    unittest.main()
