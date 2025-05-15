#!/usr/bin/env python
"""
Unittest-based test script for testing the alias plugin of Jibberish shell.
"""
import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the plugin to test
from app.plugins import alias_command
from tests.utils.test_utils import CaptureOutput, mock_click_echo
from tests import test_helper

class TestAliasCommands(unittest.TestCase):
    """Tests for the alias commands plugin."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Clear the aliases for testing
        alias_command.aliases.clear()
        
        # Create a temporary file for testing aliases persistence
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        
        # Set the aliases file path to our temporary file
        self.aliases_file_patcher = patch.object(alias_command, 'ALIASES_FILE', self.temp_file.name)
        self.mock_aliases_file = self.aliases_file_patcher.start()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Create instances of the plugins
        self.alias_cmd = alias_command.AliasCommand()
        self.unalias_cmd = alias_command.UnaliasCommand()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Stop the patchers
        self.aliases_file_patcher.stop()
        self.click_echo_patcher.stop()
        
        # Remove the temporary file
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
    
    def test_alias_can_handle(self):
        """Test the can_handle method of AliasCommand."""
        # Should handle 'alias' command
        self.assertTrue(self.alias_cmd.can_handle("alias ls='ls -la'"), 
                        "Should handle 'alias ls='ls -la''")
        self.assertTrue(self.alias_cmd.can_handle("alias"), 
                      "Should handle 'alias'")
        
        # Should not handle other commands
        self.assertFalse(self.alias_cmd.can_handle("ls"), 
                       "Should not handle 'ls'")
        
        # Set up an alias and test handling it
        alias_command.aliases["ll"] = "ls -la"
        self.assertTrue(self.alias_cmd.can_handle("ll"), 
                      "Should handle alias 'll'")
    
    def test_execute_set_alias(self):
        """Test setting an alias."""
        result = self.alias_cmd.execute("alias ls='ls -la'")
        self.assertTrue(result, f"Expected True but got {result}")
        self.assertIn("ls", alias_command.aliases, "Alias 'ls' should be set")
        self.assertEqual(alias_command.aliases["ls"], "ls -la", 
                       f"Expected 'ls -la' but got '{alias_command.aliases['ls']}'")
    
    def test_execute_list_aliases(self):
        """Test listing aliases."""
        # Set up some aliases
        alias_command.aliases["ls"] = "ls -la"
        alias_command.aliases["ll"] = "ls -l"
        
        with CaptureOutput() as output:
            result = self.alias_cmd.execute("alias")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that output contains the aliases
        self.assertIn("Current aliases", output.stdout_content, 
                    "Output should indicate listing aliases")
        self.assertIn("ls", output.stdout_content, 
                    "Output should contain 'ls' alias")
        self.assertIn("ll", output.stdout_content, 
                    "Output should contain 'll' alias")
    
    def test_execute_use_alias(self):
        """Test using an alias."""
        # Set up an alias
        alias_command.aliases["ll"] = "ls -l"
        
        # Execute the alias command
        result, cmd = self.alias_cmd.execute("ll")
        self.assertFalse(result, f"Expected False but got {result}")
        self.assertEqual(cmd, "ls -l", f"Expected 'ls -l' but got '{cmd}'")
    
    def test_save_load_aliases(self):
        """Test saving and loading aliases."""
        # Set some aliases
        alias_command.aliases["ls"] = "ls -la"
        alias_command.aliases["ll"] = "ls -l"
        
        # Save aliases
        alias_command.save_aliases()
        
        # Clear the aliases
        alias_command.aliases.clear()
        self.assertEqual(len(alias_command.aliases), 0, "Aliases should be empty")
        
        # Load aliases
        alias_command.load_aliases()
        
        # Check that aliases were loaded
        self.assertIn("ls", alias_command.aliases, "Alias 'ls' should be loaded")
        self.assertIn("ll", alias_command.aliases, "Alias 'll' should be loaded")
        self.assertEqual(alias_command.aliases["ls"], "ls -la", 
                       f"Expected 'ls -la' but got '{alias_command.aliases['ls']}'")
        self.assertEqual(alias_command.aliases["ll"], "ls -l", 
                       f"Expected 'ls -l' but got '{alias_command.aliases['ll']}'")
    
    def test_unalias_can_handle(self):
        """Test the can_handle method of UnaliasCommand."""
        # Should handle 'unalias' command
        self.assertTrue(self.unalias_cmd.can_handle("unalias ls"), 
                      "Should handle 'unalias ls'")
        self.assertTrue(self.unalias_cmd.can_handle("unalias"), 
                      "Should handle 'unalias'")
        
        # Should not handle other commands
        self.assertFalse(self.unalias_cmd.can_handle("ls"), 
                       "Should not handle 'ls'")
    
    def test_execute_remove_alias(self):
        """Test removing an alias."""
        # Set up some aliases
        alias_command.aliases["ls"] = "ls -la"
        alias_command.aliases["ll"] = "ls -l"
        
        result = self.unalias_cmd.execute("unalias ls")
        self.assertTrue(result, f"Expected True but got {result}")
        self.assertNotIn("ls", alias_command.aliases, "Alias 'ls' should be removed")
        self.assertIn("ll", alias_command.aliases, "Alias 'll' should still exist")
    
    def test_execute_remove_nonexistent_alias(self):
        """Test removing a nonexistent alias."""
        with CaptureOutput() as output:
            result = self.unalias_cmd.execute("unalias nonexistent")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that output contains the error message
        self.assertIn("not found", output.stdout_content, 
                    "Output should contain 'not found'")
    
    def test_alias_can_handle_with_pipe(self):
        """Test the can_handle method of AliasCommand with pipe."""
        # Should handle 'alias | grep ls' command
        self.assertTrue(self.alias_cmd.can_handle("alias | grep ls"), 
                      "Should handle 'alias | grep ls'")
        
        # Should not handle other piped commands
        self.assertFalse(self.alias_cmd.can_handle("ls | grep test"), 
                       "Should not handle 'ls | grep test'")
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    def test_execute_alias_with_pipe(self, mock_unlink, mock_tempfile, mock_subprocess_run):
        """Test executing alias command with pipe."""
        # Set up some aliases for testing
        alias_command.aliases["ls"] = "ls -la"
        alias_command.aliases["ll"] = "ls -l"
        alias_command.aliases["grep"] = "grep --color=auto"
        
        # Set up the mocks
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/test_alias_file"
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file
        
        # Execute the command with a pipe
        result = self.alias_cmd.execute("alias | grep ls")
        
        # Verify that the command was handled properly
        self.assertTrue(result, "Should return True to indicate command was handled")
        
        # Check that the temporary file was created and written to
        mock_temp_file.write.assert_called_once()
        write_content = mock_temp_file.write.call_args[0][0]
        self.assertIn("alias ls='ls -la'", write_content)
        self.assertIn("alias ll='ls -l'", write_content)
        
        # Check that subprocess.run was called with the correct command
        expected_command = f"cat {mock_temp_file.name} | grep ls"
        mock_subprocess_run.assert_called_once()
        self.assertEqual(mock_subprocess_run.call_args[0][0], expected_command)
        
        # Check that the temporary file was cleaned up
        mock_unlink.assert_called_once_with(mock_temp_file.name)
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    def test_execute_alias_with_pipe_no_aliases(self, mock_unlink, mock_tempfile, mock_subprocess_run):
        """Test executing alias command with pipe when no aliases are defined."""
        # Clear any existing aliases
        alias_command.aliases.clear()
        
        # Set up the mocks
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/test_alias_file"
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file
        
        # Execute the command with a pipe
        result = self.alias_cmd.execute("alias | grep anything")
        
        # Verify that the command was handled properly
        self.assertTrue(result, "Should return True to indicate command was handled")
        
        # Check that the temporary file was created with the correct content
        mock_temp_file.write.assert_called_once_with("No aliases defined")
        
        # Check that subprocess.run was called with the correct command
        expected_command = f"cat {mock_temp_file.name} | grep anything"
        mock_subprocess_run.assert_called_once()
        self.assertEqual(mock_subprocess_run.call_args[0][0], expected_command)
        
        # Check that the temporary file was cleaned up
        mock_unlink.assert_called_once_with(mock_temp_file.name)

if __name__ == '__main__':
    # Run the test
    unittest.main()
