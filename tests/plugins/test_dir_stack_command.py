#!/usr/bin/env python
"""
Unittest-based test script for testing the dir_stack_command plugin of Jibberish shell.
"""
import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the plugin to test
from plugins import dir_stack_command
from tests.utils.test_utils import CaptureOutput, mock_click_echo

class TestDirStackCommand(unittest.TestCase):
    """Tests for the DirStackCommand plugins."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Store the original directory
        self.original_dir = os.getcwd()
        
        # Create temporary directories for testing
        self.temp_dir1 = tempfile.mkdtemp()
        self.temp_dir2 = tempfile.mkdtemp()
        self.temp_dir3 = tempfile.mkdtemp()
        
        # Create subdirectories for testing command substitution
        self.subdir1_path = os.path.join(self.temp_dir1, "test_subdir1")
        os.makedirs(self.subdir1_path, exist_ok=True)
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Reset the directory stack if it exists as a module variable
        if hasattr(dir_stack_command, 'dir_stack'):
            dir_stack_command.dir_stack = []
        
        # Create an instance of the plugin
        self.dir_stack_cmd = dir_stack_command.DirStackCommand()
        
        # For compatibility with existing tests, create aliases to the same object
        self.pushd_cmd = self.dir_stack_cmd
        self.popd_cmd = self.dir_stack_cmd
        self.dirs_cmd = self.dir_stack_cmd
    
    def tearDown(self):
        """Clean up after each test method."""
        # Change back to the original directory
        os.chdir(self.original_dir)
        
        # Remove the temporary directories
        try:
            os.rmdir(self.temp_dir1)
            os.rmdir(self.temp_dir2)
            os.rmdir(self.temp_dir3)
        except:
            pass
        
        # Stop the patchers
        self.click_echo_patcher.stop()
    
    def test_can_handle(self):
        """Test the can_handle method for all commands."""
        # Should handle respective commands
        self.assertTrue(self.pushd_cmd.can_handle("pushd /tmp"), 
                      "Should handle 'pushd /tmp'")
        self.assertTrue(self.popd_cmd.can_handle("popd"), 
                      "Should handle 'popd'")
        self.assertTrue(self.dirs_cmd.can_handle("dirs"), 
                      "Should handle 'dirs'")
        
        # Should not handle other commands
        self.assertFalse(self.pushd_cmd.can_handle("ls"), 
                       "Should not handle 'ls'")
        self.assertFalse(self.popd_cmd.can_handle("cd /tmp"), 
                       "Should not handle 'cd /tmp'")
        self.assertFalse(self.dirs_cmd.can_handle("pwd"), 
                       "Should not handle 'pwd'")
    
    def test_pushd_with_directory(self):
        """Test pushing a directory onto the stack."""
        # Change to a known directory
        os.chdir(self.temp_dir1)
        
        # Push directory onto stack
        with CaptureOutput() as output:
            result = self.pushd_cmd.execute(f"pushd {self.temp_dir2}")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that we're in the new directory
        current_dir = os.getcwd()
        self.assertEqual(current_dir, self.temp_dir2, 
                       f"Expected '{self.temp_dir2}' but got '{current_dir}'")
        
        # Check that the stack has the original directory
        self.assertEqual(len(dir_stack_command.dir_stack), 1, 
                       f"Expected 1 item in stack but got {len(dir_stack_command.dir_stack)}")
        self.assertEqual(dir_stack_command.dir_stack[0], self.temp_dir1, 
                       f"Expected '{self.temp_dir1}' but got '{dir_stack_command.dir_stack[0]}'")
                       
    def test_pushd_with_command_chaining(self):
        """Test pushing a directory onto the stack with command chaining."""
        # Change to a known directory
        os.chdir(self.temp_dir1)
        
        # Test with a simple command chain
        result = self.pushd_cmd.execute(f"pushd {self.temp_dir2} && ls")
        
        # The result should be a tuple indicating command not fully handled
        self.assertIsInstance(result, tuple, f"Expected tuple but got {type(result)}")
        self.assertEqual(len(result), 2, f"Expected tuple of length 2 but got {len(result)}")
        self.assertFalse(result[0], f"Expected False for first element but got {result[0]}")
        self.assertEqual(result[1], "ls", f"Expected 'ls' for second element but got '{result[1]}'")
        
        # Check that we're in the new directory (pushd part executed)
        current_dir = os.getcwd()
        self.assertEqual(current_dir, self.temp_dir2, 
                       f"Expected '{self.temp_dir2}' but got '{current_dir}'")
        
        # Check that the stack has the original directory
        self.assertEqual(len(dir_stack_command.dir_stack), 1, 
                       f"Expected 1 item in stack but got {len(dir_stack_command.dir_stack)}")
        self.assertEqual(dir_stack_command.dir_stack[0], self.temp_dir1, 
                       f"Expected '{self.temp_dir1}' but got '{dir_stack_command.dir_stack[0]}'")
                       
    def test_pushd_with_command_chaining_and_alias(self):
        """Test pushd with command chaining and alias expansion."""
        # Change to a known directory
        os.chdir(self.temp_dir1)
        
        # Directly modify the aliases dict for this test
        # Save the original aliases to restore later
        original_aliases = dir_stack_command.aliases.copy()
        # Set up our test alias
        dir_stack_command.aliases["ls"] = "ls -la"
        
        try:
            # Test with a chain that includes an aliased command
            result = self.pushd_cmd.execute(f"pushd {self.temp_dir2} && ls")
            
            # The result should contain the expanded alias
            self.assertIsInstance(result, tuple, f"Expected tuple but got {type(result)}")
            self.assertEqual(len(result), 2, f"Expected tuple of length 2 but got {len(result)}")
            self.assertFalse(result[0], f"Expected False for first element but got {result[0]}")
            self.assertEqual(result[1], "ls -la", f"Expected 'ls -la' for second element but got '{result[1]}'")
            
            # Check that pushd was executed correctly
            current_dir = os.getcwd()
            self.assertEqual(current_dir, self.temp_dir2, 
                           f"Expected '{self.temp_dir2}' but got '{current_dir}'")
            
            # Test with a more complex chain and arguments
            os.chdir(self.temp_dir1)  # Reset directory
            dir_stack_command.dir_stack = []  # Reset stack
            
            result = self.pushd_cmd.execute(f"pushd {self.temp_dir3} && ls -h something.txt")
            
            # Check that alias expansion preserves arguments
            self.assertEqual(result[1], "ls -la -h something.txt", 
                           f"Expected 'ls -la -h something.txt' but got '{result[1]}'")
                           
        finally:
            # Restore original aliases
            dir_stack_command.aliases.clear()
            dir_stack_command.aliases.update(original_aliases)
    
    def test_pushd_invalid_directory(self):
        """Test pushing an invalid directory."""
        # Change to a known directory
        os.chdir(self.temp_dir1)
        
        # Try to push invalid directory
        with CaptureOutput() as output:
            result = self.pushd_cmd.execute("pushd /nonexistent/directory")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that we're still in the original directory
        current_dir = os.getcwd()
        self.assertEqual(current_dir, self.temp_dir1, 
                       f"Expected '{self.temp_dir1}' but got '{current_dir}'")
        
        # Check that the stack is unchanged
        self.assertEqual(len(dir_stack_command.dir_stack), 0, 
                       f"Expected empty stack but got {len(dir_stack_command.dir_stack)}")
    
    def test_popd(self):
        """Test popping a directory from the stack."""
        # Set up the stack
        os.chdir(self.temp_dir1)
        dir_stack_command.dir_stack = [self.temp_dir2, self.temp_dir3]
        
        # Pop directory from stack
        with CaptureOutput() as output:
            result = self.popd_cmd.execute("popd")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that we're in the popped directory
        current_dir = os.getcwd()
        self.assertEqual(current_dir, self.temp_dir2, 
                       f"Expected '{self.temp_dir2}' but got '{current_dir}'")
        
        # Check that the stack has the remaining directory
        self.assertEqual(len(dir_stack_command.dir_stack), 1, 
                       f"Expected 1 item in stack but got {len(dir_stack_command.dir_stack)}")
        self.assertEqual(dir_stack_command.dir_stack[0], self.temp_dir3, 
                       f"Expected '{self.temp_dir3}' but got '{dir_stack_command.dir_stack[0]}'")
    
    def test_popd_empty_stack(self):
        """Test popping from an empty stack."""
        # Ensure the stack is empty
        dir_stack_command.dir_stack = []
        
        # Try to pop from empty stack
        with CaptureOutput() as output:
            result = self.popd_cmd.execute("popd")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that an error message was displayed
        self.assertIn("empty", output.stdout_content.lower(), 
                    "Output should indicate empty stack")
    
    def test_dirs(self):
        """Test displaying the directory stack."""
        # Set up the stack
        dir_stack_command.dir_stack = [self.temp_dir1, self.temp_dir2]
        
        # Display the stack
        with CaptureOutput() as output:
            result = self.dirs_cmd.execute("dirs")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that the output contains the directories
        self.assertIn(self.temp_dir1, output.stdout_content, 
                    f"Output should contain '{self.temp_dir1}'")
        self.assertIn(self.temp_dir2, output.stdout_content, 
                    f"Output should contain '{self.temp_dir2}'")
    
    def test_dirs_empty_stack(self):
        """Test displaying an empty directory stack."""
        # Ensure the stack is empty
        dir_stack_command.dir_stack = []
        
        # Display the stack
        with CaptureOutput() as output:
            result = self.dirs_cmd.execute("dirs")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that an appropriate message was displayed
        self.assertIn("empty", output.stdout_content.lower(), 
                    "Output should indicate empty stack")

    def test_execute_pushd_cmd_substitution(self):
        """Test pushd with command substitution."""
        # We'll mock subprocess.run to simulate command substitution
        mock_process = MagicMock()
        mock_process.stdout = self.subdir1_path
        
        with patch('subprocess.run', return_value=mock_process) as mock_run:
            with patch('click.echo') as mock_echo:
                result = self.dir_stack_cmd.execute('pushd "$(find . -type d -name test_subdir1)"')
            
            # Verify subprocess.run was called with the correct arguments
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertIn('echo', call_args)
            self.assertIn('$(find . -type d -name test_subdir1)', call_args)
            self.assertTrue(result, "pushd command should return True")
            
            # Verify the "Resolved path:" message was echoed
            resolved_path_called = any("Resolved path:" in str(call[0][0]) 
                                     for call in mock_echo.call_args_list if call[0])
            self.assertTrue(resolved_path_called, "Should output 'Resolved path:' message")

if __name__ == '__main__':
    # Run the test
    unittest.main()
    