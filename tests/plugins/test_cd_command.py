
#!/usr/bin/env python
"""
Unittest-based test script for testing the cd_command plugin of Jibberish shell.
"""
import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the plugin to test
from app.plugins import cd_command
from tests.utils.test_utils import CaptureOutput, mock_click_echo
from tests import test_helper

class TestCDCommand(unittest.TestCase):
    """Tests for the ChangeDirectoryCommand plugin."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Store the original directory
        self.original_dir = os.getcwd()
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a subdirectory for testing command substitution
        self.subdir_path = os.path.join(self.temp_dir, "test_subdir")
        os.makedirs(self.subdir_path, exist_ok=True)
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Create an instance of the plugin
        self.cd_cmd = cd_command.ChangeDirectoryCommand()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Change back to the original directory
        os.chdir(self.original_dir)
        
        # Remove the temporary directory
        try:
            os.rmdir(self.temp_dir)
        except:
            pass
        
        # Stop the patchers
        self.click_echo_patcher.stop()
    
    def test_can_handle(self):
        """Test the can_handle method."""
        # Should handle 'cd' command
        self.assertTrue(self.cd_cmd.can_handle("cd /tmp"), 
                      "Should handle 'cd /tmp'")
        self.assertTrue(self.cd_cmd.can_handle("cd"), 
                      "Should handle 'cd'")
        
        # Should not handle other commands
        self.assertFalse(self.cd_cmd.can_handle("ls"), 
                       "Should not handle 'ls'")
    
    def test_execute_change_directory(self):
        """Test changing to a valid directory."""
        # Change to the temporary directory
        with CaptureOutput() as output:
            result = self.cd_cmd.execute(f"cd {self.temp_dir}")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that we're in the temporary directory
        current_dir = os.getcwd()
        self.assertEqual(current_dir, self.temp_dir, 
                       f"Expected '{self.temp_dir}' but got '{current_dir}'")
    
    def test_execute_home_directory(self):
        """Test changing to the home directory."""
        # Change to the home directory
        with CaptureOutput() as output:
            result = self.cd_cmd.execute("cd ~")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that we're in the home directory
        home_dir = os.path.expanduser("~")
        current_dir = os.getcwd()
        self.assertEqual(current_dir, home_dir, 
                       f"Expected '{home_dir}' but got '{current_dir}'")
    
    def test_execute_invalid_directory(self):
        """Test changing to an invalid directory."""
        # Try to change to a non-existent directory
        with CaptureOutput() as output:
            result = self.cd_cmd.execute("cd /nonexistent/directory")
            self.assertTrue(result, f"Expected True but got {result}")
        
        # Check that an error message was printed
        self.assertIn("Error: No such directory", output.stdout_content, 
                    "Output should contain error message")
        
        # Check that we're still in the same directory
        current_dir = os.getcwd()
        self.assertNotEqual(current_dir, "/nonexistent/directory", 
                         "Should not have changed to the invalid directory")
    
    def test_execute_file_as_directory(self):
        """Test changing to a file (which should fail)."""
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        
        try:
            # Try to change to the file
            with CaptureOutput() as output:
                result = self.cd_cmd.execute(f"cd {temp_file.name}")
                self.assertTrue(result, f"Expected True but got {result}")
            
            # Check that an error message was printed
            self.assertIn("is a file, not a directory", output.stdout_content, 
                        "Output should contain error message")
            
            # Check that we're still in the same directory
            current_dir = os.getcwd()
            self.assertNotEqual(current_dir, temp_file.name, 
                             "Should not have changed to the file")
        finally:
            # Clean up
            os.unlink(temp_file.name)
    
    def test_execute_cd_cmd_substitution(self):
        """Test cd with command substitution."""
        # We'll mock subprocess.run to simulate command substitution
        mock_process = MagicMock()
        mock_process.stdout = self.subdir_path
        
        with patch('subprocess.run', return_value=mock_process) as mock_run:
            with patch('click.echo') as mock_echo:
                result = self.cd_cmd.execute('cd "$(find . -type d -name test_subdir)"')
            
            # Verify subprocess.run was called with the correct arguments
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertIn('echo', call_args)
            self.assertIn('$(find . -type d -name test_subdir)', call_args)
            self.assertTrue(result, "CD command should return True")
            
            # Verify the "Resolved path:" message was echoed
            resolved_path_called = any("Resolved path:" in str(call[0][0]) 
                                     for call in mock_echo.call_args_list if call[0])
            self.assertTrue(resolved_path_called, "Should output 'Resolved path:' message")


if __name__ == '__main__':
    # Run the test
    unittest.main()
