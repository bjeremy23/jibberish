#!/usr/bin/env python
"""
Unittest-based test script for testing the question_command plugin of Jibberish shell.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the plugin to test
from app.plugins import question_command
from tests.utils.test_utils import CaptureOutput, mock_click_echo
from tests import test_helper

class TestQuestionCommand(unittest.TestCase):
    """Tests for the QuestionCommand plugin."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Create an instance of the plugin
        self.question_cmd = question_command.QuestionPlugin()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Mock the AI chat function to avoid making actual API calls
        # We need to patch app.chat.ask_question since that's what's used in question_command.py
        self.chat_patcher = patch('app.chat.ask_question', 
                                return_value="This is a mock AI response.")
        self.mock_chat = self.chat_patcher.start()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Stop the patchers
        self.click_echo_patcher.stop()
        self.chat_patcher.stop()
    
    def test_can_handle(self):
        """Test the can_handle method."""
        # Should handle '?' commands
        self.assertTrue(self.question_cmd.can_handle("?what is Linux"), 
                      "Should handle '?what is Linux'")
        self.assertTrue(self.question_cmd.can_handle("? how do I use bash"), 
                      "Should handle '? how do I use bash'")
        
        # Should not handle other commands
        self.assertFalse(self.question_cmd.can_handle("cd /tmp"), 
                       "Should not handle 'cd /tmp'")
        self.assertFalse(self.question_cmd.can_handle("what is Linux"), 
                       "Should not handle 'what is Linux'")
    
    def test_execute_question(self):
        """Test asking a question."""
        with CaptureOutput() as output:
            result = self.question_cmd.execute("?what is Linux")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that the chat function was called with the right question
        self.mock_chat.assert_called_once()
        call_args = self.mock_chat.call_args[0]
        self.assertTrue(len(call_args) > 0, "Expected at least one argument")
        self.assertIn("what is Linux", call_args[0], 
                    f"Expected question to contain 'what is Linux', got '{call_args[0]}'")
        
        # Check that the response was printed
        self.assertIn("This is a mock AI response", output.stdout_content, 
                    "Output should contain the AI response")
    
    def test_execute_question_with_space(self):
        """Test asking a question with a space after the question mark."""
        with CaptureOutput() as output:
            result = self.question_cmd.execute("? how do I use bash")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that the chat function was called with the right question
        self.mock_chat.assert_called_once()
        call_args = self.mock_chat.call_args[0]
        self.assertTrue(len(call_args) > 0, "Expected at least one argument")
        self.assertIn("how do I use bash", call_args[0], 
                    f"Expected question to contain 'how do I use bash', got '{call_args[0]}'")
    
    def test_execute_empty_question(self):
        """Test asking an empty question."""
        with CaptureOutput() as output:
            result = self.question_cmd.execute("?")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # The actual implementation doesn't check for empty questions,
        # so the chat function will be called with an empty string
        self.mock_chat.assert_called_once_with("")
        
        # Check that the mock response was printed
        self.assertIn("This is a mock AI response", output.stdout_content, 
                    "Output should contain the AI response")

if __name__ == '__main__':
    # Run the test
    unittest.main()
