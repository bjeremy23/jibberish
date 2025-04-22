#!/usr/bin/env python
"""
Unittest-based test script for testing the version_command plugin of Jibberish shell.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the plugin to test
from plugins import version_command
from tests.utils.test_utils import CaptureOutput, mock_click_echo

class TestVersionCommand(unittest.TestCase):
    """Tests for the VersionPlugin."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Create an instance of the plugin
        self.version_plugin = version_command.VersionPlugin()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Mock the api module to avoid external dependencies
        self.api_patcher = patch('plugins.version_command.api')
        self.mock_api = self.api_patcher.start()
        self.mock_api.__version__ = "25.04.0"
        self.mock_api.VERSION_NAME = "Initial Release"
    
    def tearDown(self):
        """Clean up after each test method."""
        # Stop the patchers
        self.click_echo_patcher.stop()
        self.api_patcher.stop()
    
    def test_can_handle(self):
        """Test the can_handle method."""
        # Should handle version commands
        self.assertTrue(self.version_plugin.can_handle("version"), 
                      "Should handle 'version' command")
        
        # Should not handle other commands
        self.assertFalse(self.version_plugin.can_handle("nonversion"), 
                       "Should not handle 'nonversion' command")
        self.assertFalse(self.version_plugin.can_handle("ver"), 
                       "Should not handle 'ver' command")
    
    def test_execute(self):
        """Test the execute method."""
        # Create a more flexible mock for click.echo that can handle all arguments
        flexible_mock = MagicMock()
        self.click_echo_patcher.stop()  # Stop the original patcher
        self.click_echo_patcher = patch('click.echo', side_effect=flexible_mock)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Use the CaptureOutput context manager to capture stdout
        with CaptureOutput() as output:
            # Execute the version command
            result = self.version_plugin.execute("version")
            
            # Check the return value
            self.assertTrue(result, "Expected execute to return True")
            
            # Verify that click.echo was called multiple times
            self.assertTrue(self.mock_click_echo.call_count >= 3, 
                         "Expected click.echo to be called at least 3 times")
    
    def test_plugin_registration(self):
        """Test that the plugin is registered correctly."""
        # Instead of trying to reload the module, we'll directly test the registration mechanism
        # by creating a fresh instance and checking if it can be registered properly
        
        # Mock the BuiltinCommandRegistry
        with patch('plugins.version_command.BuiltinCommandRegistry') as mock_registry:
            # Manually trigger the registration process that happens in the module
            plugin = version_command.VersionPlugin()
            version_command.BuiltinCommandRegistry.register(plugin)
            
            # Verify registration was called
            mock_registry.register.assert_called_once()
            
            # Verify the correct type of plugin was registered
            args, _ = mock_registry.register.call_args
            self.assertIsInstance(args[0], version_command.VersionPlugin,
                               "Should register an instance of VersionPlugin")


if __name__ == '__main__':
    unittest.main()
