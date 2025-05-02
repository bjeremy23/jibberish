"""
Tests for the context_manager module.
"""
import sys
import os
import unittest

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from context_manager import add_specialized_contexts, determine_temperature

class TestContextManager(unittest.TestCase):
    """Test context manager functionality"""
    
    def test_add_specialized_contexts(self):
        """Test that specialized contexts are correctly added based on keywords"""
        base_context = [{"role": "system", "content": "Base context"}]
        
        # Test SSH context
        ssh_command = "connect to the remote server using ssh"
        ssh_context = add_specialized_contexts(ssh_command, base_context.copy())
        self.assertEqual(len(ssh_context), 2)
        self.assertIn("ssh", ssh_context[1]["content"].lower())
        
        # Test Git context
        git_command = "How do I commit my changes in git?"
        git_context = add_specialized_contexts(git_command, base_context.copy())
        self.assertEqual(len(git_context), 2)
        self.assertIn("git", git_context[1]["content"].lower())
        
        # Test multiple contexts
        multi_command = "I need to git push to the remote server using ssh"
        multi_context = add_specialized_contexts(multi_command, base_context.copy())
        self.assertEqual(len(multi_context), 3)  # Base + SSH + Git
        
        # Test no matching context
        no_match_command = "list all files in the current directory"
        no_match_context = add_specialized_contexts(no_match_command, base_context.copy())
        self.assertEqual(len(no_match_context), 1)  # Just base context
    
    def test_determine_temperature(self):
        """Test that temperature is correctly determined based on command type"""
        # Technical commands should have lower temperature
        self.assertAlmostEqual(determine_temperature("git merge my-branch"), 0.3)
        self.assertAlmostEqual(determine_temperature("kubectl get pods"), 0.3)
        self.assertAlmostEqual(determine_temperature("ssh user@host"), 0.3)
        
        # Creative tasks should have higher temperature
        self.assertAlmostEqual(determine_temperature("create a bash script to process logs"), 0.7)
        self.assertAlmostEqual(determine_temperature("generate a config file"), 0.7)
        
        # Default for other commands
        self.assertAlmostEqual(determine_temperature("list files"), 0.5)

if __name__ == "__main__":
    unittest.main()
