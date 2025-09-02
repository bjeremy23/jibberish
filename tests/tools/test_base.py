#!/usr/bin/env python
"""
Tests for the jibberish tool system base classes and registry.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the tool system components
from app.tools.base import Tool, ToolRegistry, ToolCallParser


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
    
    def test_extract_tool_calls_pattern3_no_filepath_fallback(self):
        """Test extracting tool calls with [TOOL] pattern without = sign (should not auto-assign filepath)."""
        response = "[TOOL] read_file: /var/log/system.log"
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["name"], "read_file")
        # Should have empty arguments since there's no key=value format
        self.assertEqual(tool_calls[0]["arguments"], {})
    
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
            "USE_TOOL: write_file {'filepath': 'output.txt'}",
            "[TOOL] read_file: filepath=test.txt"
        ]
        
        for response in test_cases:
            with self.subTest(response=response):
                self.assertTrue(ToolCallParser.should_use_tools(response))
    
    def test_should_use_tools_negative(self):
        """Test should_use_tools with responses that shouldn't use tools."""
        response = "This is a regular response without any tool indicators."
        
        self.assertFalse(ToolCallParser.should_use_tools(response))
    
    def test_natural_language_no_tool_detection(self):
        """Test that natural language responses without tool calls are correctly identified."""
        natural_response = """Certainly. Here is a concise summary of the FDIO patch creation process, based on the README, which you can save to /tmp/patch.readme:

---

**FDIO Patch Creation Summary**

To create a new FDIO patch, use `cna make modify-fdio-src-patch` to generate a modifiable source directory, make and commit your changes in a single commit, then run `cna make create-fdio-src-patch` to generate the patch file.

---

This summary is ready for writing to `/tmp/patch.readme`. If you want me to write this directly to the file, please enable the necessary file write permissions or confirm the action."""
        
        # Should not detect tools in natural language
        self.assertFalse(ToolCallParser.should_use_tools(natural_response))
        
        # Should not extract any tool calls
        tool_calls = ToolCallParser.extract_tool_calls(natural_response)
        self.assertEqual(len(tool_calls), 0)
    
    def test_explicit_tool_call_detection(self):
        """Test that explicit tool calls are correctly detected and extracted."""
        explicit_response = """I'll write the summary to the file for you.

TOOL_CALL: write_file(filepath="/tmp/patch.readme", content="**FDIO Patch Creation Summary**\\n\\nTo create a new FDIO patch, use `cna make modify-fdio-src-patch`...")"""
        
        # Should detect explicit tool calls
        self.assertTrue(ToolCallParser.should_use_tools(explicit_response))
        
        # Should extract the tool call correctly
        tool_calls = ToolCallParser.extract_tool_calls(explicit_response)
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["name"], "write_file")
        self.assertIn("filepath", tool_calls[0]["arguments"])
        self.assertIn("content", tool_calls[0]["arguments"])
        self.assertEqual(tool_calls[0]["arguments"]["filepath"], "/tmp/patch.readme")
    
    def test_use_tool_format_detection(self):
        """Test that USE_TOOL format is correctly detected and extracted."""
        use_tool_response = """Let me save this summary for you.

USE_TOOL: write_file {"filepath": "/tmp/patch.readme", "content": "FDIO Patch Creation Summary"}"""
        
        # Should detect USE_TOOL format
        self.assertTrue(ToolCallParser.should_use_tools(use_tool_response))
        
        # Should extract the tool call correctly
        tool_calls = ToolCallParser.extract_tool_calls(use_tool_response)
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["name"], "write_file")
        self.assertEqual(tool_calls[0]["arguments"]["filepath"], "/tmp/patch.readme")
        self.assertEqual(tool_calls[0]["arguments"]["content"], "FDIO Patch Creation Summary")
    
    def test_tool_detection_case_insensitive(self):
        """Test that tool detection works case-insensitively."""
        responses = [
            "tool_call: read_file(filepath='/test')",
            "TOOL_CALL: read_file(filepath='/test')",
            "use_tool: read_file {'filepath': '/test'}",
            "USE_TOOL: read_file {'filepath': '/test'}",
            "[tool] read_file: filepath=/test",
            "[TOOL] read_file: filepath=/test"
        ]
        
        for response in responses:
            with self.subTest(response=response):
                self.assertTrue(ToolCallParser.should_use_tools(response), 
                              f"Should detect tools in: {response}")


class MockTool(Tool):
    """Mock tool implementation for testing."""
    
    @property
    def name(self) -> str:
        return "mock_tool"
    
    @property
    def description(self) -> str:
        return "A mock tool for testing"
    
    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "test_param": {
                    "type": "string",
                    "description": "A test parameter"
                }
            },
            "required": ["test_param"]
        }
    
    def execute(self, **kwargs) -> str:
        return f"Mock tool executed with: {kwargs}"


class TestToolBaseClass(unittest.TestCase):
    """Tests for the Tool base class."""
    
    def test_tool_function_definition(self):
        """Test that Tool base class generates proper function definitions."""
        tool = MockTool()
        definition = tool.to_function_definition()
        
        self.assertEqual(definition["name"], "mock_tool")
        self.assertEqual(definition["description"], "A mock tool for testing")
        self.assertIn("parameters", definition)
        self.assertEqual(definition["parameters"]["type"], "object")
    
    def test_tool_execution(self):
        """Test that Tool base class can execute properly."""
        tool = MockTool()
        result = tool.execute(test_param="test_value")
        
        self.assertIn("test_param", result)
        self.assertIn("test_value", result)

    def test_extract_tool_calls_pattern4(self):
        """Test extracting tool calls with ```tool_name format (markdown code blocks)."""
        response = """```write_file
/tmp/test.txt
This is the content
that spans multiple lines
```"""
        
        parser = ToolCallParser()
        tool_calls = parser.extract_tool_calls(response)
        
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]['name'], 'write_file')
        self.assertEqual(tool_calls[0]['arguments']['filepath'], '/tmp/test.txt')
        self.assertIn('This is the content', tool_calls[0]['arguments']['content'])
        self.assertIn('multiple lines', tool_calls[0]['arguments']['content'])

    def test_markdown_code_block_detection(self):
        """Test that markdown code blocks with tool names are correctly detected."""
        parser = ToolCallParser()
        
        # Should detect
        self.assertTrue(parser.should_use_tools("```read_file\n/path/to/file\n```"))
        self.assertTrue(parser.should_use_tools("```write_file\n/tmp/out.txt\nContent here\n```"))
        
        # Should not detect (not tool names)
        self.assertFalse(parser.should_use_tools("```python\nprint('hello')\n```"))
        self.assertFalse(parser.should_use_tools("```bash\nls -la\n```"))


if __name__ == '__main__':
    # Run the tests with verbose output
    unittest.main(verbosity=2)