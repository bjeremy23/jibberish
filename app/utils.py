"""
Utility functions for Jibberish shell that don't fit elsewhere.

This module contains functions that control Jibberish behavior:
- is_debug_enabled() - Controls output verbosity based on JIBBERISH_DEBUG environment variable
"""
import os
import sys
import io
from contextlib import contextmanager

def is_debug_enabled():
    """
    Check if debug output is enabled via JIBBERISH_DEBUG environment variable.
    
    This controls whether the application shows verbose output like environment
    variable loading and plugin registration messages.
    
    Users can set JIBBERISH_DEBUG=true in their .jbrsh file to see all messages,
    or leave it unset/false for clean output.
    """
    debug_value = os.environ.get('JIBBERISH_DEBUG', 'false').lower()
    return debug_value in ['true', 'yes', 'y', '1']

@contextmanager
def silence_stdout():
    """
    Context manager to silence stdout if debug mode is not enabled.
    
    This function respects the JIBBERISH_DEBUG environment variable.
    If JIBBERISH_DEBUG=true, output will not be silenced, regardless of standalone mode.
    """
    if not is_debug_enabled():
        original_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            yield
        finally:
            sys.stdout = original_stdout
    else:
        yield
