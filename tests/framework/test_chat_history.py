#!/usr/bin/env python
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

print("Starting test...")

# Show the current directory and sys.path
print(f"Current directory: {os.getcwd()}")
print(f"__file__: {__file__}")
print(f"Parent directory: {os.path.dirname(os.path.dirname(__file__))}")

# Fix import path - add the jibberish directory to the path
current_dir = os.path.dirname(__file__)  # framework directory
parent_dir = os.path.dirname(current_dir)  # tests directory
jibberish_dir = os.path.dirname(parent_dir)  # jibberish root directory
sys.path.insert(0, jibberish_dir)  # Add jibberish directory to path
print(f"Updated sys.path: {sys.path[0]}")

# Import the module to test
try:
    print("Importing chat module...")
    import chat
    print("Chat module imported successfully")
except Exception as e:
    print(f"Error importing chat module: {e}")
    raise

class ChatHistoryTest(unittest.TestCase):
    def setUp(self):
        # Save original values
        self.original_chat_history = chat.chat_history.copy() if chat.chat_history else []
        self.original_base_messages = chat.base_messages.copy() if hasattr(chat, 'base_messages') else []
        
        # Clear for tests
        chat.chat_history = []

    def tearDown(self):
        # Restore original values
        chat.chat_history = self.original_chat_history
        if hasattr(chat, 'base_messages'):
            chat.base_messages = self.original_base_messages

    def test_save_chat(self):
        """Test that question history ('?') is saved correctly"""
        # Create a test conversation
        test_conversation = [
            {"role": "user", "content": "Test question"},
            {"role": "assistant", "content": "Test answer"}
        ]
        
        # Save it
        chat.save_chat(test_conversation)
        
        # Verify it was added
        self.assertEqual(len(chat.chat_history), 1)
        self.assertEqual(chat.chat_history[0], test_conversation)
        print("Test save_chat passed!")

    def test_load_chat_history(self):
        """Test that question history ('?') is loaded correctly"""
        # Create test conversations
        test_conversation_1 = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"}
        ]
        test_conversation_2 = [
            {"role": "user", "content": "Question 2"},
            {"role": "assistant", "content": "Answer 2"}
        ]
        
        # Save them
        chat.save_chat(test_conversation_1)
        chat.save_chat(test_conversation_2)
        
        # Load history
        history = chat.load_chat_history()
        
        # Check result
        self.assertEqual(len(history), 2)  # Should have both messages from last conversation
        self.assertEqual(history[0]["content"], "Question 2")
        self.assertEqual(history[1]["content"], "Answer 2")
        print("Test load_chat_history passed!")
    
    def test_history_limit(self):
        """Test that history is limited to total_noof_questions"""
        # Save the original limit
        original_limit = chat.total_noof_questions
        
        try:
            # Set a small limit for testing
            chat.total_noof_questions = 3
            
            # Add more conversations than the limit
            for i in range(5):  # 0, 1, 2, 3, 4
                convo = [
                    {"role": "user", "content": f"Question {i}"},
                    {"role": "assistant", "content": f"Answer {i}"}
                ]
                chat.save_chat(convo)
            
            # Should only keep the last 3
            self.assertEqual(len(chat.chat_history), 3)
            
            # Check the actual conversations kept (should be 2, 3, 4)
            self.assertEqual(chat.chat_history[0][0]["content"], "Question 2")
            self.assertEqual(chat.chat_history[1][0]["content"], "Question 3")
            self.assertEqual(chat.chat_history[2][0]["content"], "Question 4")
            
            print("Test history_limit passed!")
        finally:
            # Restore the original limit
            chat.total_noof_questions = original_limit
    
    @patch('chat.api')
    def test_ai_command_history(self, mock_api):
        """Test that AI command history ('#') is stored in base_messages"""
        # Set up a clean base_messages for testing
        if not hasattr(chat, 'base_messages'):
            print("Chat module doesn't have base_messages attribute - skipping test")
            return
            
        original_base_messages = chat.base_messages
        chat.base_messages = []
        
        try:
            # Configure the mock API response
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "ls -la"
            mock_response.choices = [mock_choice]
            
            # Setup the API to return our mock response
            mock_api.model = "test-model"
            mock_api.client.chat.completions.create.return_value = mock_response
            
            # Call ask_ai to generate and store a command
            with patch('chat.hasattr', return_value=True):  # Force use of newer API
                result = chat.ask_ai("List all files")
            
            # Verify the result
            self.assertEqual(result, "ls -la")
            
            # Check that the command was added to base_messages
            self.assertEqual(len(chat.base_messages), 2)
            self.assertEqual(chat.base_messages[0]["role"], "user")
            self.assertEqual(chat.base_messages[0]["content"], "List all files")
            self.assertEqual(chat.base_messages[1]["role"], "assistant")
            self.assertEqual(chat.base_messages[1]["content"], "ls -la")
            
            print("Test ai_command_history passed!")
        finally:
            # Restore original base_messages
            chat.base_messages = original_base_messages

# Run the tests
if __name__ == "__main__":
    unittest.main()
