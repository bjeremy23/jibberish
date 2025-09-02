#!/usr/bin/env python
"""
Tests for the FileWriterTool specifically.
"""
import os
import sys
import unittest
import tempfile
import shutil

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the file writer tool
from app.tools.file_writer import FileWriterTool


class TestFileWriterTool(unittest.TestCase):
    """Tests for the FileWriterTool."""
    
    def setUp(self):
        """Set up the test environment before each test method."""
        self.tool = FileWriterTool()
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test file path within the temp directory
        self.test_file = os.path.join(self.temp_dir, "test_output.txt")
        
        # Create an existing file for append/overwrite tests
        self.existing_file = os.path.join(self.temp_dir, "existing_file.txt")
        with open(self.existing_file, 'w') as f:
            f.write("Original content\nSecond line")
    
    def tearDown(self):
        """Clean up after each test method."""
        # Clean up temporary directory and all contents
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_tool_properties(self):
        """Test that the tool has the correct properties."""
        self.assertEqual(self.tool.name, "write_file")
        self.assertIn("Write content to a file", self.tool.description)
        
        # Check parameters structure
        params = self.tool.parameters
        self.assertEqual(params["type"], "object")
        self.assertIn("filepath", params["properties"])
        self.assertIn("content", params["properties"])
        self.assertIn("append", params["properties"])
        self.assertIn("encoding", params["properties"])
        
        # Check required parameters
        self.assertEqual(set(params["required"]), {"filepath", "content"})
    
    def test_write_new_file_success(self):
        """Test successfully writing to a new file."""
        content = "Hello, World!\nThis is a test file."
        result = self.tool.execute(filepath=self.test_file, content=content)
        
        # Check that the result indicates success
        self.assertIn("✅", result)
        self.assertIn("File created", result)
        self.assertIn(self.test_file, result)
        self.assertIn("34 bytes", result)  # Length of content
        
        # Verify the file was actually created with correct content
        self.assertTrue(os.path.exists(self.test_file))
        with open(self.test_file, 'r') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)
    
    def test_overwrite_existing_file(self):
        """Test overwriting an existing file."""
        new_content = "This is new content that replaces the old."
        result = self.tool.execute(filepath=self.existing_file, content=new_content)
        
        # Check that the result indicates overwrite
        self.assertIn("✅", result)
        self.assertIn("File overwritten", result)
        self.assertIn(self.existing_file, result)
        
        # Verify the file was overwritten
        with open(self.existing_file, 'r') as f:
            written_content = f.read()
        self.assertEqual(written_content, new_content)
    
    def test_append_to_existing_file(self):
        """Test appending content to an existing file."""
        append_content = "\nThis is appended content."
        result = self.tool.execute(filepath=self.existing_file, content=append_content, append=True)
        
        # Check that the result indicates append
        self.assertIn("✅", result)
        self.assertIn("Content appended", result)
        self.assertIn("Original size:", result)
        self.assertIn("Added:", result)
        self.assertIn("New size:", result)
        
        # Verify the content was appended
        with open(self.existing_file, 'r') as f:
            final_content = f.read()
        expected_content = "Original content\nSecond line" + append_content
        self.assertEqual(final_content, expected_content)
    
    def test_create_directories_automatically(self):
        """Test that parent directories are created automatically."""
        nested_path = os.path.join(self.temp_dir, "subdir", "nested", "test_file.txt")
        content = "Testing directory creation"
        
        # Ensure the nested directories don't exist
        self.assertFalse(os.path.exists(os.path.dirname(nested_path)))
        
        result = self.tool.execute(filepath=nested_path, content=content)
        
        # Check success
        self.assertIn("✅", result)
        self.assertIn("File created", result)
        
        # Verify the file was created and directories exist
        self.assertTrue(os.path.exists(nested_path))
        with open(nested_path, 'r') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)
    
    def test_tilde_expansion(self):
        """Test that filepath supports tilde expansion."""
        # Use a file in the temp directory but reference it with tilde
        home_dir = os.path.expanduser("~")
        if not self.temp_dir.startswith(home_dir):
            # Skip this test if temp dir is not in home directory
            self.skipTest("Temp directory not in home directory for tilde test")
        
        # Create a relative path from home
        rel_path = os.path.relpath(self.test_file, home_dir)
        tilde_path = f"~/{rel_path}"
        
        content = "Testing tilde expansion"
        result = self.tool.execute(filepath=tilde_path, content=content)
        
        self.assertIn("✅", result)
        self.assertTrue(os.path.exists(self.test_file))
        with open(self.test_file, 'r') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)
    
    def test_empty_content(self):
        """Test writing empty content to create empty file."""
        result = self.tool.execute(filepath=self.test_file, content="")
        
        # Check success
        self.assertIn("✅", result)
        self.assertIn("File created", result)
        self.assertIn("0 bytes", result)
        
        # Verify empty file was created
        self.assertTrue(os.path.exists(self.test_file))
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "")
    
    def test_custom_encoding(self):
        """Test writing with custom encoding."""
        content = "Testing custom encoding: café, naïve"
        result = self.tool.execute(filepath=self.test_file, content=content, encoding="utf-8")
        
        self.assertIn("✅", result)
        self.assertIn("Encoding: utf-8", result)
        
        # Verify file was written with correct encoding
        with open(self.test_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)
    
    def test_missing_filepath_parameter(self):
        """Test error handling when filepath parameter is missing."""
        with self.assertRaises(ValueError) as context:
            self.tool.execute(content="test content")
        
        self.assertIn("filepath parameter is required", str(context.exception))
    
    def test_permission_denied_error(self):
        """Test handling of permission denied errors."""
        # Try to write to a location that should not be writable
        readonly_path = "/root/test_write_permission.txt"
        
        try:
            with self.assertRaises(Exception) as context:
                self.tool.execute(filepath=readonly_path, content="test content")
            
            exception_message = str(context.exception)
            self.assertIn("Permission denied", exception_message)
            
        except PermissionError:
            # Expected if we can't even attempt to write there
            pass
    
    def test_invalid_encoding(self):
        """Test handling of invalid encoding."""
        # Use content with characters that can't be encoded in ASCII
        content = "Unicode content: café, 中文, emoji 🎉"
        
        with self.assertRaises(Exception) as context:
            self.tool.execute(filepath=self.test_file, content=content, encoding="ascii")
        
        exception_message = str(context.exception)
        self.assertIn("Encoding error", exception_message)
    
    def test_line_counting(self):
        """Test that line counting works correctly."""
        content = "Line 1\nLine 2\nLine 3\n"
        result = self.tool.execute(filepath=self.test_file, content=content)
        
        # Should count 4 lines (3 lines + 1 for the final newline)
        self.assertIn("Lines: 4", result)
    
    def test_function_definition_format(self):
        """Test that the tool generates a proper function definition."""
        definition = self.tool.to_function_definition()
        
        self.assertEqual(definition["name"], "write_file")
        self.assertIn("description", definition)
        self.assertIn("parameters", definition)
        self.assertEqual(definition["parameters"]["type"], "object")
        
        # Check that all expected parameters are present
        properties = definition["parameters"]["properties"]
        self.assertIn("filepath", properties)
        self.assertIn("content", properties)
        self.assertIn("append", properties)
        self.assertIn("encoding", properties)
        
        # Check parameter descriptions and types
        self.assertEqual(properties["filepath"]["type"], "string")
        self.assertEqual(properties["content"]["type"], "string")
        self.assertEqual(properties["append"]["type"], "boolean")
        self.assertEqual(properties["encoding"]["type"], "string")
        
        # Check required parameters
        self.assertEqual(set(definition["parameters"]["required"]), {"filepath", "content"})
    
    def test_append_to_nonexistent_file(self):
        """Test appending to a file that doesn't exist (should create it)."""
        nonexistent_file = os.path.join(self.temp_dir, "new_file.txt")
        content = "This should create a new file"
        
        result = self.tool.execute(filepath=nonexistent_file, content=content, append=True)
        
        # Should indicate file was created (not appended since it didn't exist)
        self.assertIn("✅", result)
        self.assertIn("File created", result)
        
        # Verify the file exists with correct content
        self.assertTrue(os.path.exists(nonexistent_file))
        with open(nonexistent_file, 'r') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)
    
    def test_large_content(self):
        """Test writing large content to file."""
        # Generate large content (about 100KB)
        large_content = "This is a test line with some content.\n" * 2500
        
        result = self.tool.execute(filepath=self.test_file, content=large_content)
        
        self.assertIn("✅", result)
        self.assertIn("File created", result)
        
        # Verify large file was written correctly
        self.assertTrue(os.path.exists(self.test_file))
        with open(self.test_file, 'r') as f:
            written_content = f.read()
        self.assertEqual(written_content, large_content)
        
        # Check file size is reasonable
        file_size = os.path.getsize(self.test_file)
        self.assertGreater(file_size, 90000)  # Should be around 95KB
    
    def test_special_characters_in_path(self):
        """Test handling paths with special characters."""
        special_dir = os.path.join(self.temp_dir, "dir with spaces", "special-chars_test")
        special_file = os.path.join(special_dir, "file-with-dashes_and_underscores.txt")
        content = "Content in file with special path"
        
        result = self.tool.execute(filepath=special_file, content=content)
        
        self.assertIn("✅", result)
        self.assertIn("File created", result)
        
        # Verify the file was created with correct content
        self.assertTrue(os.path.exists(special_file))
        with open(special_file, 'r') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)


if __name__ == '__main__':
    # Run the tests with verbose output
    unittest.main(verbosity=2)