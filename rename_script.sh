#!/bin/bash
# filepath: /home/brownjer/bin/jibberish/rename_script.sh
# Script to help reorganize the Jibberish codebase for proper Python packaging

set -e  # Exit on any error

echo "Reorganizing files for pip package structure..."

# Create the jibberish package directory if it doesn't exist
if [ ! -d "jibberish" ]; then
    mkdir -p jibberish/plugins
    
    # Copy Python files to the new package structure
    echo "Copying Python files to the package structure..."
    cp *.py jibberish/
    cp plugins/*.py jibberish/plugins/
    
    # Create __init__.py files
    echo "Creating __init__.py files..."
    if [ ! -f "jibberish/__init__.py" ]; then
        echo '"""
Jibberish - AI-powered Linux Shell
"""

# Make the main function available at the package level
from jibberish.jibberish import main

# Import version information from centralized version module
from jibberish.version import __version__, VERSION_NAME' > jibberish/__init__.py
    fi
    
    if [ ! -f "jibberish/plugins/__init__.py" ]; then
        echo '"""
This file marks the plugins directory as a Python package.
"""' > jibberish/plugins/__init__.py
    fi
    
    # Copy README and other files
    echo "Copying documentation and configuration files..."
    mkdir -p jibberish/README
    cp README/*.md jibberish/README/
    cp .jbrsh jibberish/
    cp requirements.txt jibberish/
    
    echo "File reorganization complete!"
    echo "You can now build the package with: python -m build"
    echo "Remember to update imports in the Python files if needed."
else
    echo "jibberish directory already exists. Skipping reorganization."
    echo "If you want to recreate the structure, please remove the jibberish directory first."
fi
