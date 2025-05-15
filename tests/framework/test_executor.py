#!/usr/bin/env python
"""
Complete self-contained test suite for executor module.
This file contains all tests and does not rely on test discovery.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from tests import test_helper

# Add the parent directory to the path so we can import modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, parent_dir)

# Import test utilities directly
try:
    from tests.utils.test_utils import CaptureOutput, mock_click_echo, mock_os_system
    print("Successfully imported test utilities")
except ImportError as e:
    print(f"WARNING: Failed to import test utilities: {e}")
    
    # Create simple mock versions if imports fail
    class CaptureOutput:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    
    def mock_click_echo(*args, **kwargs):
        pass
    
    def mock_os_system(*args, **kwargs):
        return 0

# Mark this module as a test module for run_tests.py
IS_TEST_MODULE = True

# Import executor module directly
from app import executor

# Store executor module reference
_executor = executor

def get_executor():
    """Return the executor module."""
    global _executor
    if _executor is None:
        from app import executor
        _executor = executor
        print("Successfully imported executor module")
    return _executor

# Basic Test
class TestBasic(unittest.TestCase):
    """Very basic test to verify unittest is working."""
    
    def test_true(self):
        """Test that True is True."""
        self.assertTrue(True)
        print("Basic test passed!")

# Transform Multiline Tests
class TestTransformMultiline(unittest.TestCase):
    """Tests for the transform_multiline function."""
    
    def setUp(self):
        """Set up the test environment."""
        print(f"\nSetting up {self.__class__.__name__}")
        self.executor = get_executor()
        
        # Mock os.system to prevent actual command execution
        self.os_system_patcher = patch('os.system', side_effect=mock_os_system)
        self.mock_os_system = self.os_system_patcher.start()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
    
    def tearDown(self):
        """Clean up after the test."""
        print(f"Tearing down {self.__class__.__name__}")
        self.os_system_patcher.stop()
        self.click_echo_patcher.stop()
    
    def test_single_line_command(self):
        """Test transform_multiline with a single line command."""
        print("Running test_single_line_command")
        command = "ls -la"
        result = executor.transform_multiline(command)
        self.assertEqual(result, command, f"Expected '{command}' but got '{result}'")
        print("test_single_line_command passed!")
    
    def test_multiline_ssh_command(self):
        """Test transform_multiline with a multiline SSH command."""
        print("Running test_multiline_ssh_command")
        command = "ssh user@host\nls -la"
        expected = "ssh user@host \"ls -la\""
        result = executor.transform_multiline(command)
        self.assertEqual(result, expected, f"Expected '{expected}' but got '{result}'")
        print("test_multiline_ssh_command passed!")
    
    def test_empty_lines(self):
        """Test transform_multiline with empty lines."""
        print("Running test_empty_lines")
        command = "line1\n\nline3"
        result = executor.transform_multiline(command)
        self.assertEqual(result, "line1\nline3", f"Expected 'line1\nline3' but got '{result}'")
        print("test_empty_lines passed!")

# Shell Command Tests
class TestShellCommand(unittest.TestCase):
    """Tests for the execute_shell_command function."""
    
    def setUp(self):
        """Set up the test."""
        print(f"\nSetting up {self.__class__.__name__}")
        self.executor = get_executor()
        
        # Mock os.system to prevent actual command execution
        self.os_system_patcher = patch('os.system', side_effect=mock_os_system)
        self.mock_os_system = self.os_system_patcher.start()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Mock subprocess.Popen to prevent actual command execution
        self.popen_patcher = patch('subprocess.Popen')
        self.mock_popen = self.popen_patcher.start()
        
        # Set up the mock process
        self.mock_process = MagicMock()
        self.mock_process.stdout = MagicMock()
        self.mock_process.stderr = MagicMock()
        self.mock_process.poll.return_value = 0  # Process finished
        self.mock_process.wait.return_value = 0  # Return success code
        self.mock_popen.return_value = self.mock_process
    
    def tearDown(self):
        """Clean up after the test."""
        print(f"Tearing down {self.__class__.__name__}")
        self.popen_patcher.stop()
        self.os_system_patcher.stop()
        self.click_echo_patcher.stop()
    
    def test_empty_command(self):
        """Test execute_shell_command with an empty command."""
        print("Running test_empty_command")
        return_code, stdout, stderr = executor.execute_shell_command("")
        self.assertEqual(return_code, 0, f"Expected return code 0 but got {return_code}")
        self.assertEqual(stdout, "", f"Expected empty stdout but got '{stdout}'")
        self.assertEqual(stderr, "", f"Expected empty stderr but got '{stderr}'")
        print("test_empty_command passed!")
    
    def test_interactive_command(self):
        """Test execute_shell_command with an interactive command."""
        print("Running test_interactive_command")
        # Since the original code checks if a command is in the interactive list,
        # we'll patch os.environ.get to return a list that includes our test command
        # Also patch subprocess.Popen for our new implementation
        with patch.dict(os.environ, {"INTERACTIVE_LIST": "vim,nano"}):
            with patch('subprocess.Popen') as mock_popen:
                # Set up the mock to return a process-like object
                mock_process = MagicMock()
                mock_process.wait.return_value = 0
                mock_popen.return_value = mock_process
                
                # Also patch signal module since we're using it for interactive commands
                with patch('signal.signal') as mock_signal:
                    return_code, stdout, stderr = executor.execute_shell_command("vim")
                    
                    # Verify the return values
                    self.assertEqual(return_code, 0, f"Expected return code 0 but got {return_code}")
                    self.assertEqual(stdout, "", f"Expected empty stdout but got '{stdout}'")
                    self.assertEqual(stderr, "", f"Expected empty stderr but got '{stderr}'")
                    
                    # Verify Popen was called with the right arguments
                    mock_popen.assert_called_once()
                    args, kwargs = mock_popen.call_args
                    self.assertEqual(kwargs['shell'], True)
                    self.assertEqual(args[0], "vim")
        print("test_interactive_command passed!")

# Command Tests
class TestCommand(unittest.TestCase):
    """Tests for the execute_command function."""
    
    def setUp(self):
        """Set up the test."""
        print(f"\nSetting up {self.__class__.__name__}")
        self.executor = get_executor()
        
        # Mock os.system to prevent actual command execution
        self.os_system_patcher = patch('os.system', side_effect=mock_os_system)
        self.mock_os_system = self.os_system_patcher.start()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Mock execute_shell_command to prevent actual command execution
        self.shell_cmd_patcher = patch.object(
            self.executor, 'execute_shell_command', 
            return_value=(0, "test output", "")
        )
        self.mock_shell_cmd = self.shell_cmd_patcher.start()
        
        # Mock input function for testing warning prompts
        self.input_patcher = patch('builtins.input', return_value="y")
        self.mock_input = self.input_patcher.start()
    
    def tearDown(self):
        """Clean up after the test."""
        print(f"Tearing down {self.__class__.__name__}")
        self.shell_cmd_patcher.stop()
        self.input_patcher.stop()
        self.os_system_patcher.stop()
        self.click_echo_patcher.stop()
    
    def test_normal_command(self):
        """Test execute_command with a normal command."""
        print("Running test_normal_command")
        with CaptureOutput() as output:
            executor.execute_command("ls -la")
            self.mock_shell_cmd.assert_called_once_with("ls -la")
        print("test_normal_command passed!")
    
    def test_warn_list_command(self):
        """Test execute_command with a command in the warn list."""
        print("Running test_warn_list_command")
        # Set up a warn list environment variable
        with patch.dict(os.environ, {"WARN_LIST": "rm"}):
            executor.execute_command("rm file.txt")
            self.mock_input.assert_called_once()
            self.mock_shell_cmd.assert_called_once_with("rm file.txt")
        print("test_warn_list_command passed!")
    
    def test_warn_list_rejection(self):
        """Test execute_command with a rejected warning."""
        print("Running test_warn_list_rejection")
        # Mock input to return "n" (rejection)
        self.mock_input.return_value = "n"
        with patch.dict(os.environ, {"WARN_LIST": "rm"}):
            executor.execute_command("rm file.txt")
            self.mock_input.assert_called_once()
            self.mock_shell_cmd.assert_not_called()
        print("test_warn_list_rejection passed!")

# Chained Commands Tests
class TestChainedCommands(unittest.TestCase):
    """Tests for the execute_chained_commands function."""
    
    def setUp(self):
        """Set up the test."""
        print(f"\nSetting up {self.__class__.__name__}")
        self.executor = get_executor()
        
        # Mock os.system to prevent actual command execution
        self.os_system_patcher = patch('os.system', side_effect=mock_os_system)
        self.mock_os_system = self.os_system_patcher.start()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Mock execute_command to prevent actual command execution
        self.cmd_patcher = patch.object(self.executor, 'execute_command')
        self.mock_cmd = self.cmd_patcher.start()
        
        # Mock app.built_ins.is_built_in
        self.builtin_patcher = patch.object(self.executor, 'is_built_in', return_value=(False, None))
        self.mock_builtin = self.builtin_patcher.start()
    
    def tearDown(self):
        """Clean up after the test."""
        print(f"Tearing down {self.__class__.__name__}")
        self.cmd_patcher.stop()
        self.builtin_patcher.stop()
        self.os_system_patcher.stop()
        self.click_echo_patcher.stop()
    
    def test_single_command(self):
        """Test execute_chained_commands with a single command."""
        print("Running test_single_command")
        executor.execute_chained_commands("ls -la", 0)
        self.mock_cmd.assert_called_once_with("ls -la")
        print("test_single_command passed!")
    
    def test_multiple_commands(self):
        """Test execute_chained_commands with multiple commands."""
        print("Running test_multiple_commands")
        executor.execute_chained_commands("cd /tmp && ls -la", 0)
        self.assertEqual(self.mock_cmd.call_count, 2, f"Expected 2 calls but got {self.mock_cmd.call_count}")
        # Check that each command was executed
        self.mock_cmd.assert_any_call("cd /tmp")
        self.mock_cmd.assert_any_call("ls -la")
        print("test_multiple_commands passed!")
    
    def test_empty_commands(self):
        """Test execute_chained_commands with empty commands."""
        print("Running test_empty_commands")
        executor.execute_chained_commands("ls && && cd /tmp")
        self.assertEqual(self.mock_cmd.call_count, 2, f"Expected 2 calls but got {self.mock_cmd.call_count}")
        # Check that each non-empty command was executed
        self.mock_cmd.assert_any_call("ls")
        self.mock_cmd.assert_any_call("cd /tmp")
        print("test_empty_commands passed!")
        
    def test_quoted_and_operators(self):
        """Test execute_chained_commands with quoted strings containing && operators."""
        print("Running test_quoted_and_operators")
        
        # Reset mock for this test
        self.mock_cmd.reset_mock()
        
        # Test with single quotes containing &&
        single_quoted_cmd = "echo 'This && should be treated as one' && echo Second"
        executor.execute_chained_commands(single_quoted_cmd)
        self.assertEqual(self.mock_cmd.call_count, 2, f"Expected 2 calls but got {self.mock_cmd.call_count}")
        # Check that commands were properly split respecting quotes
        self.mock_cmd.assert_any_call("echo 'This && should be treated as one'")
        self.mock_cmd.assert_any_call("echo Second")
        
        # Reset mock for next test
        self.mock_cmd.reset_mock()
        
        # Test with double quotes containing &&
        double_quoted_cmd = 'echo "First && not a separator" && echo Final'
        executor.execute_chained_commands(double_quoted_cmd)
        self.assertEqual(self.mock_cmd.call_count, 2, f"Expected 2 calls but got {self.mock_cmd.call_count}")
        # Check that commands were properly split respecting quotes
        self.mock_cmd.assert_any_call('echo "First && not a separator"')
        self.mock_cmd.assert_any_call("echo Final")
        
        # Reset mock for next test
        self.mock_cmd.reset_mock()
        
        # Test with nested quotes
        nested_quotes_cmd = 'echo "Outer \'inner && still outer\' end" && echo Last'
        executor.execute_chained_commands(nested_quotes_cmd)
        self.assertEqual(self.mock_cmd.call_count, 2, f"Expected 2 calls but got {self.mock_cmd.call_count}")
        # Check that commands were properly split respecting nested quotes
        self.mock_cmd.assert_any_call('echo "Outer \'inner && still outer\' end"')
        self.mock_cmd.assert_any_call("echo Last")
        
        print("test_quoted_and_operators passed!")

# When run directly
if __name__ == '__main__':
    print("\n=== EXECUTOR MODULE COMPLETE TEST SUITE ===")
    print(f"Running from directory: {os.getcwd()}")
    
    # Create a test suite with all tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests from TestBasic
    suite.addTest(loader.loadTestsFromTestCase(TestBasic))
    
    # Add tests from TestTransformMultiline
    suite.addTest(loader.loadTestsFromTestCase(TestTransformMultiline))
    
    # Add tests from TestShellCommand
    suite.addTest(loader.loadTestsFromTestCase(TestShellCommand))
    
    # Add tests from TestCommand
    suite.addTest(loader.loadTestsFromTestCase(TestCommand))
    
    # Add tests from TestChainedCommands
    suite.addTest(loader.loadTestsFromTestCase(TestChainedCommands))
    
    # Run the tests with TextTestRunner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Ran {result.testsRun} tests")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED")
    else:
        print("\n❌ SOME TESTS FAILED")
        if result.failures:
            print("\nFailures:")
            for test, trace in result.failures:
                print(f"- {test}: {trace}")
        if result.errors:
            print("\nErrors:")
            for test, trace in result.errors:
                print(f"- {test}: {trace}")
    
    # Exit with appropriate status code
    sys.exit(not result.wasSuccessful())
