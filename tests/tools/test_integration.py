#!/usr/bin/env python
"""
Integration tests for the complete jibberish tool system.
"""
import os
import sys
import unittest
import tempfile

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the tool system components
from app.tools import ToolRegistry, FileReaderTool, FileWriterTool
from app.tools.base import ToolCallParser


class TestToolIntegration(unittest.TestCase):
    """Integration tests for the complete tool system."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        # Store original tools state
        self.original_tools = ToolRegistry._tools.copy()
        
        # Ensure FileReaderTool and FileWriterTool are registered
        if ToolRegistry.get_tool("read_file") is None:
            ToolRegistry.register(FileReaderTool())
        if ToolRegistry.get_tool("write_file") is None:
            ToolRegistry.register(FileWriterTool())
        
        # Create a test file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_file.write("#!/usr/bin/env python3\nprint('Hello, World!')\n# This is a test file\n")
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        
        # Restore original tools state
        ToolRegistry._tools.clear()
        ToolRegistry._tools.update(self.original_tools)
    
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
        self.assertIn("This is a test file", result)
        self.assertIn("=== File:", result)
    
    def test_multiple_tool_calls_execution(self):
        """Test executing multiple tool calls in sequence."""
        # Create a second test file
        temp_file2 = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_file2.write("Second test file\nwith different content\n")
        temp_file2.close()
        
        try:
            # Simulate AI response with multiple tool calls
            ai_response = f"""
            First, let me read the main file: TOOL_CALL: read_file(filepath='{self.temp_file.name}')
            Now let me check the second file: TOOL_CALL: read_file(filepath='{temp_file2.name}')
            """
            
            # Parse the tool calls
            tool_calls = ToolCallParser.extract_tool_calls(ai_response)
            
            self.assertEqual(len(tool_calls), 2)
            
            # Execute both tools
            results = []
            for tool_call in tool_calls:
                tool = ToolRegistry.get_tool(tool_call["name"])
                self.assertIsNotNone(tool)
                result = tool.execute(**tool_call["arguments"])
                results.append(result)
            
            # Verify both results
            self.assertIn("Hello, World!", results[0])
            self.assertIn("Second test file", results[1])
            
        finally:
            os.unlink(temp_file2.name)
    
    def test_tool_call_with_parameters(self):
        """Test tool calls with various parameters."""
        ai_response = f"USE_TOOL: read_file {{\"filepath\": \"{self.temp_file.name}\", \"max_lines\": 2, \"start_line\": 1}}"
        
        # Parse and execute
        tool_calls = ToolCallParser.extract_tool_calls(ai_response)
        self.assertEqual(len(tool_calls), 1)
        
        tool_call = tool_calls[0]
        tool = ToolRegistry.get_tool(tool_call["name"])
        result = tool.execute(**tool_call["arguments"])
        
        # Should only have first 2 lines
        self.assertIn("#!/usr/bin/env python3", result)
        self.assertIn("Hello, World!", result)
        self.assertNotIn("This is a test file", result)  # This is line 3
        self.assertIn("Lines 1-2 of 3", result)
    
    def test_tool_error_handling_in_integration(self):
        """Test that tool errors are properly handled in the integration flow."""
        # Simulate tool call with non-existent file
        ai_response = "TOOL_CALL: read_file(filepath='/nonexistent/file.txt')"
        
        # Parse and execute
        tool_calls = ToolCallParser.extract_tool_calls(ai_response)
        tool_call = tool_calls[0]
        tool = ToolRegistry.get_tool(tool_call["name"])
        
        result = tool.execute(**tool_call["arguments"])
        
        # Should get an error message, not an exception
        self.assertIn("ERROR:", result)
        self.assertIn("does not exist", result)
    
    def test_function_definitions_integration(self):
        """Test that function definitions work properly for AI integration."""
        definitions = ToolRegistry.get_function_definitions()
        
        # Should have at least the read_file tool
        self.assertGreaterEqual(len(definitions), 1)
        
        # Find the read_file definition
        read_file_def = None
        for definition in definitions:
            if definition["name"] == "read_file":
                read_file_def = definition
                break
        
        self.assertIsNotNone(read_file_def)
        
        # Verify the structure is suitable for OpenAI function calling
        self.assertIn("name", read_file_def)
        self.assertIn("description", read_file_def)
        self.assertIn("parameters", read_file_def)
        self.assertEqual(read_file_def["parameters"]["type"], "object")
        self.assertIn("properties", read_file_def["parameters"])
        self.assertIn("required", read_file_def["parameters"])
    
    def test_registry_persistence_across_calls(self):
        """Test that the registry maintains state across multiple calls."""
        # Register a tool
        tool = ToolRegistry.get_tool("read_file")
        self.assertIsNotNone(tool)
        
        # Make multiple calls
        for i in range(3):
            retrieved_tool = ToolRegistry.get_tool("read_file")
            self.assertIsNotNone(retrieved_tool)
            self.assertEqual(retrieved_tool.name, "read_file")
        
        # Verify we get the same instance
        tool2 = ToolRegistry.get_tool("read_file")
        self.assertIs(tool, tool2)  # Should be the exact same object
    
    def test_write_file_integration(self):
        """Test end-to-end write_file tool execution."""
        # Create a temporary file path for writing
        temp_output = tempfile.mktemp(suffix=".txt")
        
        try:
            # Simulate AI response with write_file tool call
            content = "This is test content\nwritten by the AI tool\n"
            ai_response = f'TOOL_CALL: write_file(filepath="{temp_output}", content="{content}")'
            
            # Parse the tool calls
            tool_calls = ToolCallParser.extract_tool_calls(ai_response)
            
            self.assertEqual(len(tool_calls), 1)
            self.assertEqual(tool_calls[0]["name"], "write_file")
            
            # Execute the tool
            tool_call = tool_calls[0]
            tool = ToolRegistry.get_tool(tool_call["name"])
            
            self.assertIsNotNone(tool)
            
            result = tool.execute(**tool_call["arguments"])
            
            # Verify the execution result
            self.assertIn("✅", result)
            self.assertIn("File created", result)
            self.assertIn(temp_output, result)
            
            # Verify the file was actually created with correct content
            self.assertTrue(os.path.exists(temp_output))
            with open(temp_output, 'r') as f:
                written_content = f.read()
            self.assertEqual(written_content, content)
            
        finally:
            # Clean up
            if os.path.exists(temp_output):
                os.unlink(temp_output)
    
    def test_read_write_tool_chain(self):
        """Test chaining read_file and write_file tools together."""
        temp_output = tempfile.mktemp(suffix=".txt")
        
        try:
            # Step 1: Read from the original test file
            read_response = f"TOOL_CALL: read_file(filepath='{self.temp_file.name}')"
            read_tool_calls = ToolCallParser.extract_tool_calls(read_response)
            
            read_tool = ToolRegistry.get_tool("read_file")
            read_result = read_tool.execute(**read_tool_calls[0]["arguments"])
            
            # Extract just the content (skip the metadata header)
            lines = read_result.split('\n')
            content_start = 0
            for i, line in enumerate(lines):
                if line.startswith('===') and 'total' in line:
                    content_start = i + 2  # Skip the header and blank line
                    break
            original_content = '\n'.join(lines[content_start:])
            
            # Step 2: Write that content to a new file with additional text
            modified_content = original_content + "\n# Modified by integration test"
            # Properly escape the content for JSON
            import json
            escaped_content = json.dumps(modified_content)
            write_response = f'USE_TOOL: write_file {{"filepath": "{temp_output}", "content": {escaped_content}}}'
            write_tool_calls = ToolCallParser.extract_tool_calls(write_response)
            
            write_tool = ToolRegistry.get_tool("write_file")
            write_result = write_tool.execute(**write_tool_calls[0]["arguments"])
            
            # Verify write succeeded
            self.assertIn("✅", write_result)
            self.assertIn("File created", write_result)
            
            # Verify the chained operation worked
            self.assertTrue(os.path.exists(temp_output))
            with open(temp_output, 'r') as f:
                final_content = f.read()
            
            self.assertIn("Hello, World!", final_content)
            self.assertIn("Modified by integration test", final_content)
            
        finally:
            if os.path.exists(temp_output):
                os.unlink(temp_output)
    
    def test_both_tools_in_function_definitions(self):
        """Test that both read_file and write_file appear in function definitions."""
        definitions = ToolRegistry.get_function_definitions()
        
        # Should have both tools
        tool_names = [def_["name"] for def_ in definitions]
        self.assertIn("read_file", tool_names)
        self.assertIn("write_file", tool_names)
        
        # Find both definitions
        read_def = next((d for d in definitions if d["name"] == "read_file"), None)
        write_def = next((d for d in definitions if d["name"] == "write_file"), None)
        
        self.assertIsNotNone(read_def)
        self.assertIsNotNone(write_def)
        
        # Verify both have proper structure
        for definition in [read_def, write_def]:
            self.assertIn("name", definition)
            self.assertIn("description", definition)
            self.assertIn("parameters", definition)
            self.assertEqual(definition["parameters"]["type"], "object")
            self.assertIn("properties", definition["parameters"])
            self.assertIn("required", definition["parameters"])


if __name__ == '__main__':
    # Run the tests with verbose output
    unittest.main(verbosity=2)