#!/usr/bin/env python
"""
Unittest-based test script for testing the jibberish tool system.
"""
import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the tool system components
from app.tools import ToolRegistry, FileReaderTool
from app.tools.base import Tool, ToolCallParser
from tests.utils.test_utils import CaptureOutput


class TestToolRegistry(unittest.TestCase):
    """Tests for the ToolRegistry class."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Store original tools and clear registry for clean testing
        self.original_tools = ToolRegistry._tools.copy()
        ToolRegistry._tools.clear()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Restore original tools
        ToolRegistry._tools.clear()
        ToolRegistry._tools.update(self.original_tools)
    
    def test_tool_registration(self):
        """Test that tools can be registered and retrieved."""
        # Create a mock tool
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"
        
        # Register the tool
        ToolRegistry.register(mock_tool)
        
        # Check that it was registered
        registered_tools = ToolRegistry.get_all_tools()
        self.assertIn("test_tool", registered_tools)
        self.assertEqual(registered_tools["test_tool"], mock_tool)
        
        # Check that we can retrieve it
        retrieved_tool = ToolRegistry.get_tool("test_tool")
        self.assertEqual(retrieved_tool, mock_tool)
    
    def test_get_nonexistent_tool(self):
        """Test retrieving a tool that doesn't exist."""
        result = ToolRegistry.get_tool("nonexistent_tool")
        self.assertIsNone(result)
    
    def test_function_definitions(self):
        """Test generating OpenAI function definitions."""
        # Create a mock tool with function definition
        mock_tool = MagicMock()
        mock_tool.to_function_definition.return_value = {
            "name": "test_tool",
            "description": "Test tool",
            "parameters": {"type": "object"}
        }
        
        # Register the tool
        ToolRegistry.register(mock_tool)
        
        # Get function definitions
        definitions = ToolRegistry.get_function_definitions()
        
        # Check that the definition is correct
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["name"], "test_tool")
        mock_tool.to_function_definition.assert_called_once()


