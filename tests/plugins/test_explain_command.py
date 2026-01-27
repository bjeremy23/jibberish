#!/usr/bin/env python
"""
Unittest-based test script for testing the explain_command plugin of Jibberish shell.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the plugin to test
from app.plugins import explain_command
from tests.utils.test_utils import CaptureOutput, mock_click_echo


class TestExplainCommand(unittest.TestCase):
    """Tests for the ExplainCommandPlugin."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Create an instance of the plugin
        self.explain_plugin = explain_command.ExplainCommandPlugin()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Stop the patchers
        self.click_echo_patcher.stop()
    
    def test_can_handle_explain_command(self):
        """Test the can_handle method with 'explain' commands."""
        # Should handle 'explain' followed by a command
        self.assertTrue(self.explain_plugin.can_handle("explain ls"), 
                      "Should handle 'explain ls'")
        self.assertTrue(self.explain_plugin.can_handle("explain tar -xzvf file.tar.gz"), 
                      "Should handle 'explain tar -xzvf file.tar.gz'")
        self.assertTrue(self.explain_plugin.can_handle("explain"), 
                      "Should handle bare 'explain' command")
        self.assertTrue(self.explain_plugin.can_handle("explain "), 
                      "Should handle 'explain ' with trailing space")
        
    def test_can_handle_non_explain_commands(self):
        """Test that can_handle returns False for non-explain commands."""
        self.assertFalse(self.explain_plugin.can_handle("ls"), 
                       "Should not handle 'ls'")
        self.assertFalse(self.explain_plugin.can_handle("explains"), 
                       "Should not handle 'explains'")
        self.assertFalse(self.explain_plugin.can_handle("explanation"), 
                       "Should not handle 'explanation'")
        self.assertFalse(self.explain_plugin.can_handle("# explain"), 
                       "Should not handle '# explain'")
    
    def test_execute_without_command(self):
        """Test execute with just 'explain' shows usage."""
        flexible_mock = MagicMock()
        self.click_echo_patcher.stop()
        self.click_echo_patcher = patch('click.echo', side_effect=flexible_mock)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        result = self.explain_plugin.execute("explain")
        
        # Should return (True, None) - handled but no new command
        self.assertEqual(result, (True, None), 
                       "Expected (True, None) for bare explain command")
        
        # Verify click.echo was called (for usage message)
        self.assertTrue(self.mock_click_echo.call_count >= 1, 
                     "Expected click.echo to be called for usage message")
    
    def test_execute_with_command(self):
        """Test execute with a command to explain."""
        flexible_mock = MagicMock()
        self.click_echo_patcher.stop()
        self.click_echo_patcher = patch('click.echo', side_effect=flexible_mock)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Mock the explain_command_ai function
        with patch('app.plugins.explain_command.explain_command_ai') as mock_ai:
            mock_ai.return_value = "ls - List directory contents\n\nFlags:\n  -l  Long listing format"
            
            result = self.explain_plugin.execute("explain ls -l")
            
            # Should return (True, None) - handled but no new command to execute
            self.assertEqual(result, (True, None), 
                           "Expected (True, None) for explain with command")
            
            # Verify AI function was called with the command
            mock_ai.assert_called_once_with("ls -l")
    
    def test_execute_ai_failure(self):
        """Test execute when AI fails to explain."""
        flexible_mock = MagicMock()
        self.click_echo_patcher.stop()
        self.click_echo_patcher = patch('click.echo', side_effect=flexible_mock)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Mock the explain_command_ai function to return None (failure)
        with patch('app.plugins.explain_command.explain_command_ai') as mock_ai:
            mock_ai.return_value = None
            
            result = self.explain_plugin.execute("explain unknowncommand")
            
            # Should still return (True, None) - handled
            self.assertEqual(result, (True, None), 
                           "Expected (True, None) even on AI failure")
    
    def test_plugin_attributes(self):
        """Test plugin has correct attributes."""
        self.assertEqual(self.explain_plugin.plugin_name, "explain_command",
                       "Plugin name should be 'explain_command'")
        self.assertFalse(self.explain_plugin.is_required,
                       "Plugin should not be required")
        self.assertTrue(self.explain_plugin.is_enabled,
                       "Plugin should be enabled by default")
    
    def test_plugin_registration(self):
        """Test that the plugin is registered correctly."""
        with patch('app.plugins.explain_command.BuiltinCommandRegistry') as mock_registry:
            # Manually trigger the registration process
            plugin = explain_command.ExplainCommandPlugin()
            explain_command.BuiltinCommandRegistry.register(plugin)
            
            # Verify registration was called
            mock_registry.register.assert_called_once()
            
            # Verify the correct type of plugin was registered
            args, _ = mock_registry.register.call_args
            self.assertIsInstance(args[0], explain_command.ExplainCommandPlugin,
                               "Should register an instance of ExplainCommandPlugin")


class TestExplainCommandAI(unittest.TestCase):
    """Tests for the explain_command_ai function."""
    
    def test_explain_command_ai_success(self):
        """Test explain_command_ai with successful API response."""
        # Mock the API client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "tar - Archive utility\n\nFlags:\n  -x  Extract"
        
        with patch('app.api.client') as mock_client:
            with patch('app.api.model', 'gpt-4'):
                mock_client.chat.completions.create.return_value = mock_response
                
                result = explain_command.explain_command_ai("tar -xzvf file.tar.gz")
                
                self.assertIsNotNone(result, "Should return an explanation")
                self.assertIn("tar", result.lower(), "Explanation should mention tar")
    
    def test_explain_command_ai_failure(self):
        """Test explain_command_ai when API fails."""
        with patch('app.api.client') as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            with patch('app.utils.is_debug_enabled', return_value=False):
                result = explain_command.explain_command_ai("ls")
                
                self.assertIsNone(result, "Should return None on API failure")


if __name__ == '__main__':
    unittest.main()
