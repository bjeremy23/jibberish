#!/usr/bin/env python3

import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.utils import generate_tool_context_message


class TestToolContextMessage(unittest.TestCase):
    """Tests for the generate_tool_context_message function."""
    
    def test_tool_context_message_generation(self):
        """Test that tool context message is generated correctly."""
        context_msg = generate_tool_context_message()
        
        self.assertIsNotNone(context_msg)
        self.assertEqual(context_msg['role'], 'system')
        self.assertIn('content', context_msg)
        
        content = context_msg['content']
        
        # Check that it contains tool descriptions
        self.assertIn('read_file', content)
        self.assertIn('write_file', content)
        
        # Check that it contains the improved formatting instructions
        self.assertIn('TOOL_CALL:', content)
        self.assertIn('USE_TOOL:', content)
        self.assertIn('[TOOL]', content)
        self.assertIn('```tool_name', content)  # Check for markdown code block format
        
        # Check that examples are provided
        self.assertIn('Examples:', content)
        
        # Check that tool chaining is explained
        self.assertIn('TOOL CHAINING', content)
        self.assertIn('multiple tools or actions', content)
        self.assertIn('actually make the tool calls', content)
    
    def test_tool_context_includes_parameter_info(self):
        """Test that tool context includes parameter information."""
        context_msg = generate_tool_context_message()
        content = context_msg['content']
        
        # Should include parameter details
        self.assertIn('filepath', content)
        self.assertIn('(required)', content)
        self.assertIn('(optional)', content)
        
        # Should include parameter types
        self.assertIn('(string)', content)
        self.assertIn('(integer)', content)


if __name__ == '__main__':
    unittest.main(verbosity=2)