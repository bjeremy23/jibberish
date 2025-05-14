#!/usr/bin/env python3
# filepath: /home/brownjer/bin/jibberish/update_toml_version.py

"""
This script updates the version in pyproject.toml to match version.py.
Run this whenever you update the version in version.py.
"""

import sys
import os
import re
from version import __version__

def update_toml_version():
    """Update the version in pyproject.toml with the one from version.py."""
    toml_file = "pyproject.toml"
    
    # Check if pyproject.toml exists
    if not os.path.exists(toml_file):
        print(f"Error: {toml_file} not found.")
        return False
    
    # Read the content of pyproject.toml
    with open(toml_file, "r") as f:
        content = f.read()
    
    # Replace the version
    pattern = r'(version\s*=\s*)["\'](.*?)["\']'
    new_content = re.sub(pattern, f'\\1"{__version__}"', content)
    
    # Write the content back to pyproject.toml
    with open(toml_file, "w") as f:
        f.write(new_content)
    
    print(f"Updated version in {toml_file} to {__version__}")
    return True

if __name__ == "__main__":
    if update_toml_version():
        sys.exit(0)
    else:
        sys.exit(1)
