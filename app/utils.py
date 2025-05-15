"""
Utility functions for Jibberish shell that don't fit elsewhere.
"""
import os
import sys
import io
from contextlib import contextmanager

def is_standalone_mode():
    """Check if Jibberish is running in standalone mode."""
    return os.environ.get('JIBBERISH_STANDALONE_MODE') == '1'

@contextmanager
def silence_stdout():
    """Context manager to silence stdout if in standalone mode."""
    if is_standalone_mode():
        original_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            yield
        finally:
            sys.stdout = original_stdout
    else:
        yield

def suppress_in_standalone(func):
    """Decorator to suppress console output if in standalone mode."""
    def wrapper(*args, **kwargs):
        if is_standalone_mode():
            original_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                return func(*args, **kwargs)
            finally:
                sys.stdout = original_stdout
        else:
            return func(*args, **kwargs)
    return wrapper
