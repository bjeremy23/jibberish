#!/usr/bin/env python3
# filepath: /home/brownjer/bin/jibberish/setup.py

from setuptools import setup, find_packages
import os
import sys

# Add the current directory to sys.path to import version.py
sys.path.insert(0, os.path.abspath('.'))
from version import __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Determine correct packages based on directory structure
packages = []
if os.path.exists("jibberish"):
    # If the code has been reorganized
    packages = find_packages(include=["jibberish", "jibberish.*"])
else:
    # Original structure
    packages = find_packages(include=["plugins", "plugins.*"])

setup(
    name="jibberish",
    version=__version__,  # Use version from version.py
    author="Jeremy Brown",
    author_email="bjeremy32@yahoo.com",
    description="An AI-powered Linux Shell that generates commands from natural language",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bjeremy23/jibberish",
    packages=packages,
    py_modules=["jibberish", "api", "built_ins", "chat", "context_manager", 
                "executor", "history", "plugin_system"] if not os.path.exists("jibberish") else [],
    python_requires=">=3.6",
    install_requires=[
        "click>=8.0.0",
        "openai>=1.0.0",
        "psutil>=7.0.0",
    ],
    extras_require={
        "azure": ["azure-identity", "azure-ai-openai"],
    },
    entry_points={
        "console_scripts": [
            "jibberish=jibberish:main" if os.path.exists("jibberish") else "jibberish=jibberish:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Utilities",
    ],
)
