#!/usr/bin/env python3
"""
Test for the alias expansion feature in the executor module.
This tests that commands using aliases are properly expanded before execution.
"""

import os
import sys
import unittest
import json
import tempfile
from unittest import mock

# Add the parent directory to the path so we can import modules properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the modules we need to test
from executor import execute_shell_command

class MockProcess:
    """Mock subprocess process for testing"""
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = mock.MagicMock()
        self.stdout.readline.side_effect = [stdout, ""] if stdout else [""]
        self.stderr = mock.MagicMock()
        self.stderr.readline.side_effect = [stderr, ""] if stderr else [""]
        self.returncode = returncode

    def communicate(self):
        return "", ""

    def wait(self):
        return self.returncode

class TestAliasExpansion(unittest.TestCase):
    """Test alias expansion in the execute_shell_command function"""

    def setUp(self):
        """Setup test environment with mock aliases file."""
        # Create a temporary aliases file
        self.temp_aliases_file = tempfile.NamedTemporaryFile(delete=False)
        aliases_data = {
            "ls": "ls -CF",
            "ll": "ls -la",
            "grep": "grep --color=auto"
        }
        # Write test aliases to the file
        with open(self.temp_aliases_file.name, 'w') as f:
            json.dump(aliases_data, f)

        # Mock the path to the aliases file in the alias_command module
        self.aliases_file_patcher = mock.patch(
            'plugins.alias_command.ALIASES_FILE',
            self.temp_aliases_file.name
        )
        self.aliases_file_mock = self.aliases_file_patcher.start()

        # Mock subprocess.Popen to avoid executing actual commands
        self.popen_patcher = mock.patch('subprocess.Popen')
        self.mock_popen = self.popen_patcher.start()
        self.mock_popen.return_value = MockProcess(stdout="Test output", returncode=0)
        
        # Import the module inside the test to ensure our patches take effect
        import plugins.alias_command
        self.alias_module = plugins.alias_command
        
        # Force reload of aliases from our test file
        self.alias_module.load_aliases()

    def tearDown(self):
        """Clean up test environment."""
        self.aliases_file_patcher.stop()
        self.popen_patcher.stop()
        os.unlink(self.temp_aliases_file.name)

    @mock.patch('click.echo')  # Mock click.echo to capture output
    def test_basic_alias_expansion(self, mock_echo):
        """Test that a simple command with an alias is properly expanded."""
        # Execute a command that should be expanded
        execute_shell_command("ls")
        
        # Check that the expansion message was printed
        mock_echo.assert_any_call(mock.ANY)  # At least one call to echo
        
        # Check that the expanded command was passed to subprocess.Popen
        self.mock_popen.assert_called_once()
        
        # Get the arguments passed to subprocess.Popen
        call_args = self.mock_popen.call_args
        
        # Check how the command is passed (either as first positional arg or as 'args' kwarg)
        command = None
        if 'args' in call_args[1]:  # If passed as keyword arg 'args'
            command = call_args[1]['args']
        else:  # If passed as first positional arg
            command = call_args[0][0]
            
        # The command should be expanded from "ls" to "ls -CF"
        self.assertEqual(command, "ls -CF")

    @mock.patch('click.echo')  # Mock click.echo to capture output
    def test_alias_with_arguments(self, mock_echo):
        """Test that an aliased command with arguments is properly expanded."""
        # Execute a command with arguments that should be expanded
        execute_shell_command("ls /home")
        
        # Get the arguments passed to subprocess.Popen
        call_args = self.mock_popen.call_args
        
        # Check how the command is passed (either as first positional arg or as 'args' kwarg)
        command = None
        if 'args' in call_args[1]:  # If passed as keyword arg 'args'
            command = call_args[1]['args']
        else:  # If passed as first positional arg
            command = call_args[0][0]
            
        # The command should be expanded from "ls /home" to "ls -CF /home"
        self.assertEqual(command, "ls -CF /home")

    @mock.patch('click.echo')  # Mock click.echo to capture output
    def test_unknown_alias_not_expanded(self, mock_echo):
        """Test that a command without an alias is not modified."""
        # Execute a command without an alias
        execute_shell_command("pwd")
        
        # Get the arguments passed to subprocess.Popen
        call_args = self.mock_popen.call_args
        
        # Check how the command is passed (either as first positional arg or as 'args' kwarg)
        command = None
        if 'args' in call_args[1]:  # If passed as keyword arg 'args'
            command = call_args[1]['args']
        else:  # If passed as first positional arg
            command = call_args[0][0]
            
        # The command should not be expanded
        self.assertEqual(command, "pwd")

    @mock.patch('click.echo')  # Mock click.echo to capture output
    def test_complex_alias_expansion(self, mock_echo):
        """Test that a complex command with an alias and pipes is properly expanded."""
        # Execute a complex command with an alias
        execute_shell_command("ls | grep test")
        
        # Get the arguments passed to subprocess.Popen
        call_args = self.mock_popen.call_args
        
        # Check how the command is passed (either as first positional arg or as 'args' kwarg)
        command = None
        if 'args' in call_args[1]:  # If passed as keyword arg 'args'
            command = call_args[1]['args']
        else:  # If passed as first positional arg
            command = call_args[0][0]
            
        # The command should be expanded from "ls | grep test" to "ls -CF | grep --color=auto test"
        self.assertEqual(command, "ls -CF | grep --color=auto test")


if __name__ == '__main__':
    unittest.main()
