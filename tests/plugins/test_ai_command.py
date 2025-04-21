#!/usr/bin/env python
"""
Unittest-based test script for testing the ai_command plugin of Jibberish shell.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the plugin to test
from plugins import ai_command
from tests.utils.test_utils import CaptureOutput, mock_click_echo

class TestAICommand(unittest.TestCase):
    """Tests for the AICommand plugin."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Create an instance of the plugin
        self.ai_cmd = ai_command.AICommandPlugin()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Mock the AI functions to avoid making actual API calls
        self.chat_ask_ai_patcher = patch('plugins.ai_command.chat.ask_ai', 
                                       return_value="ls -la")
        self.mock_ask_ai = self.chat_ask_ai_patcher.start()
        
        # Mock input function
        self.input_patcher = patch('builtins.input', return_value="y")
        self.mock_input = self.input_patcher.start()
        
        # Mock execute_command function
        self.execute_command_patcher = patch('executor.execute_command')
        self.mock_execute_command = self.execute_command_patcher.start()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Stop all the patchers
        self.click_echo_patcher.stop()
        self.chat_ask_ai_patcher.stop()
        self.input_patcher.stop()
        self.execute_command_patcher.stop()
    
    def test_can_handle(self):
        """Test the can_handle method."""
        # Should handle '#' commands
        self.assertTrue(self.ai_cmd.can_handle("#find large files"), 
                      "Should handle '#find large files'")
        self.assertTrue(self.ai_cmd.can_handle("#test show all running processes"), 
                      "Should handle '#test show all running processes'")
        
        # Should not handle other commands
        self.assertFalse(self.ai_cmd.can_handle("ls"), 
                       "Should not handle 'ls'")
        self.assertFalse(self.ai_cmd.can_handle("?what is bash"), 
                       "Should not handle '?what is bash'")
    
    def test_execute_ai_command(self):
        """Test executing an AI command."""
        with CaptureOutput() as output:
            result = self.ai_cmd.execute("#find large files")
            
            # The execute method should return (False, command) to indicate
            # the shell should execute the command
            self.assertIsInstance(result, tuple, "Expected result to be a tuple")
            self.assertEqual(len(result), 2, "Expected tuple with 2 elements")
            self.assertFalse(result[0], "First element should be False")
            self.assertEqual(result[1], "ls -la", "Second element should be the command to execute")
        
        # Check that the API was called with the right query
        self.mock_ask_ai.assert_called_once()
        call_args = self.mock_ask_ai.call_args[0]
        self.assertGreater(len(call_args), 0, "Expected at least one argument")
        self.assertIn("find large files", call_args[0], 
                    f"Expected query to contain 'find large files', got '{call_args[0]}'")
        
        # Note: The plugin itself doesn't call execute_command directly,
        # it returns a tuple that signals that the command should be executed
    
    def test_execute_ai_command_with_prompt(self):
        """Test executing an AI command with prompt."""
        # Set up environment for prompting
        with patch.dict(os.environ, {"PROMPT_AI_COMMANDS": "true"}):
            with CaptureOutput() as output:
                result = self.ai_cmd.execute("#find large files")
                
                # The prompt is confirmed (mock_input returns "y"), so it should
                # return (False, command) to signal the shell to execute the command
                self.assertIsInstance(result, tuple, "Expected result to be a tuple")
                self.assertEqual(len(result), 2, "Expected tuple with 2 elements")
                self.assertFalse(result[0], "First element should be False")
                self.assertEqual(result[1], "ls -la", "Second element should be the command to execute")
            
            # Check that input was called to prompt the user
            self.mock_input.assert_called_once()
    
    def test_execute_ai_command_with_rejection(self):
        """Test rejecting an AI command."""
        # Mock input to return "n" (rejection)
        self.input_patcher.stop()
        self.input_patcher = patch('builtins.input', return_value="n")
        self.mock_input = self.input_patcher.start()
        
        # Set up environment for prompting
        with patch.dict(os.environ, {"PROMPT_AI_COMMANDS": "true"}):
            with CaptureOutput() as output:
                result = self.ai_cmd.execute("#find large files")
                
                # When rejected, the plugin should return True to indicate that it has handled
                # the command and no further action is needed by the shell
                self.assertTrue(result, "Expected True when command is rejected")
            
            # Check that input was called to prompt the user
            self.mock_input.assert_called_once()
            
            # No need to check if execute_command was called, as the plugin doesn't call it directly
    
    def test_execute_double_hash_ai_command(self):
        """Test executing a double hash AI command (## prefix)."""
        # Set up the AI response for this test
        self.mock_ask_ai.return_value = "ls -la"
        
        with CaptureOutput() as output:
            result = self.ai_cmd.execute("## find large files")
            
            # With double hash, the result should be True (handled) and not passed for execution
            self.assertTrue(result, "Expected True for double hash command (should be handled)")
            
            # Capture and check the output - flush and read the output file
            output.stdout.flush()
            output.stdout.seek(0)
            stdout_content = output.stdout.read()
            self.assertIn("# ls -la", stdout_content, 
                        "Expected output to contain '# ls -la'")
        
        # Check that the API was called with the right query (without ## prefix)
        self.mock_ask_ai.assert_called_once()
        call_args = self.mock_ask_ai.call_args[0]
        self.assertGreater(len(call_args), 0, "Expected at least one argument")
        self.assertEqual(" find large files", call_args[0], 
                       "Expected query to be ' find large files' with leading space after removing # characters")

if __name__ == '__main__':
    # Run the test
    unittest.main()
