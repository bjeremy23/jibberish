#!/usr/bin/env python
"""
Fixed tests for the LinuxCommandTool specifically.
"""
import unittest
from unittest.mock import patch, Mock
import os
import sys

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the linux command tool
from app.tools.linux_command import LinuxCommandTool


class TestLinuxCommandTool(unittest.TestCase):
    """Tests for the LinuxCommandTool."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.tool = LinuxCommandTool()
        
        # Store original environment variables
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
        self.assertIn("Use this tool if a request requires execution on the host", self.tool.description)
        self.assertIn("executable linux command strings", self.tool.description)
        
        # Check parameters structure
        params = self.tool.parameters
        self.assertEqual(params["type"], "object")
        self.assertIn("command", params["properties"])
        self.assertIn("required", params)
        self.assertEqual(params["required"], ["command"])
    
    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_successful_command_execution(self, mock_execute):
        """Test successful command execution."""
        # Setup mocks
        mock_execute.return_value = (0, "Command executed successfully")
        
        # Execute command
        result = self.tool.execute("echo 'hello world'")
        
        # Verify mocks were called correctly
        mock_execute.assert_called_once_with("echo 'hello world'", original_command="echo 'hello world'", add_to_history=True)
        
        # Verify result
        self.assertEqual(result, "SUCCESS: Command executed successfully")

    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_failed_command_execution(self, mock_execute):
        """Test failed command execution."""
        # Setup mocks
        mock_execute.return_value = (1, "Command failed: No such file or directory")
        
        # Execute command
        result = self.tool.execute("ls /nonexistent/directory")
        
        # Verify mocks were called correctly
        mock_execute.assert_called_once_with("ls /nonexistent/directory", original_command="ls /nonexistent/directory", add_to_history=True)
        
        # Verify result contains error message
        self.assertIn("ERROR", result)
        self.assertIn("Command failed: No such file or directory", result)

    def test_exception_handling(self):
        """Test that exceptions are properly caught and handled."""
        with patch('app.tools.linux_command.execute_command_with_built_ins') as mock_execute:
            # Setup mock to raise an exception
            mock_execute.side_effect = Exception("Unexpected error occurred")
            
            # Execute command
            result = self.tool.execute("some command")
            
            # Verify error is caught and formatted
            self.assertIn("ERROR:", result)
            self.assertIn("Unexpected error occurred", result)

    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_warn_list_security_check_single_command(self, mock_execute):
        """Test that tools bypass WARN_LIST security checks."""
        # Set up WARN_LIST environment variable
        os.environ["WARN_LIST"] = "rm,sudo,dd"
        
        # Mock successful execution
        mock_execute.return_value = (0, "Command executed via tool")
        
        # Test each command in warn list - should now execute since tools bypass WARN_LIST
        dangerous_commands = ["rm -rf /", "sudo rm -rf /", "dd if=/dev/zero"]
        
        for cmd in dangerous_commands:
            with self.subTest(command=cmd):
                result = self.tool.execute(cmd)
                
                # Tools should bypass WARN_LIST and execute successfully
                self.assertNotIn("SECURITY:", result)
                self.assertEqual(result, "SUCCESS: Command executed via tool")

    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_warn_list_security_check_all_commands(self, mock_execute):
        """Test that tools bypass WARN_LIST='all' security checks."""
        # Set WARN_LIST to 'all'
        os.environ["WARN_LIST"] = "all"
        
        # Mock successful execution
        mock_execute.return_value = (0, "Command executed via tool")
        
        # Test that command executes despite WARN_LIST='all' since tools bypass WARN_LIST
        result = self.tool.execute("echo 'safe command'")
        
        self.assertNotIn("SECURITY:", result)
        self.assertEqual(result, "SUCCESS: Command executed via tool")

    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_warn_list_partial_match(self, mock_execute):
        """Test that tools bypass WARN_LIST partial matching."""
        # Set up WARN_LIST with partial commands
        os.environ["WARN_LIST"] = "rm,sudo"
        
        # Mock successful execution
        mock_execute.return_value = (0, "Command executed via tool")
        
        # Test commands that start with warn list items - should execute since tools bypass WARN_LIST
        blocked_commands = ["rm file.txt", "rmdir directory", "sudo ls", "sudo -u user cmd"]
        
        for cmd in blocked_commands:
            with self.subTest(command=cmd):
                result = self.tool.execute(cmd)
                self.assertNotIn("SECURITY:", result)
                self.assertEqual(result, "SUCCESS: Command executed via tool")

    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_warn_list_safe_commands(self, mock_execute):
        """Test that safe commands are not blocked by WARN_LIST."""
        # Set up WARN_LIST
        os.environ["WARN_LIST"] = "rm,sudo,dd"
        
        mock_execute.return_value = (0, "Safe command executed")
        
        # Test safe commands that don't match warn list
        safe_commands = ["ls -la", "echo hello", "cat file.txt", "grep pattern file"]
        
        for cmd in safe_commands:
            with self.subTest(command=cmd):
                result = self.tool.execute(cmd)
                
                # Should not contain security warning
                self.assertNotIn("SECURITY:", result)
                self.assertEqual(result, "SUCCESS: Safe command executed")

    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_warn_list_empty_or_missing(self, mock_execute):
        """Test behavior when WARN_LIST is empty or not set."""
        # Test with empty WARN_LIST
        os.environ["WARN_LIST"] = ""
        
        mock_execute.return_value = (0, "Command executed")
        
        result = self.tool.execute("rm file.txt")
        
        # Should not be blocked
        self.assertNotIn("SECURITY:", result)
        self.assertEqual(result, "SUCCESS: Command executed")

    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_warn_list_whitespace_handling(self, mock_execute):
        """Test that tools bypass WARN_LIST with whitespace handling."""
        # Set up WARN_LIST with whitespace
        os.environ["WARN_LIST"] = " rm , sudo , dd "
        
        # Mock successful execution
        mock_execute.return_value = (0, "Command executed via tool")
        
        result = self.tool.execute("rm file.txt")
        
        # Tools should bypass WARN_LIST regardless of whitespace
        self.assertNotIn("SECURITY:", result)
        self.assertEqual(result, "SUCCESS: Command executed via tool")

    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_warn_list_case_sensitivity(self, mock_execute):
        """Test that WARN_LIST matching is case sensitive."""
        os.environ["WARN_LIST"] = "rm,sudo"
        
        mock_execute.return_value = (0, "Command executed")
        
        # These should be allowed (different case)
        case_different_commands = ["RM file.txt", "SUDO ls", "Rm file.txt"]
        
        for cmd in case_different_commands:
            with self.subTest(command=cmd):
                result = self.tool.execute(cmd)
                # Should NOT contain security warning (case sensitive)
                self.assertNotIn("SECURITY:", result)
                self.assertEqual(result, "SUCCESS: Command executed")

    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_command_whitespace_handling(self, mock_execute):
        """Test that tools handle commands with whitespace and bypass WARN_LIST."""
        os.environ["WARN_LIST"] = "rm,sudo"
        
        # Mock successful execution
        mock_execute.return_value = (0, "Command executed via tool")
        
        # Test commands with whitespace - should execute since tools bypass WARN_LIST
        whitespace_commands = [
            "  rm file.txt  ",
            "\trm file.txt\n",
            "   sudo ls   "
        ]
        
        for cmd in whitespace_commands:
            with self.subTest(command=repr(cmd)):
                result = self.tool.execute(cmd)
                self.assertNotIn("SECURITY:", result)
                self.assertEqual(result, "SUCCESS: Command executed via tool")

    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_empty_command(self, mock_execute):
        """Test behavior with empty command."""
        mock_execute.return_value = (0, "")
        
        result = self.tool.execute("")
        
        # Should execute empty command
        mock_execute.assert_called_once_with("", original_command="", add_to_history=True)
        self.assertEqual(result, "SUCCESS: ")

    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_command_chaining(self, mock_execute):
        """Test that command chaining is properly passed through."""
        # Setup mocks
        mock_execute.return_value = (0, "Commands chained successfully")
        
        # Test command chaining with &&
        chained_command = "mkdir test_dir && cd test_dir && ls -la"
        result = self.tool.execute(chained_command)
        
        # Verify the full chained command was passed to execute_command_with_built_ins
        mock_execute.assert_called_once_with(chained_command, original_command=chained_command, add_to_history=True)
        self.assertEqual(result, "SUCCESS: Commands chained successfully")

    @patch('app.tools.linux_command.execute_command_with_built_ins')
    def test_complex_command_with_special_characters(self, mock_execute):
        """Test commands with special characters and complex syntax."""
        mock_execute.return_value = (0, "Complex command executed")
        
        complex_command = "find /path -name '*.txt' | grep -E '^[A-Z]' | sort | head -10"
        result = self.tool.execute(complex_command)
        
        mock_execute.assert_called_once_with(complex_command, original_command=complex_command, add_to_history=True)
        self.assertEqual(result, "SUCCESS: Complex command executed")

    def test_function_definition_format(self):
        """Test that the tool provides a proper function definition for AI integration."""
        function_def = self.tool.to_function_definition()
        
        # Check basic structure
        self.assertIn("name", function_def)
        self.assertIn("description", function_def)
        self.assertIn("parameters", function_def)
        
        # Check specific values
        self.assertEqual(function_def["name"], "linux_command")
        self.assertIn("properties", function_def["parameters"])
        self.assertIn("command", function_def["parameters"]["properties"])

    def test_is_command_in_warn_list_method(self):
        """Test the internal _is_command_in_warn_list method."""
        # Test empty warn list
        os.environ["WARN_LIST"] = ""
        self.assertFalse(self.tool._is_command_in_warn_list("any command"))
        
        # Test with warn list
        os.environ["WARN_LIST"] = "rm,sudo,dd"
        self.assertTrue(self.tool._is_command_in_warn_list("rm file.txt"))
        self.assertTrue(self.tool._is_command_in_warn_list("sudo ls"))
        self.assertFalse(self.tool._is_command_in_warn_list("ls -la"))
        
        # Test 'all' keyword
        os.environ["WARN_LIST"] = "all"
        self.assertTrue(self.tool._is_command_in_warn_list("any command"))
        self.assertTrue(self.tool._is_command_in_warn_list("ls -la"))


if __name__ == '__main__':
    unittest.main()