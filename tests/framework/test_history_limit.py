#!/usr/bin/env python
"""
Unittest-based test script for testing the history_limit module of Jibberish shell.
"""
import unittest
import os
import tempfile
import readline
import sys
import io
from unittest.mock import patch, MagicMock

# Import the test_helper module for utility functions
# Add parent directory to path so we can import the history module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from tests import test_helper
from app import history

class TestHistoryLimit(unittest.TestCase):
    def setUp(self):
        # Create a temporary history file for testing
        self.temp_histfile = tempfile.mktemp()
        # Save the original histfile path
        self.original_histfile = history.histfile
        # Replace the histfile path with our temporary one
        history.histfile = self.temp_histfile
        # Save any existing MAX_HISTORY_LINES environment variable
        self.original_max_history = os.environ.get('MAX_HISTORY_LINES')
        # Set a default value for testing
        os.environ['MAX_HISTORY_LINES'] = '2000'
        # Clear any existing history
        readline.clear_history()

    def tearDown(self):
        # Clean up: Restore original histfile path
        history.histfile = self.original_histfile
        # Restore original MAX_HISTORY_LINES environment variable
        if self.original_max_history is not None:
            os.environ['MAX_HISTORY_LINES'] = self.original_max_history
        else:
            if 'MAX_HISTORY_LINES' in os.environ:
                del os.environ['MAX_HISTORY_LINES']
        # Remove the temporary history file if it exists
        if os.path.exists(self.temp_histfile):
            os.remove(self.temp_histfile)
        # Clear history
        readline.clear_history()

    def test_limit_history_size(self):
        """Test that history is limited to max_lines (2000 by default)"""
        # Temporarily restore original add_history function to avoid auto-limiting
        # during our test setup
        original_add_history = history.original_add_history
        temp_add_history = readline.add_history
        readline.add_history = original_add_history
        
        try:
            # Add 2500 items to history (more than our limit of 2000)
            for i in range(1, 2501):
                readline.add_history(f"test command {i}")
                
            # Verify we have 2500 items
            self.assertEqual(readline.get_current_history_length(), 2500)
            
            # Call the function to limit history size
            history.limit_history_size(2000)
            
            # Check that we now have exactly 2000 items
            self.assertEqual(readline.get_current_history_length(), 2000)
            
            # Verify the oldest items were removed and newest were kept
            # The first item should now be "test command 501" 
            # (since we removed the oldest 500 items)
            self.assertEqual(readline.get_history_item(1), "test command 501")
            
            # The last item should be "test command 2500"
            self.assertEqual(
                readline.get_history_item(readline.get_current_history_length()), 
                "test command 2500"
            )
        finally:
            # Restore our custom add_history function
            readline.add_history = temp_add_history

    def test_history_limit_at_exit(self):
        """Test that history is limited when the program exits"""
        # Add 2500 items to history (more than our limit of 2000)
        for i in range(1, 2501):
            readline.add_history(f"test command {i}")
        
        # Simulate program exit by calling the registered atexit functions
        # Note: We're not calling all atexit handlers, just the ones we know about
        history.limit_history_size()  # Should use value from environment (2000)
        readline.write_history_file(history.histfile)
        
        # Clear the history
        readline.clear_history()
        
        # Read back the history file and check its content
        readline.read_history_file(history.histfile)
        
        # Check that we have exactly 2000 items
        self.assertEqual(readline.get_current_history_length(), 2000)
        
        # Verify the oldest items were removed and newest were kept
        # The first item should now be "test command 501" 
        # (since we removed the oldest 500 items)
        self.assertEqual(readline.get_history_item(1), "test command 501")
        
        # The last item should be "test command 2500"
        self.assertEqual(
            readline.get_history_item(readline.get_current_history_length()), 
            "test command 2500"
        )
        
    def test_environment_variable(self):
        """Test that the MAX_HISTORY_LINES environment variable is respected"""
        # Set a custom history limit
        os.environ['MAX_HISTORY_LINES'] = '1000'
        
        # Temporarily restore original add_history function to avoid auto-limiting
        original_add_history = history.original_add_history
        temp_add_history = readline.add_history
        readline.add_history = original_add_history
        
        try:
            # Add 1500 items to history (more than our limit of 1000)
            for i in range(1, 1501):
                readline.add_history(f"test command {i}")
                
            # Verify we have 1500 items (since we bypassed the limit)
            self.assertEqual(readline.get_current_history_length(), 1500)
            
            # Now call limit_history_size to apply the limit from the environment
            history.limit_history_size()
            
            # Check that we now have exactly 1000 items (our environment limit)
            self.assertEqual(readline.get_current_history_length(), 1000)
            
            # Verify the oldest items were removed and newest were kept
            # The first item should now be "test command 501" 
            # (since we removed the oldest 500 items)
            self.assertEqual(readline.get_history_item(1), "test command 501")
            
            # The last item should be "test command 1500"
            self.assertEqual(
                readline.get_history_item(readline.get_current_history_length()), 
                "test command 1500"
            )
        finally:
            # Restore our custom add_history function
            readline.add_history = temp_add_history
        
    def test_invalid_environment_variable(self):
        """Test handling of invalid MAX_HISTORY_LINES environment variable value"""
        # Set an invalid history limit
        os.environ['MAX_HISTORY_LINES'] = 'not_a_number'
        
        # Temporarily restore original add_history function to avoid auto-limiting
        original_add_history = history.original_add_history
        temp_add_history = readline.add_history
        readline.add_history = original_add_history
        
        try:
            # Add items to history
            for i in range(1, 101):
                readline.add_history(f"test command {i}")
                
            # Capture stdout to check for warning message
            with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                max_lines = history.get_max_history_lines()
                
            # Verify that the default value is returned and a warning is printed
            self.assertEqual(max_lines, 2000)
            self.assertIn("Warning:", fake_stdout.getvalue())
        finally:
            # Restore our custom add_history function
            readline.add_history = temp_add_history
        
    def test_add_history_respects_limit(self):
        """Test that add_history now automatically enforces the history limit"""
        # Set history limit to 5
        os.environ['MAX_HISTORY_LINES'] = '5'
        
        # Clear existing history
        readline.clear_history()
        
        # Add 10 items to history - this should trigger our custom add_history wrapper
        for i in range(1, 11):
            readline.add_history(f"test command {i}")
            
        # Verify we have exactly 5 items (our limit)
        self.assertEqual(readline.get_current_history_length(), 5)
        
        # Verify the oldest items were removed and newest were kept
        # The first item should now be "test command 6" 
        # (since we removed the oldest 5 items)
        self.assertEqual(readline.get_history_item(1), "test command 6")
        
        # The last item should be "test command 10"
        self.assertEqual(
            readline.get_history_item(readline.get_current_history_length()),
            "test command 10"
        )

if __name__ == '__main__':
    unittest.main()
