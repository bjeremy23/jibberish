#!/usr/bin/env python
"""
Unittest-based test script for testing the history module of Jibberish shell.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the module to test
from tests import test_helper
from app import history
from tests.utils.test_utils import create_mock_environment, cleanup_mock_environment

class TestHistory(unittest.TestCase):
    """Tests for the history module."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Create a mock environment
        self.env = create_mock_environment()
        
        # Mock readline related functions
        self.readline_patcher = patch.multiple(
            history.readline,
            get_current_history_length=MagicMock(return_value=3),
            get_history_item=MagicMock(side_effect=lambda i: [None, "ls -la", "cd /tmp", "echo test"][i]),
            parse_and_bind=MagicMock(),
            set_completer=MagicMock(),
            set_completer_delims=MagicMock()
        )
        self.mock_readline = self.readline_patcher.start()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Stop the patchers and clean up
        self.readline_patcher.stop()
        cleanup_mock_environment(self.env)
    
    def test_list_history(self):
        """Test the list_history function."""
        with patch('builtins.print') as mock_print:
            history.list_history()
            # Check that print was called for each history item
            self.assertGreaterEqual(mock_print.call_count, 3, 
                                  f"Expected at least 3 calls but got {mock_print.call_count}")
    
    def test_get_history_item(self):
        """Test the get_history_item function."""
        item = history.get_history_item(1)
        self.assertEqual(item, "ls -la", f"Expected 'ls -la' but got '{item}'")
        
        item = history.get_history_item(2)
        self.assertEqual(item, "cd /tmp", f"Expected 'cd /tmp' but got '{item}'")
        
        item = history.get_history_item(3)
        self.assertEqual(item, "echo test", f"Expected 'echo test' but got '{item}'")
    
    def test_get_history_by_number(self):
        """Test the get_history function with a numeric index."""
        with patch('click.echo'):
            cmd = history.get_history("!2")
            self.assertEqual(cmd, "cd /tmp", f"Expected 'cd /tmp' but got '{cmd}'")
    
    def test_get_history_invalid_index(self):
        """Test the get_history function with an invalid index."""
        with patch('click.echo'):
            cmd = history.get_history("!99")
            self.assertIsNone(cmd, f"Expected None but got '{cmd}'")
    
    def test_get_history_invalid_format(self):
        """Test the get_history function with an invalid format."""
        with patch('click.echo'):
            cmd = history.get_history("!abc")
            self.assertIsNone(cmd, f"Expected None but got '{cmd}'")

