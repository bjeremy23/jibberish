#!/usr/bin/env python
"""
Unittest-based test script for testing the change_partner_command plugin of Jibberish shell.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the plugin to test
from plugins import change_partner_command
from tests.utils.test_utils import CaptureOutput, mock_click_echo

class TestChangePartnerCommand(unittest.TestCase):
    """Tests for the ChangePartnerCommand plugin."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Create an instance of the plugin
        self.change_partner_cmd = change_partner_command.ChangePartnerPlugin()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Mock chat.change_partner function
        self.change_partner_patcher = patch('plugins.change_partner_command.chat.change_partner')
        self.mock_change_partner = self.change_partner_patcher.start()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Stop the patchers
        self.click_echo_patcher.stop()
        self.change_partner_patcher.stop()
    
    def test_can_handle(self):
        """Test the can_handle method."""
        # Should handle ':)' commands
        self.assertTrue(self.change_partner_cmd.can_handle(":) Batman"), 
                      "Should handle ':) Batman'")
        self.assertTrue(self.change_partner_cmd.can_handle(":) GPT-4"), 
                      "Should handle ':) GPT-4'")
        
        # Should not handle other commands
        self.assertFalse(self.change_partner_cmd.can_handle("ls"), 
                       "Should not handle 'ls'")
        self.assertFalse(self.change_partner_cmd.can_handle("Batman"), 
                       "Should not handle 'Batman'")
    
    def test_execute_change_partner_normal(self):
        """Test changing to a normal partner."""
        # Change to a partner
        with CaptureOutput() as output:
            result = self.change_partner_cmd.execute(":) Batman")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that change_partner was called with the correct name
        # The implementation adds a leading space when parsing the command
        self.mock_change_partner.assert_called_once_with(" Batman")
        
        # Check that output contains confirmation
        self.assertIn("talking with", output.stdout_content, 
                    "Output should confirm change")
        self.assertIn("Batman", output.stdout_content, 
                    "Output should contain partner name")
    
    def test_execute_empty_partner(self):
        """Test changing with an empty partner name."""
        # Try to change with empty name
        with CaptureOutput() as output:
            result = self.change_partner_cmd.execute(":)")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Based on the implementation, chat.change_partner would be called with empty string
        self.mock_change_partner.assert_called_once_with("")
        
        # Check that output contains the empty partner name
        self.assertIn("talking with ", output.stdout_content,
                    "Output should indicate change without partner name")

if __name__ == '__main__':
    # Run the test
    unittest.main()
