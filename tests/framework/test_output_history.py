"""
Tests for the output_history module.

This module tests the command output recall feature that allows users
to reference previous command outputs using $_ or @n syntax.
"""

import unittest
import sys
import os

# Add the parent directory to sys.path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.output_history import (
    store_output,
    get_output,
    get_last_output,
    get_last_command,
    get_output_context_for_ai,
    parse_output_reference,
    has_output_reference,
    clear_history,
    get_history_size,
    list_available_outputs
)


class TestOutputHistory(unittest.TestCase):
    """Test cases for output history storage and retrieval."""
    
    def setUp(self):
        """Clear history before each test."""
        clear_history()
    
    def tearDown(self):
        """Clear history after each test."""
        clear_history()
    
    def test_store_and_retrieve_output(self):
        """Test basic store and retrieve functionality."""
        store_output("ls -la", "file1.txt\nfile2.txt\nfile3.txt", 0)
        
        self.assertEqual(get_history_size(), 1)
        self.assertEqual(get_last_output(), "file1.txt\nfile2.txt\nfile3.txt")
        self.assertEqual(get_last_command(), "ls -la")
    
    def test_multiple_outputs(self):
        """Test storing multiple outputs and retrieving by index."""
        store_output("ls", "file1.txt", 0)
        store_output("pwd", "/home/user", 0)
        store_output("whoami", "testuser", 0)
        
        self.assertEqual(get_history_size(), 3)
        
        # @0 is most recent
        self.assertEqual(get_output(0)["output"], "testuser")
        self.assertEqual(get_output(0)["command"], "whoami")
        
        # @1 is second most recent
        self.assertEqual(get_output(1)["output"], "/home/user")
        self.assertEqual(get_output(1)["command"], "pwd")
        
        # @2 is third most recent
        self.assertEqual(get_output(2)["output"], "file1.txt")
    
    def test_empty_output_not_stored(self):
        """Test that empty outputs are not stored."""
        store_output("echo", "", 0)
        store_output("echo", "   ", 0)
        
        self.assertEqual(get_history_size(), 0)
    
    def test_get_output_invalid_index(self):
        """Test getting output with invalid index returns None."""
        store_output("ls", "file.txt", 0)
        
        self.assertIsNone(get_output(5))
        self.assertIsNone(get_output(-1))
    
    def test_has_output_reference(self):
        """Test detection of output references in text."""
        self.assertTrue(has_output_reference("compress $_ into archive"))
        self.assertTrue(has_output_reference("use @0 for the command"))
        self.assertTrue(has_output_reference("combine @1 and @2"))
        self.assertFalse(has_output_reference("just a normal command"))
        self.assertFalse(has_output_reference("email@example.com"))  # @ in email shouldn't trigger
    
    def test_parse_output_reference_underscore(self):
        """Test parsing $_ reference."""
        store_output("ls *.log", "error.log\naccess.log", 0)
        
        has_ref, expanded = parse_output_reference("compress $_ into archive")
        
        self.assertTrue(has_ref)
        self.assertIn("error.log", expanded)
        self.assertIn("access.log", expanded)
    
    def test_parse_output_reference_at_syntax(self):
        """Test parsing @n references."""
        store_output("ls", "file1.txt", 0)
        store_output("pwd", "/home/user", 0)
        
        has_ref, expanded = parse_output_reference("cd to @1 directory")
        
        self.assertTrue(has_ref)
        self.assertIn("file1.txt", expanded)
    
    def test_parse_output_reference_no_reference(self):
        """Test parsing text without references."""
        has_ref, expanded = parse_output_reference("just a normal command")
        
        self.assertFalse(has_ref)
        self.assertEqual(expanded, "just a normal command")
    
    def test_get_output_context_for_ai(self):
        """Test generating AI context from output history."""
        store_output("ls *.py", "main.py\nutils.py", 0)
        store_output("cat main.py", "print('hello')", 0)
        
        context = get_output_context_for_ai(max_entries=2)
        
        self.assertIsNotNone(context)
        self.assertIn("@0", context)
        self.assertIn("@1", context)
        self.assertIn("cat main.py", context)
        self.assertIn("ls *.py", context)
    
    def test_get_output_context_empty_history(self):
        """Test AI context with empty history returns None."""
        context = get_output_context_for_ai()
        self.assertIsNone(context)
    
    def test_list_available_outputs(self):
        """Test listing available outputs."""
        store_output("ls", "file.txt", 0)
        store_output("pwd", "/home", 0)
        
        outputs = list_available_outputs()
        
        self.assertEqual(len(outputs), 2)
        self.assertEqual(outputs[0]["index"], 0)
        self.assertIn("$_", outputs[0]["reference"])
        self.assertEqual(outputs[1]["index"], 1)
    
    def test_output_truncation(self):
        """Test that very long outputs are truncated."""
        long_output = "x" * 60000  # Longer than the 50KB limit
        store_output("cat bigfile", long_output, 0)
        
        stored = get_last_output()
        self.assertLess(len(stored), 55000)
        self.assertIn("[output truncated]", stored)
    
    def test_history_limit(self):
        """Test that history respects the maximum limit."""
        # Store more than MAX_OUTPUT_HISTORY entries
        for i in range(15):
            store_output(f"cmd{i}", f"output{i}", 0)
        
        # Should only keep MAX_OUTPUT_HISTORY (10) entries
        self.assertEqual(get_history_size(), 10)
        
        # Most recent should be cmd14
        self.assertEqual(get_last_command(), "cmd14")


class TestOutputHistoryIntegration(unittest.TestCase):
    """Integration tests for output history with other components."""
    
    def setUp(self):
        clear_history()
    
    def tearDown(self):
        clear_history()
    
    def test_typical_workflow(self):
        """Test a typical user workflow using output references."""
        # User runs a command
        store_output("find . -name '*.log'", "/var/log/error.log\n/var/log/access.log", 0)
        
        # User wants to work with "that output"
        context = get_output_context_for_ai()
        self.assertIn("/var/log/error.log", context)
        
        # User references specific output
        has_ref, expanded = parse_output_reference("compress @0 into archive.tar.gz")
        self.assertTrue(has_ref)
        self.assertIn("/var/log/error.log", expanded)


if __name__ == '__main__':
    unittest.main()