class TestTabCompletion(unittest.TestCase):
    """Tests for the TAB completion functionality."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Create a mock environment
        self.env = create_mock_environment()
        self.test_dir = self.env['test_dir']
        
        # Create some test files and directories for path completion tests
        self.test_file = os.path.join(self.test_dir, 'test_file.txt')
        with open(self.test_file, 'w') as f:
            f.write("test content")
            
        self.test_subdir = os.path.join(self.test_dir, 'test_subdir')
        os.mkdir(self.test_subdir)
        
        # Mock readline functions
        self.readline_patcher = patch.multiple(
            history.readline,
            get_line_buffer=MagicMock(return_value="cd "),
            get_endidx=MagicMock(return_value=3),
            set_completion_display_matches_hook=MagicMock()
        )
        self.mock_readline = self.readline_patcher.start()
        
        # Mock os.environ for PATH testing
        self.mock_path = os.path.join(self.test_dir, 'bin')
        os.mkdir(self.mock_path)
        
        # Create mock executable files
        self.mock_cmd1 = os.path.join(self.mock_path, 'testcmd1')
        with open(self.mock_cmd1, 'w') as f:
            f.write("#!/bin/bash\necho test")
        os.chmod(self.mock_cmd1, 0o755)
        
        self.mock_cmd2 = os.path.join(self.mock_path, 'testcmd2')
        with open(self.mock_cmd2, 'w') as f:
            f.write("#!/bin/bash\necho test")
        os.chmod(self.mock_cmd2, 0o755)
        
        # Store original PATH and set mock PATH
        self.original_path = os.environ.get('PATH', '')
        os.environ['PATH'] = self.mock_path
        
    def tearDown(self):
        """Clean up after each test method."""
        # Restore original PATH
        os.environ['PATH'] = self.original_path
        
        # Stop the patchers and clean up
        self.readline_patcher.stop()
        cleanup_mock_environment(self.env)
    
    def test_custom_completer_path_completion(self):
        """Test path completion in custom_completer."""
        # We'll use a simpler approach - directly create and test path matching
        test_prefix = "test"
        
        # Set up our expected matches - mimic what glob.glob would return
        test_matches = [self.test_file, self.test_subdir]
        
        # Define which of our matches are directories
        is_dir_results = {self.test_file: False, self.test_subdir: True}
        
        # Mock functions to ensure consistent behavior
        def mock_isdir(path):
            return is_dir_results.get(path, False)
            
        def mock_glob(pattern):
            if pattern.startswith(test_prefix):
                return test_matches
            return []
            
        # Set up patches - critically set buffer to "ls " to ensure we're NOT in cd context
        with patch.object(history.readline, 'get_line_buffer', return_value="ls "):
            with patch.object(history.readline, 'get_endidx', return_value=3):
                with patch('glob.glob', side_effect=mock_glob):
                    with patch('os.path.isdir', side_effect=mock_isdir):
                        with patch('os.path.expanduser', return_value=test_prefix):
                            # Ensure module-level state is reset
                            history._completion_matches = []
                            
                            # Get completions for our test prefix
                            completions = []
                            state = 0
                            while True:
                                completion = history.custom_completer(test_prefix, state)
                                if completion is None:
                                    break
                                completions.append(completion)
                                state += 1
                            
                            # Verify results - file should be returned as is, directory with trailing slash
                            self.assertIn(self.test_file, completions, 
                                        f"Expected '{self.test_file}' in completions but not found")
                            expected_dir = self.test_subdir + '/'  # Directory should have trailing slash
                            self.assertIn(expected_dir, completions, 
                                        f"Expected '{expected_dir}' in completions but not found")
    
    def test_custom_completer_command_completion(self):
        """Test command completion in custom_completer."""
        # For command completion testing, we need to make sure it doesn't find any path matches
        # so it will proceed to check commands in PATH
        dummy_text = "xcmdtest"  # A prefix unlikely to match any existing files/dirs
        
        # Create a set of mock commands that can be found in the PATH
        mock_commands = [f"{dummy_text}1", f"{dummy_text}2"]
        
        # Define a custom side effect for os.path.isdir
        # Make PATH directories return True, but command files return False
        def mock_isdir(path):
            if path == self.mock_path:  # This is a PATH directory
                return True
            if path.endswith(tuple(mock_commands)):  # These are command files
                return False
            return False  # Default case
        
        # Define a custom side effect for os.listdir
        def mock_listdir(path):
            if path == self.mock_path:  # Only return commands for our mock PATH
                return mock_commands
            return []  # Empty for other directories
        
        # We need to patch several functions to ensure command completion works correctly
        with patch('glob.glob', return_value=[]):  # Ensure no path matches are found
            with patch('os.environ.get', return_value=self.mock_path):  # Mock PATH
                with patch('os.path.isdir', side_effect=mock_isdir):  # Custom directory check
                    with patch('os.listdir', side_effect=mock_listdir):  # Custom directory listing
                        with patch('os.access', return_value=True):  # Make all files executable
                            with patch('os.path.join', side_effect=os.path.join):  # Use real path joining
                                # Set up readline mock to simulate command completion context
                                with patch.object(history.readline, 'get_line_buffer', return_value=dummy_text):
                                    with patch.object(history.readline, 'get_endidx', return_value=len(dummy_text)):
                                        # Reset module-level _completion_matches
                                        history._completion_matches = []
                                        
                                        # Test command completion with state 0 (first call)
                                        completions = []
                                        state = 0
                                        while True:
                                            completion = history.custom_completer(dummy_text, state)
                                            if completion is None:
                                                break
                                            completions.append(completion)
                                            state += 1
                        
                                        # Check that our test commands are in the completions
                                        self.assertIn(f"{dummy_text}1", completions, 
                                                   f"Expected '{dummy_text}1' in completions but not found")
                                        self.assertIn(f"{dummy_text}2", completions, 
                                                   f"Expected '{dummy_text}2' in completions but not found")
    
    def test_custom_completer_cd_command(self):
        """Test that custom_completer only shows directories with cd command."""
        # Create a test text file inside the test_subdir to verify it doesn't show
        nested_file = os.path.join(self.test_subdir, 'nested_file.txt')
        with open(nested_file, 'w') as f:
            f.write("test content")
        
        # Set up completions for "cd " followed by the test directory path
        cd_command_text = "cd " + self.test_dir + "/"
        test_text = self.test_dir + "/"  # Text to complete
        
        with patch.object(history.readline, 'get_line_buffer', return_value=cd_command_text):
            with patch.object(history.readline, 'get_endidx', return_value=len(cd_command_text)):
                # Test cd command completion with state 0 (first call)
                completions = []
                state = 0
                while True:
                    completion = history.custom_completer(test_text, state)
                    if completion is None:
                        break
                    completions.append(completion)
                    state += 1
                
                # For cd command, directories should be included with trailing slash
                expected_dir_path = self.test_subdir + '/'
                self.assertIn(expected_dir_path, completions, 
                            f"Expected directory '{expected_dir_path}' in completions but not found")
                
                # Verify files are not included with cd command
                self.assertTrue(all(os.path.isdir(path.rstrip('/')) for path in completions),
                             "Only directories should be included in cd command completions")
    
    def test_display_completions_hook(self):
        """Test the display completions hook function."""
        # Create some test matches
        matches = [self.test_file, self.test_subdir + '/']
        
        with patch('builtins.print') as mock_print:
            with patch('os.get_terminal_size', return_value=MagicMock(columns=80)):
                # Call the display completions hook
                result = history._display_completions_hook('test', matches, 10)
                
                # Check that the function returned True
                self.assertTrue(result, f"Expected True but got {result}")
                
                # Check that print was called for displaying the matches
                self.assertGreater(mock_print.call_count, 0, f"Print should be called but wasn't")
    
    def test_word_break_hook(self):
        """Test the word break hook function."""
        breaks = history.word_break_hook()
        self.assertEqual(breaks, ' \t\n`!@#$%^&*()=+[{]}\\|;:\'",<>?',
                       f"Expected default delimiters but got '{breaks}'")
    
    def test_tilde_expansion(self):
        """Test that the custom completer handles tilde expansion."""
        with patch('os.path.expanduser', return_value=self.test_dir) as mock_expanduser:
            # Call the completer with a path starting with tilde
            history.custom_completer("~/", 0)
            
            # Verify that expanduser was called with the correct argument
            mock_expanduser.assert_called_with("~/")
            
if __name__ == '__main__':
    unittest.main()
