#!/usr/bin/env python
"""
Tests for the LinuxCommandTool specifically.
"""
import os
import sys
import unittest
from unittest.mock import patch, Mock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the linux command tool
from app.tools.linux_command import LinuxCommandTool


class TestLinuxCommandTool(unittest.TestCase):
    """Tests for the LinuxCommandTool."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        self.tool = LinuxCommandTool()
        
        # Store original environment variables to restore later
        self.original_warn_list = os.environ.get("WARN_LIST", "")
        self.original_prompt_ai = os.environ.get("PROMPT_AI_COMMANDS", "")
    
    def tearDown(self):
        """Clean up after each test method."""
        # Restore original environment variables
        if self.original_warn_list:
            os.environ["WARN_LIST"] = self.original_warn_list
        elif "WARN_LIST" in os.environ:
            del os.environ["WARN_LIST"]
            
        if self.original_prompt_ai:
            os.environ["PROMPT_AI_COMMANDS"] = self.original_prompt_ai
        elif "PROMPT_AI_COMMANDS" in os.environ:
            del os.environ["PROMPT_AI_COMMANDS"]
    
    def test_tool_properties(self):
        """Test that the tool has the correct properties."""
        self.assertEqual(self.tool.name, "linux_command")
        self.assertIn("Execute Linux shell commands", self.tool.description)
        self.assertIn("ALWAYS use this tool", self.tool.description)
        
        # Check parameters structure
        params = self.tool.parameters
        self.assertEqual(params["type"], "object")
        self.assertIn("command", params["properties"])
        self.assertIn("command", params["required"])
        
        # Check command parameter details
        command_param = params["properties"]["command"]
        self.assertEqual(command_param["type"], "string")
        self.assertIn("description", command_param)
        self.assertIn("Linux command to execute", command_param["description"])
    
    @patch('app.tools.linux_command.prompt_before_execution')
    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_successful_command_execution(self, mock_execute, mock_prompt):
        """Test successful command execution."""
        # Setup mocks
        mock_prompt.return_value = True
        mock_execute.return_value = (True, "Command executed successfully")
        
        # Execute command
        result = self.tool.execute("echo 'hello world'")
        
        # Verify mocks were called correctly
        mock_prompt.assert_called_once_with("command 'echo 'hello world''")
        mock_execute.assert_called_once_with("echo 'hello world'")
        
        # Verify result
        self.assertEqual(result, "Command executed successfully")
    
    @patch('app.tools.linux_command.prompt_before_execution')
    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_failed_command_execution(self, mock_execute, mock_prompt):
        """Test failed command execution."""
        # Setup mocks
        mock_prompt.return_value = True
        mock_execute.return_value = (False, "ERROR: Command failed: No such file or directory")
        
        # Execute command
        result = self.tool.execute("ls /nonexistent/directory")
        
        # Verify mocks were called correctly
        mock_prompt.assert_called_once_with("command 'ls /nonexistent/directory'")
        mock_execute.assert_called_once_with("ls /nonexistent/directory")
        
        # Verify result (error message should be passed through)
        self.assertEqual(result, "ERROR: Command failed: No such file or directory")
    
    @patch('app.tools.linux_command.prompt_before_execution')
    def test_command_execution_cancelled_by_prompt(self, mock_prompt):
        """Test command execution cancelled by user prompt."""
        # Ensure WARN_LIST doesn't block our test command
        os.environ["WARN_LIST"] = ""
        
        # Setup mock to simulate user cancellation
        mock_prompt.return_value = False
        
        # Execute command (use a safe command that won't be in WARN_LIST)
        result = self.tool.execute("echo 'test command'")
        
        # Verify prompt was called
        mock_prompt.assert_called_once_with("command 'echo 'test command''")
        
        # Verify cancellation message
        self.assertIn("Command execution cancelled", result)
        self.assertIn("echo 'test command'", result)
    
    def test_warn_list_security_check_single_command(self):
        """Test that commands in WARN_LIST are blocked."""
        # Set up WARN_LIST environment variable
        os.environ["WARN_LIST"] = "rm,sudo,dd"
        
        # Test each command in warn list
        dangerous_commands = ["rm -rf /", "sudo rm -rf /", "dd if=/dev/zero"]
        
        for cmd in dangerous_commands:
            with self.subTest(command=cmd):
                result = self.tool.execute(cmd)
                
                self.assertIn("SECURITY:", result)
                self.assertIn("Cannot execute command", result)
                self.assertIn("WARN_LIST", result)
                self.assertIn(cmd, result)
    
    def test_warn_list_security_check_all_commands(self):
        """Test that WARN_LIST='all' blocks all commands."""
        # Set WARN_LIST to 'all'
        os.environ["WARN_LIST"] = "all"
        
        # Test that any command is blocked
        result = self.tool.execute("echo 'safe command'")
        
        self.assertIn("SECURITY:", result)
        self.assertIn("Cannot execute command", result)
        self.assertIn("WARN_LIST", result)
    
    def test_warn_list_partial_match(self):
        """Test that WARN_LIST matches command prefixes correctly."""
        # Set up WARN_LIST with partial commands
        os.environ["WARN_LIST"] = "rm,sudo"
        
        # Test commands that start with warn list items
        blocked_commands = ["rm file.txt", "rmdir directory", "sudo ls", "sudo -u user cmd"]
        
        for cmd in blocked_commands:
            with self.subTest(command=cmd):
                result = self.tool.execute(cmd)
                self.assertIn("SECURITY:", result)
    
    def test_warn_list_safe_commands(self):
        """Test that safe commands are not blocked by WARN_LIST."""
        # Set up WARN_LIST
        os.environ["WARN_LIST"] = "rm,sudo,dd"
        
        with patch('app.tools.linux_command.prompt_before_execution') as mock_prompt, \
             patch('app.tools.linux_command.execute_command_with_built_ins') as mock_execute:
            
            mock_prompt.return_value = True
            mock_execute.return_value = (True, "Safe command executed")
            
            # Test safe commands that don't match warn list
            safe_commands = ["ls -la", "echo hello", "cat file.txt", "grep pattern file"]
            
            for cmd in safe_commands:
                with self.subTest(command=cmd):
                    result = self.tool.execute(cmd)
                    
                    # Should not contain security warning
                    self.assertNotIn("SECURITY:", result)
                    self.assertEqual(result, "Safe command executed")
    
    def test_warn_list_empty_or_missing(self):
        """Test behavior when WARN_LIST is empty or not set."""
        # Test with empty WARN_LIST
        os.environ["WARN_LIST"] = ""
        
        with patch('app.tools.linux_command.prompt_before_execution') as mock_prompt, \
             patch('app.tools.linux_command.execute_command_with_built_ins') as mock_execute:
            
            mock_prompt.return_value = True
            mock_execute.return_value = (True, "Command executed")
            
            result = self.tool.execute("rm file.txt")
            
            # Should not be blocked
            self.assertNotIn("SECURITY:", result)
            self.assertEqual(result, "Command executed")
        
        # Test with missing WARN_LIST
        if "WARN_LIST" in os.environ:
            del os.environ["WARN_LIST"]
        
        with patch('app.tools.linux_command.prompt_before_execution') as mock_prompt, \
             patch('app.tools.linux_command.execute_command_with_built_ins') as mock_execute:
            
            mock_prompt.return_value = True
            mock_execute.return_value = (True, "Command executed")
            
            result = self.tool.execute("rm file.txt")
            
            # Should not be blocked
            self.assertNotIn("SECURITY:", result)
            self.assertEqual(result, "Command executed")
    
    def test_warn_list_whitespace_handling(self):
        """Test that WARN_LIST handles whitespace correctly."""
        # Set up WARN_LIST with whitespace
        os.environ["WARN_LIST"] = " rm , sudo , dd "
        
        result = self.tool.execute("rm file.txt")
        
        self.assertIn("SECURITY:", result)
        self.assertIn("Cannot execute command", result)
    
    @patch('app.tools.linux_command.prompt_before_execution')
    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_exception_handling(self, mock_execute, mock_prompt):
        """Test that exceptions are properly caught and handled."""
        # Setup mocks to raise an exception
        mock_prompt.return_value = True
        mock_execute.side_effect = Exception("Unexpected error occurred")
        
        # Execute command
        result = self.tool.execute("some command")
        
        # Verify error is caught and formatted
        self.assertIn("ERROR:", result)
        self.assertIn("Failed to execute command", result)
        self.assertIn("some command", result)
        self.assertIn("Unexpected error occurred", result)
    
    @patch('app.tools.linux_command.prompt_before_execution')
    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_command_chaining(self, mock_execute, mock_prompt):
        """Test that command chaining is properly passed through."""
        # Setup mocks
        mock_prompt.return_value = True
        mock_execute.return_value = (True, "Commands chained successfully")
        
        # Test command chaining with &&
        chained_command = "mkdir test_dir && cd test_dir && ls -la"
        result = self.tool.execute(chained_command)
        
        # Verify the full chained command was passed to execute_command_with_built_ins
        mock_execute.assert_called_once_with(chained_command)
        self.assertEqual(result, "Commands chained successfully")
    
    def test_function_definition_format(self):
        """Test that the tool generates a proper function definition."""
        definition = self.tool.to_function_definition()
        
        self.assertEqual(definition["name"], "linux_command")
        self.assertIn("description", definition)
        self.assertIn("parameters", definition)
        self.assertEqual(definition["parameters"]["type"], "object")
        
        # Check that command parameter is present
        properties = definition["parameters"]["properties"]
        self.assertIn("command", properties)
        
        # Check parameter descriptions
        self.assertIn("description", properties["command"])
        self.assertEqual(properties["command"]["type"], "string")
        
        # Check required parameters
        self.assertIn("required", definition["parameters"])
        self.assertIn("command", definition["parameters"]["required"])
    
    def test_is_command_in_warn_list_method(self):
        """Test the internal _is_command_in_warn_list method directly."""
        # Test with specific warn list
        os.environ["WARN_LIST"] = "rm,sudo,dd"
        
        # Test positive cases
        self.assertTrue(self.tool._is_command_in_warn_list("rm file.txt"))
        self.assertTrue(self.tool._is_command_in_warn_list("sudo ls"))
        self.assertTrue(self.tool._is_command_in_warn_list("dd if=/dev/zero"))
        
        # Test negative cases
        self.assertFalse(self.tool._is_command_in_warn_list("ls -la"))
        self.assertFalse(self.tool._is_command_in_warn_list("echo hello"))
        self.assertFalse(self.tool._is_command_in_warn_list("cat file.txt"))
        
        # Test 'all' case
        os.environ["WARN_LIST"] = "all"
        self.assertTrue(self.tool._is_command_in_warn_list("any command"))
        self.assertTrue(self.tool._is_command_in_warn_list("ls"))
        
        # Test empty warn list
        os.environ["WARN_LIST"] = ""
        self.assertFalse(self.tool._is_command_in_warn_list("rm file.txt"))
        
        # Test missing warn list
        if "WARN_LIST" in os.environ:
            del os.environ["WARN_LIST"]
        self.assertFalse(self.tool._is_command_in_warn_list("rm file.txt"))
    
    def test_command_whitespace_handling(self):
        """Test that commands with leading/trailing whitespace are handled correctly."""
        os.environ["WARN_LIST"] = "rm,sudo"
        
        # Test commands with whitespace
        whitespace_commands = [
            "  rm file.txt  ",
            "\trm file.txt\n",
            "   sudo ls   "
        ]
        
        for cmd in whitespace_commands:
            with self.subTest(command=repr(cmd)):
                result = self.tool.execute(cmd)
                self.assertIn("SECURITY:", result)
    
    @patch('app.tools.linux_command.prompt_before_execution')
    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_empty_command(self, mock_execute, mock_prompt):
        """Test behavior with empty command."""
        mock_prompt.return_value = True
        mock_execute.return_value = (True, "")
        
        result = self.tool.execute("")
        
        # Should still call the execution pipeline
        mock_prompt.assert_called_once_with("command ''")
        mock_execute.assert_called_once_with("")
    
    @patch('app.tools.linux_command.prompt_before_execution')
    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_complex_command_with_special_characters(self, mock_execute, mock_prompt):
        """Test commands with special characters and complex syntax."""
        mock_prompt.return_value = True
        mock_execute.return_value = (True, "Complex command executed")
        
        complex_command = "find /path -name '*.txt' | grep -E '^[A-Z]' | sort | head -10"
        result = self.tool.execute(complex_command)
        
        mock_execute.assert_called_once_with(complex_command)
        self.assertEqual(result, "Complex command executed")
    
    def test_warn_list_case_sensitivity(self):
        """Test that WARN_LIST matching is case sensitive."""
        os.environ["WARN_LIST"] = "rm,sudo"
        
        # Test that case matters (these should NOT be blocked)
        with patch('app.tools.linux_command.prompt_before_execution') as mock_prompt, \
             patch('app.tools.linux_command.execute_command_with_built_ins') as mock_execute:
            
            mock_prompt.return_value = True
            mock_execute.return_value = (True, "Command executed")
            
            # These should be allowed (different case)
            case_different_commands = ["RM file.txt", "SUDO ls", "Rm file.txt"]
            
            for cmd in case_different_commands:
                with self.subTest(command=cmd):
                    result = self.tool.execute(cmd)
                    # Should NOT contain security warning (case sensitive)
                    self.assertNotIn("SECURITY:", result)
                    self.assertEqual(result, "Command executed")


if __name__ == '__main__':
    # Run the tests with verbose output
    unittest.main(verbosity=2)