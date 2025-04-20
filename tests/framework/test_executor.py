#!/usr/bin/env python
"""
PyATS test script for testing the executor module of Jibberish shell.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import subprocess

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the module to test
import executor
from tests.utils.test_utils import CaptureOutput, mock_click_echo, mock_os_system

# Import PyATS components
from pyats import aetest
from pyats.log.utils import banner

class CommonSetup(aetest.CommonSetup):
    """Common setup tasks for all tests."""
    
    @aetest.subsection
    def setup_environment(self):
        """Set up the test environment."""
        # Mock os.system to prevent actual command execution
        self.os_system_patcher = patch('os.system', side_effect=mock_os_system)
        self.mock_os_system = self.os_system_patcher.start()
        
        # Mock click.echo to capture output
        self.click_echo_patcher = patch('click.echo', side_effect=mock_click_echo)
        self.mock_click_echo = self.click_echo_patcher.start()
        
        # Store the patchers in the parent for cleanup
        self.parent.os_system_patcher = self.os_system_patcher
        self.parent.click_echo_patcher = self.click_echo_patcher

class TestExecutorTransformMultiline(aetest.Testcase):
    """Tests for the transform_multiline function."""
    
    @aetest.test
    def test_single_line_command(self):
        """Test transform_multiline with a single line command."""
        command = "ls -la"
        result = executor.transform_multiline(command)
        assert result == command, f"Expected '{command}' but got '{result}'"
    
    @aetest.test
    def test_multiline_ssh_command(self):
        """Test transform_multiline with a multiline SSH command."""
        command = "ssh user@host\nls -la"
        expected = "ssh user@host \"ls -la\""
        result = executor.transform_multiline(command)
        assert result == expected, f"Expected '{expected}' but got '{result}'"
    
    @aetest.test
    def test_empty_lines(self):
        """Test transform_multiline with empty lines."""
        command = "line1\n\nline3"
        result = executor.transform_multiline(command)
        assert result == "line1\nline3", f"Expected 'line1\nline3' but got '{result}'"

class TestExecutorShellCommand(aetest.Testcase):
    """Tests for the execute_shell_command function."""
    
    @aetest.setup
    def setup(self):
        """Set up the test."""
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
    
    @aetest.teardown
    def teardown(self):
        """Clean up after the test."""
        self.popen_patcher.stop()
    
    @aetest.test
    def test_empty_command(self):
        """Test execute_shell_command with an empty command."""
        return_code, stdout, stderr = executor.execute_shell_command("")
        assert return_code == 0, f"Expected return code 0 but got {return_code}"
        assert stdout == "", f"Expected empty stdout but got '{stdout}'"
        assert stderr == "", f"Expected empty stderr but got '{stderr}'"
    
    @aetest.test
    def test_interactive_command(self):
        """Test execute_shell_command with an interactive command."""
        with patch.object(executor, 'is_interactive', return_value=True):
            return_code, stdout, stderr = executor.execute_shell_command("vim")
            assert return_code == 0, f"Expected return code 0 but got {return_code}"
            assert stdout == "", f"Expected empty stdout but got '{stdout}'"
            assert stderr == "", f"Expected empty stderr but got '{stderr}'"
            self.parent.os_system_patcher.assert_called_once_with("vim")

class TestExecutorCommand(aetest.Testcase):
    """Tests for the execute_command function."""
    
    @aetest.setup
    def setup(self):
        """Set up the test."""
        # Mock execute_shell_command to prevent actual command execution
        self.shell_cmd_patcher = patch.object(
            executor, 'execute_shell_command', 
            return_value=(0, "test output", "")
        )
        self.mock_shell_cmd = self.shell_cmd_patcher.start()
        
        # Mock input function for testing warning prompts
        self.input_patcher = patch('builtins.input', return_value="y")
        self.mock_input = self.input_patcher.start()
    
    @aetest.teardown
    def teardown(self):
        """Clean up after the test."""
        self.shell_cmd_patcher.stop()
        self.input_patcher.stop()
    
    @aetest.test
    def test_normal_command(self):
        """Test execute_command with a normal command."""
        with CaptureOutput() as output:
            executor.execute_command("ls -la")
            self.mock_shell_cmd.assert_called_once_with("ls -la")
    
    @aetest.test
    def test_warn_list_command(self):
        """Test execute_command with a command in the warn list."""
        # Set up a warn list environment variable
        with patch.dict(os.environ, {"WARN_LIST": "rm"}):
            executor.execute_command("rm file.txt")
            self.mock_input.assert_called_once()
            self.mock_shell_cmd.assert_called_once_with("rm file.txt")
    
    @aetest.test
    def test_warn_list_rejection(self):
        """Test execute_command with a rejected warning."""
        # Mock input to return "n" (rejection)
        self.mock_input.return_value = "n"
        with patch.dict(os.environ, {"WARN_LIST": "rm"}):
            executor.execute_command("rm file.txt")
            self.mock_input.assert_called_once()
            self.mock_shell_cmd.assert_not_called()

class TestExecutorChainedCommands(aetest.Testcase):
    """Tests for the execute_chained_commands function."""
    
    @aetest.setup
    def setup(self):
        """Set up the test."""
        # Mock execute_command to prevent actual command execution
        self.cmd_patcher = patch.object(executor, 'execute_command')
        self.mock_cmd = self.cmd_patcher.start()
        
        # Mock built_ins.is_built_in
        self.builtin_patcher = patch.object(executor, 'is_built_in', return_value=(False, None))
        self.mock_builtin = self.builtin_patcher.start()
    
    @aetest.teardown
    def teardown(self):
        """Clean up after the test."""
        self.cmd_patcher.stop()
        self.builtin_patcher.stop()
    
    @aetest.test
    def test_single_command(self):
        """Test execute_chained_commands with a single command."""
        executor.execute_chained_commands("ls -la")
        self.mock_cmd.assert_called_once_with("ls -la")
    
    @aetest.test
    def test_multiple_commands(self):
        """Test execute_chained_commands with multiple commands."""
        executor.execute_chained_commands("cd /tmp && ls -la")
        assert self.mock_cmd.call_count == 2, f"Expected 2 calls but got {self.mock_cmd.call_count}"
        # Check that each command was executed
        self.mock_cmd.assert_any_call("cd /tmp")
        self.mock_cmd.assert_any_call("ls -la")
    
    @aetest.test
    def test_empty_commands(self):
        """Test execute_chained_commands with empty commands."""
        executor.execute_chained_commands("ls && && cd /tmp")
        assert self.mock_cmd.call_count == 2, f"Expected 2 calls but got {self.mock_cmd.call_count}"
        # Check that each non-empty command was executed
        self.mock_cmd.assert_any_call("ls")
        self.mock_cmd.assert_any_call("cd /tmp")

class CommonCleanup(aetest.CommonCleanup):
    """Common cleanup tasks for all tests."""
    
    @aetest.subsection
    def cleanup_environment(self):
        """Clean up the test environment."""
        self.parent.os_system_patcher.stop()
        self.parent.click_echo_patcher.stop()

if __name__ == '__main__':
    # Run the test
    aetest.main()
