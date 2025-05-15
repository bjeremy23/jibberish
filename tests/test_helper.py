"""
Helper module to ensure consistent import paths for tests.
Import this in all test modules.
"""
import os
import sys
import importlib

# Add jibberish root directory to path
jibberish_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if jibberish_dir not in sys.path:
    sys.path.insert(0, jibberish_dir)

# Import modules to make available to tests
from app import chat
from app import history
from app import executor
from app import plugin_system
from app import built_ins
from app import context_manager
from app import api
from app import version

# Provide direct access as global variables
# This way tests can simply import test_helper and use test_helper.chat, etc.
