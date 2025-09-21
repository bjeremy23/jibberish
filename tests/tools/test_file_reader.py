#!/usr/bin/env python
"""
Tests for the FileReaderTool specifically.
"""
import os
import sys
import unittest
import tempfile

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the file reader tool
from app.tools.file_reader import FileReaderTool


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
        
        # Create a large test file for size testing
        self.large_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        # Write content that would exceed 1MB threshold (simulate large file)
        large_content = "Large file content line\n" * 1000
        self.large_file.write(large_content)
        self.large_file.close()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Clean up temporary files
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        if os.path.exists(self.large_file.name):
            os.unlink(self.large_file.name)
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
        self.assertIn("max_lines", params["properties"])
        self.assertIn("start_line", params["properties"])
        self.assertIn("filepath", params["required"])
    
    def test_read_file_success(self):
        """Test successfully reading a file."""
        result = self.tool.execute(filepath=self.temp_file.name)
        
        # Check that the result contains the file contents
        self.assertIn("Line 1", result)
        self.assertIn("Line 2", result)
        self.assertIn("Line 5", result)
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
        self.assertNotIn("Line 5", result)
        self.assertIn("Lines 3-4 of 5", result)
    
    def test_read_file_start_line_only(self):
        """Test reading a file with only start_line parameter (no max_lines)."""
        result = self.tool.execute(filepath=self.temp_file.name, start_line=3)
        
        # Check that we started from line 3 and read to the end
        self.assertNotIn("Line 1", result)
        self.assertNotIn("Line 2", result)
        self.assertIn("Line 3", result)
        self.assertIn("Line 4", result)
        self.assertIn("Line 5", result)
        self.assertIn("Lines 3-5 of 5", result)
    
    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        result = self.tool.execute(filepath="/nonexistent/file.txt")
        
        self.assertIn("ERROR:", result)
        self.assertIn("not found", result)
    
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
    
    def test_tilde_expansion(self):
        """Test that filepath supports tilde expansion."""
        # Create a file in home directory for testing
        home_dir = os.path.expanduser("~")
        home_test_file = os.path.join(home_dir, "test_jibberish_file.tmp")
        
        try:
            with open(home_test_file, 'w') as f:
                f.write("Test content for tilde expansion\n")
            
            # Test with tilde path
            tilde_path = "~/test_jibberish_file.tmp"
            result = self.tool.execute(filepath=tilde_path)
            
            self.assertIn("Test content for tilde expansion", result)
            
        finally:
            # Clean up
            if os.path.exists(home_test_file):
                os.unlink(home_test_file)
    
    def test_empty_file(self):
        """Test reading an empty file."""
        empty_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        empty_file.close()  # Creates an empty file
        
        try:
            result = self.tool.execute(filepath=empty_file.name)
            
            # Empty files should result in an error since start_line 1 is beyond length
            self.assertIn("ERROR:", result)
            self.assertIn("beyond the file length", result)
            
        finally:
            os.unlink(empty_file.name)
    
    def test_file_permission_error(self):
        """Test handling of permission denied errors."""
        # Create a file and remove read permissions (if possible)
        restricted_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        restricted_file.write("Content that should not be readable")
        restricted_file.close()
        
        try:
            # Remove read permission
            os.chmod(restricted_file.name, 0o000)
            
            result = self.tool.execute(filepath=restricted_file.name)
            
            self.assertIn("ERROR:", result)
            self.assertIn("permission denied", result.lower())
            
        except (OSError, PermissionError):
            # Skip this test if we can't modify permissions (some systems)
            self.skipTest("Cannot modify file permissions on this system")
        finally:
            # Restore permissions and clean up
            try:
                os.chmod(restricted_file.name, 0o644)
                os.unlink(restricted_file.name)
            except (OSError, PermissionError):
                pass
    
    def test_function_definition_format(self):
        """Test that the tool generates a proper function definition."""
        definition = self.tool.to_function_definition()
        
        self.assertEqual(definition["name"], "read_file")
        self.assertIn("description", definition)
        self.assertIn("parameters", definition)
        self.assertEqual(definition["parameters"]["type"], "object")
        
        # Check that all expected parameters are present
        properties = definition["parameters"]["properties"]
        self.assertIn("filepath", properties)
        self.assertIn("max_lines", properties)
        self.assertIn("start_line", properties)
        
        # Check parameter descriptions
        self.assertIn("description", properties["filepath"])
        self.assertIn("description", properties["max_lines"])
        self.assertIn("description", properties["start_line"])
    
    def test_binary_file_handling(self):
        """Test handling of binary files."""
        # Create a simple binary file
        binary_file = tempfile.NamedTemporaryFile(mode='wb', delete=False)
        binary_file.write(b'\x00\x01\x02\x03\xFF\xFE\xFD')
        binary_file.close()
        
        try:
            result = self.tool.execute(filepath=binary_file.name)
            
            # The tool actually reads binary files with replacement characters
            # It should succeed and include the file metadata
            self.assertIn("=== File:", result)
            self.assertNotIn("ERROR:", result)
            
        finally:
            os.unlink(binary_file.name)
    
    def test_zero_max_lines(self):
        """Test behavior with max_lines=0."""
        result = self.tool.execute(filepath=self.temp_file.name, max_lines=0)
        
        # Should return metadata but no content
        self.assertIn("=== File:", result)
        self.assertIn("Lines 1-0 of 5", result)
        # Should not contain any of the actual file content
        self.assertNotIn("Line 1", result)


if __name__ == '__main__':
    # Run the tests with verbose output
    unittest.main(verbosity=2)