class TestFileReaderTool(unittest.TestCase):
    """Tests for the FileReaderTool."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        self.tool = FileReaderTool()
        
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_file.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
        self.temp_file.close()
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Clean up temporary files
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_tool_properties(self):
        """Test that the tool has the correct properties."""
        self.assertEqual(self.tool.name, "read_file")
        self.assertIn("Read the contents of a file", self.tool.description)
        
        # Check parameters structure
        params = self.tool.parameters
        self.assertEqual(params["type"], "object")
        self.assertIn("filepath", params["properties"])
        self.assertIn("filepath", params["required"])
    
    def test_read_file_success(self):
        """Test successfully reading a file."""
        result = self.tool.execute(filepath=self.temp_file.name)
        
        # Check that the result contains the file contents
        self.assertIn("Line 1", result)
        self.assertIn("Line 2", result)
        self.assertIn("=== File:", result)
        self.assertIn("5 total", result)
    
    def test_read_file_with_max_lines(self):
        """Test reading a file with max_lines parameter."""
        result = self.tool.execute(filepath=self.temp_file.name, max_lines=2)
        
        # Check that only 2 lines were read
        self.assertIn("Line 1", result)
        self.assertIn("Line 2", result)
        self.assertNotIn("Line 3", result)
        self.assertIn("Lines 1-2 of 5", result)
    
    def test_read_file_with_start_line(self):
        """Test reading a file with start_line parameter."""
        result = self.tool.execute(filepath=self.temp_file.name, start_line=3, max_lines=2)
        
        # Check that we started from line 3
        self.assertNotIn("Line 1", result)
        self.assertNotIn("Line 2", result)
        self.assertIn("Line 3", result)
        self.assertIn("Line 4", result)
        self.assertIn("Lines 3-4 of 5", result)
    
    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        result = self.tool.execute(filepath="/nonexistent/file.txt")
        
        self.assertIn("ERROR:", result)
        self.assertIn("does not exist", result)
    
    def test_read_directory_as_file(self):
        """Test trying to read a directory as a file."""
        result = self.tool.execute(filepath=self.temp_dir)
        
        self.assertIn("ERROR:", result)
        self.assertIn("is not a file", result)
    
    def test_start_line_beyond_file_length(self):
        """Test start_line parameter beyond file length."""
        result = self.tool.execute(filepath=self.temp_file.name, start_line=10)
        
        self.assertIn("ERROR:", result)
        self.assertIn("beyond the file length", result)
    
    def test_function_definition_format(self):
        """Test that the tool generates a proper function definition."""
        definition = self.tool.to_function_definition()
        
        self.assertEqual(definition["name"], "read_file")
        self.assertIn("description", definition)
        self.assertIn("parameters", definition)
        self.assertEqual(definition["parameters"]["type"], "object")


class TestToolCallParser(unittest.TestCase):
    """Tests for the ToolCallParser."""
    
    def test_extract_tool_calls_pattern1(self):
        """Test extracting tool calls with TOOL_CALL pattern."""
        response = "I need to read that file. TOOL_CALL: read_file(filepath='/etc/passwd')"
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["name"], "read_file")
        self.assertEqual(tool_calls[0]["arguments"]["filepath"], "/etc/passwd")
    
    def test_extract_tool_calls_pattern2(self):
        """Test extracting tool calls with USE_TOOL pattern."""
        response = 'Let me check: USE_TOOL: read_file {"filepath": "/home/user/test.py", "max_lines": 20}'
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["name"], "read_file")
        self.assertEqual(tool_calls[0]["arguments"]["filepath"], "/home/user/test.py")
        self.assertEqual(tool_calls[0]["arguments"]["max_lines"], 20)
    
    def test_extract_tool_calls_pattern3(self):
        """Test extracting tool calls with [TOOL] pattern."""
        response = "[TOOL] read_file: filepath=/var/log/system.log"
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["name"], "read_file")
        self.assertEqual(tool_calls[0]["arguments"]["filepath"], "/var/log/system.log")
    
    def test_extract_multiple_tool_calls(self):
        """Test extracting multiple tool calls from one response."""
        response = """
        First, I'll read the config: TOOL_CALL: read_file(filepath='config.py')
        Then check the log: [TOOL] read_file: filepath=/var/log/app.log
        """
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        self.assertEqual(len(tool_calls), 2)
        self.assertEqual(tool_calls[0]["name"], "read_file")
        self.assertEqual(tool_calls[1]["name"], "read_file")
    
    def test_extract_no_tool_calls(self):
        """Test response with no tool calls."""
        response = "This is just a regular response with no tool requests."
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        self.assertEqual(len(tool_calls), 0)
    
    def test_should_use_tools_positive(self):
        """Test should_use_tools with responses that should use tools."""
        test_cases = [
            "TOOL_CALL: read_file(filepath='test.py')",
            "I need to read the file to understand",
            "Let me examine the file contents",
            "[TOOL] read_file: filepath=test.txt"
        ]
        
        for response in test_cases:
            with self.subTest(response=response):
                self.assertTrue(ToolCallParser.should_use_tools(response))
    
    def test_should_use_tools_negative(self):
        """Test should_use_tools with responses that shouldn't use tools."""
        response = "This is a regular response without any tool indicators."
        
        self.assertFalse(ToolCallParser.should_use_tools(response))


class TestToolIntegration(unittest.TestCase):
    """Integration tests for the complete tool system."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Ensure FileReaderTool is registered
        if ToolRegistry.get_tool("read_file") is None:
            ToolRegistry.register(FileReaderTool())
        
        # Create a test file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_file.write("#!/usr/bin/env python3\nprint('Hello, World!')\n")
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_end_to_end_tool_execution(self):
        """Test complete workflow: parse tool call and execute it."""
        # Simulate AI response with tool call
        ai_response = f"TOOL_CALL: read_file(filepath='{self.temp_file.name}')"
        
        # Parse the tool calls
        tool_calls = ToolCallParser.extract_tool_calls(ai_response)
        
        self.assertEqual(len(tool_calls), 1)
        
        # Execute the tool
        tool_call = tool_calls[0]
        tool = ToolRegistry.get_tool(tool_call["name"])
        
        self.assertIsNotNone(tool)
        
        result = tool.execute(**tool_call["arguments"])
        
        # Verify the execution result
        self.assertIn("#!/usr/bin/env python3", result)
        self.assertIn("Hello, World!", result)
        self.assertIn("=== File:", result)


if __name__ == '__main__':
    # Run the tests with verbose output
    unittest.main(verbosity=2)