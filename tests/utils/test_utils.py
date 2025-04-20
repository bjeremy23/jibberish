"""
Common test utilities for Jibberish shell tests.
"""
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def create_mock_environment():
    """Creates a mock environment for testing."""
    # Create a temporary directory for test files
    test_dir = tempfile.mkdtemp()
    
    # Create a mock history file
    history_file = os.path.join(test_dir, '.cli_history')
    with open(history_file, 'w') as f:
        f.write("test command 1\ntest command 2\n")
    
    return {
        'test_dir': test_dir,
        'history_file': history_file
    }

def cleanup_mock_environment(env):
    """Cleans up the mock environment after testing."""
    import shutil
    if os.path.exists(env['test_dir']):
        shutil.rmtree(env['test_dir'])

class CaptureOutput:
    """Context manager to capture stdout and stderr."""
    def __init__(self):
        self.stdout = None
        self.stderr = None
        self._stdout = None
        self._stderr = None

    def __enter__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = self.stdout = tempfile.NamedTemporaryFile(mode='w+t')
        sys.stderr = self.stderr = tempfile.NamedTemporaryFile(mode='w+t')
        return self

    def __exit__(self, *args):
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        self.stdout.flush()
        self.stderr.flush()
        self.stdout.seek(0)
        self.stderr.seek(0)
        self.stdout_content = self.stdout.read()
        self.stderr_content = self.stderr.read()
        self.stdout.close()
        self.stderr.close()
        return False  # Don't suppress exceptions

def mock_click_echo(message, nl=True, **kwargs):
    """Mocks the click.echo function to capture output."""
    if nl:
        print(message)
    else:
        print(message, end='')

def mock_os_system(command):
    """Mocks the os.system function to avoid executing commands during tests."""
    return 0  # Return success code
