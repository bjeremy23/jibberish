#!/usr/bin/env python
"""
Unittest-based test script for testing the export_command plugin of Jibberish shell.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the plugin to test
from app.plugins import export_command
from tests.utils.test_utils import CaptureOutput, mock_click_echo
from tests import test_helper

class TestExportCommand(unittest.TestCase):
    """Tests for the ExportCommand plugin."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Store original environment variables
        self.original_env = os.environ.copy()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Create an instance of the plugin
        self.export_cmd = export_command.ExportCommand()
        
        # Clear test environment variables if they exist
        for var in ['TEST_VAR1', 'TEST_VAR2', 'TEST_VAR_EMPTY']:
            if var in os.environ:
                del os.environ[var]
    
    def tearDown(self):
        """Clean up after each test method."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Stop the patchers
        self.click_echo_patcher.stop()
    
    def test_can_handle(self):
        """Test the can_handle method."""
        # Should handle 'export' command
        self.assertTrue(self.export_cmd.can_handle("export VAR=value"), 
                      "Should handle 'export VAR=value'")
        self.assertTrue(self.export_cmd.can_handle("export"), 
                      "Should handle 'export'")
        
        # Should not handle other commands
        self.assertFalse(self.export_cmd.can_handle("ls"), 
                       "Should not handle 'ls'")
        self.assertFalse(self.export_cmd.can_handle("echo $VAR"), 
                       "Should not handle 'echo $VAR'")
    
    def test_execute_set_variable(self):
        """Test setting an environment variable."""
        # Set a variable
        with CaptureOutput() as output:
            result = self.export_cmd.execute("export TEST_VAR1=test_value")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that the variable was set
        self.assertIn("TEST_VAR1", os.environ, 
                    "TEST_VAR1 should be set")
        self.assertEqual(os.environ["TEST_VAR1"], "test_value", 
                       f"Expected 'test_value' but got '{os.environ['TEST_VAR1']}'")
        
        # Check that success message was displayed
        self.assertIn("Environment variable TEST_VAR1=test_value", output.stdout_content, 
                    "Output should confirm variable was set")
    
    def test_execute_set_empty_variable(self):
        """Test setting an empty environment variable."""
        # Set an empty variable
        with CaptureOutput() as output:
            result = self.export_cmd.execute("export TEST_VAR_EMPTY=")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that the variable was set to empty
        self.assertIn("TEST_VAR_EMPTY", os.environ, 
                    "TEST_VAR_EMPTY should be set")
        self.assertEqual(os.environ["TEST_VAR_EMPTY"], "", 
                       f"Expected empty string but got '{os.environ['TEST_VAR_EMPTY']}'")
    
    def test_execute_set_quoted_value(self):
        """Test setting a variable with quoted value."""
        # Set a variable with quoted value
        with CaptureOutput() as output:
            result = self.export_cmd.execute('export TEST_VAR2="quoted value with spaces"')
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that the variable was set correctly
        self.assertIn("TEST_VAR2", os.environ, 
                    "TEST_VAR2 should be set")
        self.assertEqual(os.environ["TEST_VAR2"], "quoted value with spaces", 
                       f"Expected 'quoted value with spaces' but got '{os.environ['TEST_VAR2']}'")
    
    def test_execute_list_variables(self):
        """Test listing environment variables."""
        # Set some test variables
        os.environ["TEST_VAR1"] = "test_value1"
        os.environ["TEST_VAR2"] = "test_value2"
        
        # Execute the export command
        result = self.export_cmd.execute("export")
        
        # Check that the result is a tuple indicating the command should be passed to executor
        self.assertIsInstance(result, tuple, "Result should be a tuple")
        self.assertEqual(len(result), 2, "Tuple should have two elements")
        self.assertEqual(result[0], False, "First element should be False")
        self.assertEqual(result[1], "export", "Second element should be 'export'")
    
    def test_execute_invalid_format(self):
        """Test invalid export format."""
        # Try an invalid format
        with CaptureOutput() as output:
            result = self.export_cmd.execute("export INVALID FORMAT")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that error message was displayed
        self.assertIn("Invalid format", output.stdout_content, 
                    "Output should indicate invalid format")

if __name__ == '__main__':
    # Run the test
    unittest.main()
